from opentelemetry import trace

from tailored_kit.config import ServiceSettings
from tailored_kit.messaging_redpanda.envelope import (
    ActorContext,
    EventEnvelope,
    extract_trace_context,
    inject_trace_headers,
)
from tailored_kit.telemetry_otel.setup import get_current_trace_context, setup_telemetry


def test_event_envelope_serialization_and_defaults():
    env = EventEnvelope(
        event_type="documents.compile.succeeded",
        producer_service="latex-worker",
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        feature_key="studio.cv.tailor",
        actor=ActorContext(user_id="u_1", analytics_anon_id="a_1"),
        payload={"doc_id": "doc_123"},
    )
    raw = env.model_dump_json()
    restored = EventEnvelope.model_validate_json(raw)
    assert restored.event_type == "documents.compile.succeeded"
    assert restored.schema_version == "1.0"
    assert restored.feature_key == "studio.cv.tailor"
    assert restored.actor.analytics_anon_id == "a_1"
    assert restored.payload["doc_id"] == "doc_123"


def test_w3c_traceparent_roundtrip_across_kafka_headers():
    setup_telemetry(None, ServiceSettings(service_name="test-svc", otel_enabled=False))
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("parent-op"):
        tid, sid = get_current_trace_context()
        assert len(tid) == 32
        assert tid != "0" * 32
        headers = inject_trace_headers({"X-Feature-Key": "radar.auto_search"})

    header_dict = {k: v.decode() for k, v in headers}
    assert "traceparent" in header_dict
    assert tid in header_dict["traceparent"]
    assert header_dict["X-Feature-Key"] == "radar.auto_search"

    extracted = extract_trace_context(headers)
    with tracer.start_as_current_span("child-op", context=extracted):
        child_tid, child_sid = get_current_trace_context()
        assert child_tid == tid
        assert child_sid != sid
