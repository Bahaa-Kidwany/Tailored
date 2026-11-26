from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import clickhouse_connect
from fastapi import FastAPI, Request, status
from pydantic import BaseModel, Field

from tailored_kit import (
    ActorContext,
    EventEnvelope,
    RedpandaConsumer,
    RedpandaProducer,
    ServiceSettings,
    audit_feature,
    create_service_app,
)
from tailored_kit.feature_context import get_current_feature_key
from tailored_kit.telemetry_otel.setup import get_current_trace_context

logger = logging.getLogger(__name__)

FORBIDDEN_PII_KEYS = {
    "email",
    "phone",
    "phone_number",
    "raw_cv",
    "latex_content",
    "password",
    "notes",
    "message_text",
}


class TelemetrySettings(ServiceSettings):
    service_name: str = "telemetry-audit-service"
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_user: str = "tailored_ch"
    clickhouse_password: str = "tailored_ch_dev_pass"


settings = TelemetrySettings()


class TelemetryEventItem(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    feature_key: str
    event_name: str
    route: str = "/"
    persona_track: str = "unknown"
    job_id: Optional[str] = None
    doc_id: Optional[str] = None
    duration_ms: int = 0
    scroll_depth_pct: int = 0
    numeric_value: float = 0.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class TelemetryBatchRequest(BaseModel):
    events: List[TelemetryEventItem] = Field(default_factory=list, max_length=100)


def _scrub_properties(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in raw.items() if k.lower() not in FORBIDDEN_PII_KEYS}


def _fixed(value: Optional[str], length: int, fill: str = "0") -> str:
    s = (value or "").strip()
    if len(s) >= length:
        return s[:length]
    return s.ljust(length, fill)


def _parse_uuid(value: Optional[str], fallback: Optional[UUID] = None) -> Optional[UUID]:
    if not value:
        return fallback
    try:
        return UUID(str(value))
    except Exception:
        return fallback


def _get_ch_client():
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )


def _insert_audit_row(envelope: EventEnvelope) -> None:
    p = envelope.payload
    client = _get_ch_client()
    try:
        client.insert(
            table="tailored_audit.feature_audit_logs",
            data=[[
                _parse_uuid(envelope.event_id, uuid4()),
                envelope.occurred_at.astimezone(timezone.utc).replace(tzinfo=None),
                _fixed(envelope.trace_id, 32),
                _fixed(envelope.span_id, 16),
                p.get("feature_key") or envelope.feature_key or "unknown",
                p.get("service_name") or envelope.producer_service,
                p.get("action") or "execute",
                p.get("outcome") or "success",
                _fixed(p.get("actor_user_id_hash"), 64),
                p.get("resource_type") or "generic",
                str(p.get("resource_id") or ""),
                _fixed(p.get("before_hash"), 64),
                _fixed(p.get("after_hash"), 64),
                str(p.get("diff_summary") or "{}"),
                int(p.get("credit_delta") or 0),
                int(p.get("duration_ms") or 0),
                str(p.get("active_flags_json") or "{}"),
                str(p.get("error_code") or ""),
            ]],
            column_names=[
                "audit_id",
                "occurred_at",
                "trace_id",
                "span_id",
                "feature_key",
                "service_name",
                "action",
                "outcome",
                "actor_user_id_hash",
                "resource_type",
                "resource_id",
                "before_hash",
                "after_hash",
                "diff_summary",
                "credit_delta",
                "duration_ms",
                "active_flags_json",
                "error_code",
            ],
        )
    finally:
        client.close()


def _insert_analytics_row(envelope: EventEnvelope) -> None:
    p = envelope.payload
    client = _get_ch_client()
    try:
        occurred = envelope.occurred_at.astimezone(timezone.utc).replace(tzinfo=None)
        received = datetime.now(timezone.utc).replace(tzinfo=None)
        anon_uuid = _parse_uuid(envelope.actor.analytics_anon_id, UUID(int=0))
        sess_uuid = _parse_uuid(p.get("session_id"), UUID(int=0))
        job_uuid = _parse_uuid(p.get("job_id"), None)
        client.insert(
            table="tailored_analytics.user_behavior_events",
            data=[[
                _parse_uuid(envelope.event_id, uuid4()),
                occurred,
                received,
                anon_uuid,
                sess_uuid,
                _fixed(envelope.trace_id, 32),
                p.get("feature_key") or envelope.feature_key or "unknown",
                p.get("event_name") or envelope.event_type,
                str(p.get("route") or "/"),
                str(p.get("persona_track") or "unknown"),
                job_uuid,
                p.get("doc_id"),
                int(p.get("duration_ms") or 0),
                int(p.get("scroll_depth_pct") or 0),
                float(p.get("numeric_value") or 0.0),
                json.dumps(p.get("properties") or {}, ensure_ascii=False),
            ]],
            column_names=[
                "event_id",
                "occurred_at",
                "received_at",
                "analytics_anon_id",
                "session_id",
                "trace_id",
                "feature_key",
                "event_name",
                "route",
                "persona_track",
                "job_id",
                "doc_id",
                "duration_ms",
                "scroll_depth_pct",
                "numeric_value",
                "properties_json",
            ],
        )
    finally:
        client.close()


