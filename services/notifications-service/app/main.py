from __future__ import annotations

import asyncio
import json
import logging
import smtplib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, delete
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    EventEnvelope,
    InternalHttpClient,
    NotFoundError,
    OutboxEvent,
    ProcessedEvent,
    RedpandaConsumer,
    RedpandaProducer,
    RequestContext,
    ServiceSettings,
    audit_feature,
    create_service_app,
    require_user,
)

from app.models import EmailDispatchLogDB, NotificationDB, NotificationRuleDB, utc_now

logger = logging.getLogger(__name__)


class NotificationsSettings(ServiceSettings):
    service_name: str = "notifications-service"
    database_url: str = "postgresql+psycopg://notifications_svc:tailored_notif_pass@postgres:5432/notifications_db"
    pipeline_service_url: str = "http://pipeline-service:8005"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "alerts@tailored.app"


settings = NotificationsSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)

NOTIF_TABLES = [
    NotificationDB.__table__,
    NotificationRuleDB.__table__,
    EmailDispatchLogDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]


def _notif_to_dict(n: NotificationDB) -> Dict[str, Any]:
    return {
        "id": n.id,
        "category": n.category,
        "title": n.title,
        "subtitle": n.subtitle,
        "timestamp": n.created_at.isoformat(),
        "read": n.read_at is not None,
        "archived": n.archived_at is not None,
        "snoozed_until": n.snoozed_until.isoformat() if n.snoozed_until else None,
        "job_id": n.job_id,
        "pipeline_id": n.pipeline_id,
        "action_label": n.action_label,
        "target_path": n.target_path,
    }


def _send_notif_email_sync(subject: str, body: str, to_addr: str) -> str:
    if not settings.smtp_host or not to_addr:
        return "logged_local"
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            if settings.smtp_port in (587, 2525):
                smtp.starttls()
            if settings.smtp_user and settings.smtp_pass:
                smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
        return "sent_smtp"
    except Exception as exc:
        logger.warning("Notification SMTP delivery error: %s", exc)
        return "smtp_failed"


