import json
import logging
import sys
from datetime import datetime, timezone

from tailored_kit.feature_context import get_current_feature_key
from tailored_kit.telemetry_otel.setup import get_current_trace_context


class StructuredJsonFormatter(logging.Formatter):
    """Formats Python log records as JSON correlated with OTel trace_id and feature_key."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = get_current_trace_context()
        feature_key = getattr(record, "feature_key", None) or get_current_feature_key()
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": self.service_name,
            "logger": record.name,
            "trace_id": trace_id,
            "span_id": span_id,
            "feature_key": feature_key,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Configures root logger to emit trace-correlated structured JSON to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter(service_name=service_name))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
