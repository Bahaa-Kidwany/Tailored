from __future__ import annotations

import logging
from typing import Optional, Tuple

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from tailored_kit.config import ServiceSettings

logger = logging.getLogger(__name__)

_ZERO_TRACE_ID = "0" * 32
_ZERO_SPAN_ID = "0" * 16
_TRACER_INITIALIZED = False


def get_current_trace_context() -> Tuple[str, str]:
    """Returns (32-hex trace_id, 16-hex span_id) from active OpenTelemetry span."""
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx and ctx.is_valid:
        return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
    return _ZERO_TRACE_ID, _ZERO_SPAN_ID


def setup_telemetry(app: Optional[FastAPI], settings: ServiceSettings) -> None:
    """Initializes OTel TracerProvider, W3C propagator, and FastAPI/HTTPX hooks."""
    global _TRACER_INITIALIZED

    set_global_textmap(TraceContextTextMapPropagator())

    if not _TRACER_INITIALIZED:
        resource = Resource.create(
            {
                "service.name": settings.service_name,
                "service.version": settings.service_version,
                "deployment.environment": settings.environment,
            }
        )
        provider = TracerProvider(resource=resource)
        if settings.otel_enabled and settings.otlp_endpoint:
            try:
                exporter = OTLPSpanExporter(
                    endpoint=settings.otlp_endpoint,
                    insecure=settings.otlp_endpoint.startswith("http://"),
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception as exc:
                logger.warning("OTLP exporter initialization failed (%s)", exc)

        trace.set_tracer_provider(provider)
        HTTPXClientInstrumentor().instrument()
        _TRACER_INITIALIZED = True

    if app is not None and not getattr(app.state, "_otel_instrumented", False):
        FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
        app.state._otel_instrumented = True