async def _create_and_push_notif(
    redis_client: aioredis.Redis,
    *,
    user_id: str,
    category: str,
    title: str,
    subtitle: str,
    action_label: str,
    target_path: str,
    job_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    dedup_key: Optional[str] = None,
    fit_score: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    with Session(engine) as session:
        rule = session.get(NotificationRuleDB, user_id)
        if rule:
            if rule.digest_cadence == "off":
                return None
            if category == "followup" and not rule.followup_reminders:
                return None
            if category == "credit" and "low credit" in title.lower() and not rule.low_credit_alerts:
                return None
            if category == "match" and fit_score is not None and fit_score < float(rule.min_match_alert_score):
                return None

        if dedup_key:
            exists = session.exec(
                select(NotificationDB).where(
                    NotificationDB.user_id == user_id,
                    NotificationDB.dedup_key == dedup_key,
                )
            ).first()
            if exists:
                return None
        row = NotificationDB(
            user_id=user_id,
            category=category,
            title=title,
            subtitle=subtitle,
            action_label=action_label,
            target_path=target_path,
            job_id=job_id,
            pipeline_id=pipeline_id,
            dedup_key=dedup_key,
        )
        session.add(row)
        session.flush()
        dispatch_status = await asyncio.to_thread(_send_notif_email_sync, title, subtitle, "")
        session.add(
            EmailDispatchLogDB(
                user_id=user_id,
                template_key=f"notif.{category}",
                provider_msg_id=row.id,
                status=dispatch_status,
            )
        )
        session.commit()
        session.refresh(row)
        data = _notif_to_dict(row)

    await redis_client.publish(f"sse:notif:{user_id}", json.dumps({"event": "notification", "data": data}))
    return data


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=NOTIF_TABLES)
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    internal_http = InternalHttpClient(
        caller_service=settings.service_name,
        hmac_secret=settings.internal_hmac_secret,
        timeout_seconds=4.0,
    )
    app.state.internal_http = internal_http

    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable (%s)", exc)
    app.state.redpanda_producer = producer

    async def on_event(env: EventEnvelope) -> None:
        p = env.payload
        uid = p.get("user_id") or env.actor.user_id
        if not uid:
            return

        if env.event_type == "user.erasure.requested":
            with Session(engine) as session:
                session.exec(delete(NotificationDB).where(NotificationDB.user_id == uid))
                session.exec(delete(NotificationRuleDB).where(NotificationRuleDB.user_id == uid))
                session.exec(delete(EmailDispatchLogDB).where(EmailDispatchLogDB.user_id == uid))
                session.commit()
            return

        if env.event_type == "job.high_match.detected":
            raw_fit = float(p.get("fit_score", 90))
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="match",
                title=f"{raw_fit}% Match: {p.get('company_name', '')} — {p.get('title', '')}",
                subtitle="High-fit role discovered in your Radar feed.",
                action_label="Tailor CV · 1 cr",
                target_path="/studio",
                job_id=p.get("job_id"),
                dedup_key=f"match:{p.get('job_id')}",
                fit_score=raw_fit,
            )
        elif env.event_type == "latex.compile.succeeded":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="document",
                title=f"PDF Ready: {p.get('doc_id', 'Tailored CV')}",
                subtitle="1-Page ATS PDF compiled and archived cleanly.",
                action_label="Open Studio",
                target_path="/studio",
                dedup_key=f"pdf:{p.get('doc_id')}:v{p.get('version_no', 1)}",
            )
        elif env.event_type == "credits.refunded":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="credit",
                title=f"Automatic Credit Refund (+{p.get('amount', 1)} cr)",
                subtitle=f"Returned automatically because compilation failed ({p.get('doc_id', '')}).",
                action_label="View Ledger",
                target_path="/plans",
                dedup_key=f"refund:{p.get('hold_id')}",
            )
        elif env.event_type == "credits.pack.purchased":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="credit",
                title=f"+{p.get('credits_granted', 0)} Credits Added",
                subtitle=f"Available balance: {p.get('available_credits', 0)} credits (never expire).",
                action_label="View Wallet",
                target_path="/plans",
                dedup_key=f"purchase:{p.get('order_id')}",
            )
        elif env.event_type == "credits.low_balance":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="credit",
                title=f"Low Credit Balance ({p.get('available_credits', 0)} cr left)",
                subtitle="Top up anytime — discovery & Studio AI edits remain 0 cr.",
                action_label="Top Up",
                target_path="/plans",
            )
        elif env.event_type == "pipeline.item.applied":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="followup",
                title=f"Applied: {p.get('company_name', '')} — {p.get('job_title', '')}",
                subtitle="Documents frozen cleanly; 7-day follow-up reminder armed.",
                action_label="View Thread",
                target_path=f"/pipeline/{p.get('pipeline_item_id', '')}",
                pipeline_id=p.get("pipeline_item_id"),
                dedup_key=f"applied:{p.get('pipeline_item_id')}",
            )
        elif env.event_type == "ai.suggestion.emitted":
            await _create_and_push_notif(
                redis_client,
                user_id=uid,
                category="ai_insight",
                title=p.get("title", "AI Career Insight"),
                subtitle=p.get("body", ""),
                action_label="Review",
                target_path=p.get("cta_route", "/dashboard"),
                dedup_key=f"ai_sugg:{p.get('suggestion_id')}",
            )

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=[
            "jobs.events.v1",
            "documents.events.v1",
            "billing.events.v1",
            "pipeline.events.v1",
            "ai.events.v1",
            "identity.lifecycle.v1",
        ],
        group_id="notif-fanout-cg",
        handler=on_event,
        dlq_producer=producer,
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("Consumer delayed (%s)", exc)

    stop_evt = asyncio.Event()

    async def _followup_and_digest_scheduler() -> None:
        await asyncio.sleep(5.0)
        while not stop_evt.is_set():
            try:
                resp = await internal_http.get(f"{settings.pipeline_service_url}/internal/pipeline/overdue-followups")
                if resp.status_code == 200:
                    for item in resp.json():
                        await _create_and_push_notif(
                            redis_client,
                            user_id=item["user_id"],
                            category="followup",
                            title=f"7-Day Follow-Up Due: {item.get('company_name', '')}",
                            subtitle=f"Check in on your {item.get('job_title', 'application')} submission.",
                            action_label="Draft Follow-Up",
                            target_path=f"/pipeline/{item['id']}",
                            pipeline_id=item["id"],
                            dedup_key=f"overdue_7d:{item['id']}",
                        )
            except Exception as exc:
                logger.warning("Overdue follow-up check skipped: %s", exc)
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=300.0)
            except asyncio.TimeoutError:
                pass

    sched_task = asyncio.create_task(_followup_and_digest_scheduler())

    try:
        yield
    finally:
        stop_evt.set()
        sched_task.cancel()
        try:
            await sched_task
        except asyncio.CancelledError:
            pass
        await consumer.stop()
        await internal_http.close()
        await producer.stop()
        await redis_client.aclose()


