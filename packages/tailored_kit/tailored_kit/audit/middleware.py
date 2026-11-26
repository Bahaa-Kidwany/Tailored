from typing import Optional

from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from tailored_kit.feature_context import (
    get_current_feature_key,
    reset_feature_key,
    set_current_feature_key,
)
from tailored_kit.telemetry_otel.setup import get_current_trace_context


class TraceAndFeatureMiddleware(BaseHTTPMiddleware):
    """Propagates X-Feature-Key into context/spans and stamps X-Trace-Id on every HTTP response."""

    def __init__(self, app, default_feature_key: Optional[str] = None) -> None:
        super().__init__(app)
        self.default_feature_key = default_feature_key

    async def dispatch(self, request: Request, call_next) -> Response:
        feature_key = request.headers.get("X-Feature-Key") or self.default_feature_key
        token = set_current_feature_key(feature_key)
        try:
            span = trace.get_current_span()
            if span and feature_key:
                span.set_attribute("tailored.feature_key", feature_key)
            response = await call_next(request)
            trace_id, _ = get_current_trace_context()
            if "X-Trace-Id" not in response.headers:
                response.headers["X-Trace-Id"] = trace_id
            return response
        finally:
            reset_feature_key(token)