def _query_audit_by_trace(trace_id: str) -> List[Dict[str, Any]]:
    client = _get_ch_client()
    try:
        res = client.query(
            """
            SELECT
                toString(audit_id) AS audit_id,
                occurred_at,
                trace_id,
                span_id,
                feature_key,
                service_name,
                action,
                outcome,
                actor_user_id_hash,
                resource_type,
                resource_id,
                credit_delta,
                duration_ms,
                error_code
            FROM tailored_audit.feature_audit_logs
            WHERE trace_id = %(trace_id)s
            ORDER BY occurred_at ASC
            """,
            parameters={"trace_id": _fixed(trace_id, 32)},
        )
        cols = res.column_names
        rows: List[Dict[str, Any]] = []
        for r in res.result_rows:
            item = dict(zip(cols, r))
            if isinstance(item.get("occurred_at"), datetime):
                item["occurred_at"] = item["occurred_at"].isoformat()
            rows.append(item)
        return rows
    finally:
        client.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = RedpandaProducer(settings.redpanda_brokers)
    for attempt in range(1, 11):
        try:
            await producer.start()
            break
        except Exception as exc:
            logger.warning("Waiting for Redpanda (%s/10): %s", attempt, exc)
            await asyncio.sleep(2)
    app.state.redpanda_producer = producer

    async def on_audit(env: EventEnvelope) -> None:
        await asyncio.to_thread(_insert_audit_row, env)

    async def on_analytics(env: EventEnvelope) -> None:
        await asyncio.to_thread(_insert_analytics_row, env)

    audit_consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["audit.trail.v1"],
        group_id="clickhouse-audit-cg",
        handler=on_audit,
        dlq_producer=producer,
    )
    analytics_consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["telemetry.interactions.v1"],
        group_id="clickhouse-analytics-cg",
        handler=on_analytics,
        dlq_producer=producer,
    )
    await audit_consumer.start()
    await analytics_consumer.start()
    try:
        yield
    finally:
        await analytics_consumer.stop()
        await audit_consumer.stop()
        await producer.stop()


def _health_details(app: FastAPI) -> Dict[str, Any]:
    producer = getattr(app.state, "redpanda_producer", None)
    return {"redpanda_ready": bool(producer and producer.is_ready)}


app = create_service_app(
    settings,
    title="Tailored Telemetry & Audit Service",
    lifespan=lifespan,
    health_check_fn=_health_details,
)


@app.post("/api/v1/telemetry/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry_events(payload: TelemetryBatchRequest, request: Request) -> Dict[str, Any]:
    trace_id, span_id = get_current_trace_context()
    anon_id = request.headers.get("X-Analytics-Anon-Id") or str(UUID(int=0))
    user_id = request.headers.get("X-User-Id")
    producer: RedpandaProducer = request.app.state.redpanda_producer

    published = 0
    for item in payload.events:
        envelope = EventEnvelope(
            event_id=item.event_id,
            event_type=item.event_name,
            occurred_at=item.occurred_at,
            producer_service=settings.service_name,
            trace_id=trace_id,
            span_id=span_id,
            feature_key=item.feature_key,
            actor=ActorContext(user_id=user_id, analytics_anon_id=anon_id),
            payload={
                "session_id": item.session_id,
                "feature_key": item.feature_key,
                "event_name": item.event_name,
                "route": item.route,
                "persona_track": item.persona_track,
                "job_id": item.job_id,
                "doc_id": item.doc_id,
                "duration_ms": item.duration_ms,
                "scroll_depth_pct": item.scroll_depth_pct,
                "numeric_value": item.numeric_value,
                "properties": _scrub_properties(item.properties),
            },
        )
        await producer.publish("telemetry.interactions.v1", envelope, partition_key=anon_id)
        published += 1

    return {"accepted": published, "trace_id": trace_id}


@app.post("/internal/phase0/probe")
@audit_feature(feature_key="system.phase0.probe", resource_type="probe", action="verify")
async def phase0_probe(request: Request) -> Dict[str, Any]:
    trace_id, span_id = get_current_trace_context()
    feature_key = get_current_feature_key() or "system.phase0.probe"
    logger.info("Executed Phase 0 probe for feature_key=%s", feature_key)
    return {
        "status": "ok",
        "trace_id": trace_id,
        "span_id": span_id,
        "feature_key": feature_key,
    }


@app.get("/api/v1/admin/audit/traces/{trace_id}")
async def get_audit_trace(trace_id: str) -> Dict[str, Any]:
    rows = await asyncio.to_thread(_query_audit_by_trace, trace_id)
    return {"trace_id": trace_id, "count": len(rows), "records": rows}