app = create_service_app(
    settings,
    title="Tailored Notifications & SSE Center",
    lifespan=lifespan,
)


# --- Schemas ---

class SnoozeRequest(BaseModel):
    hours: int = 72


class NotificationRulesPatch(BaseModel):
    min_match_alert_score: Optional[int] = None
    digest_cadence: Optional[str] = None
    followup_reminders: Optional[bool] = None
    low_credit_alerts: Optional[bool] = None


# --- Endpoints ---

@app.get("/api/v1/notifications")
async def list_notifications(
    category: Optional[str] = Query(default=None),
    unread_only: bool = Query(default=False),
    ctx: RequestContext = Depends(require_user),
) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        stmt = select(NotificationDB).where(
            NotificationDB.user_id == ctx.user_id,
            NotificationDB.archived_at.is_(None),
        )
        if category and category != "all":
            stmt = stmt.where(NotificationDB.category == category)
        if unread_only:
            stmt = stmt.where(NotificationDB.read_at.is_(None))
        rows = session.exec(stmt.order_by(NotificationDB.created_at.desc())).all()
        return [_notif_to_dict(r) for r in rows]


@app.get("/api/v1/notifications/stream")
async def stream_notifications(request: Request, ctx: RequestContext = Depends(require_user)):
    redis_client: aioredis.Redis = request.app.state.redis
    channel = f"sse:notif:{ctx.user_id}"

    async def event_gen():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        try:
            yield f"event: ready\ndata: {json.dumps({'user_id': ctx.user_id})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("data"):
                    payload = msg["data"]
                    yield f"event: notification\ndata: {payload}\n\n"
                else:
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.patch("/api/v1/notifications/{notif_id}/read")
@audit_feature(feature_key="notifications.inbox.read", resource_type="notification", action="mark_read")
async def mark_read(
    notif_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        row = session.get(NotificationDB, notif_id)
        if not row or row.user_id != ctx.user_id:
            raise NotFoundError("Notification not found.")
        row.read_at = utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)
        return _notif_to_dict(row)


@app.patch("/api/v1/notifications/{notif_id}/snooze")
@audit_feature(feature_key="notifications.snooze", resource_type="notification", action="snooze")
async def snooze_notification(
    notif_id: str,
    payload: SnoozeRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        row = session.get(NotificationDB, notif_id)
        if not row or row.user_id != ctx.user_id:
            raise NotFoundError("Notification not found.")
        row.snoozed_until = utc_now() + timedelta(hours=payload.hours)
        row.read_at = row.read_at or utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)
        return _notif_to_dict(row)


@app.post("/api/v1/notifications/mark-all-read")
async def mark_all_read(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        rows = session.exec(
            select(NotificationDB).where(
                NotificationDB.user_id == ctx.user_id,
                NotificationDB.read_at.is_(None),
            )
        ).all()
        now = utc_now()
        for r in rows:
            r.read_at = now
            session.add(r)
        session.commit()
        return {"marked_read": len(rows)}


@app.get("/api/v1/notifications/rules")
async def get_rules(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        rule = session.get(NotificationRuleDB, ctx.user_id)
        if not rule:
            rule = NotificationRuleDB(user_id=ctx.user_id)
            session.add(rule)
            session.commit()
            session.refresh(rule)
        return rule.model_dump()


@app.patch("/api/v1/notifications/rules")
async def patch_rules(
    payload: NotificationRulesPatch, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        rule = session.get(NotificationRuleDB, ctx.user_id) or NotificationRuleDB(user_id=ctx.user_id)
        for k, v in payload.model_dump(exclude_none=True).items():
            setattr(rule, k, v)
        rule.updated_at = utc_now()
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule.model_dump()
