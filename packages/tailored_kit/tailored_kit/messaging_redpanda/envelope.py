from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActorContext(BaseModel):
    user_id: Optional[str] = None
    analytics_anon_id: Optional[str] = None


class EventEnvelope(BaseModel):
    """Canonical Redpanda event envelope matching 03_api_and_event_contracts.md."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    schema_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=utc_now)
    producer_service: str
    trace_id: str = "0" * 32
    span_id: str = "0" * 16
    feature_key: Optional[str] = None
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))
    actor: ActorContext = Field(default_factory=ActorContext)
    payload: Dict[str, Any] = Field(default_factory=dict)


def inject_trace_headers(base_headers: Optional[Dict[str, str]] = None) -> List[Tuple[str, bytes]]:
    """Injects active OTel W3C traceparent and metadata into Kafka record headers."""
    carrier: Dict[str, str] = dict(base_headers or {})
    inject(carrier)
    return [(k, str(v).encode("utf-8")) for k, v in carrier.items() if v is not None]


def extract_trace_context(headers: Optional[List[Tuple[str, bytes]]]) -> Any:
    """Extracts W3C trace context from Kafka record headers."""
    carrier: Dict[str, str] = {}
    if headers:
        for k, v in headers:
            if v is not None:
                carrier[k] = v.decode("utf-8", errors="ignore")
    return extract(carrier)


def get_span_link_from_headers(headers: Optional[List[Tuple[str, bytes]]]) -> Optional[trace.Link]:
    ctx = extract_trace_context(headers)
    span_ctx = trace.get_current_span(ctx).get_span_context()
    if span_ctx and span_ctx.is_valid:
        return trace.Link(span_ctx)
    return None
