from __future__ import annotations

import json
import logging
import urllib.parse
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, delete
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    EventEnvelope,
    InternalHttpClient,
    NotFoundError,
    OutboxEvent,
    OutboxRelay,
    ProcessedEvent,
    RedpandaConsumer,
    RedpandaProducer,
    RequestContext,
    ServiceSettings,
    audit_feature,
    create_service_app,
    require_internal_service,
    require_user,
)
from tailored_kit.telemetry_otel.setup import get_current_trace_context

from app.models import InterviewRoundNoteDB, OutreachDispatchDB, PipelineItemDB, utc_now

logger = logging.getLogger(__name__)


class PipelineSettings(ServiceSettings):
    service_name: str = "pipeline-service"
    database_url: str = "postgresql+psycopg://pipeline_svc:tailored_pipeline_pass@postgres:5432/pipeline_db"
    jobs_service_url: str = "http://jobs-service:8003"
    profile_service_url: str = "http://profile-service:8002"
    documents_service_url: str = "http://documents-service:8004"


settings = PipelineSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)

PIPELINE_TABLES = [
    PipelineItemDB.__table__,
    InterviewRoundNoteDB.__table__,
    OutreachDispatchDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]


def _enqueue_outbox(
    session: Session,
    *,
    event_type: str,
    user_id: str,
    anon_id: Optional[str],
    feature_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type="pipeline_item",
            aggregate_id=payload.get("pipeline_item_id") or user_id,
            topic="pipeline.events.v1",
            event_type=event_type,
            partition_key=user_id,
            payload_json=json.dumps(payload, default=str),
            headers_json=json.dumps(
                {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "feature_key": feature_key,
                    "actor": {"user_id": user_id, "analytics_anon_id": anon_id},
                }
            ),
        )
    )


def _item_to_dict(session: Session, item: PipelineItemDB) -> Dict[str, Any]:
    rounds = session.exec(
        select(InterviewRoundNoteDB)
        .where(InterviewRoundNoteDB.pipeline_item_id == item.id)
        .order_by(InterviewRoundNoteDB.created_at.asc())
    ).all()
    dispatches = session.exec(
        select(OutreachDispatchDB)
        .where(OutreachDispatchDB.pipeline_item_id == item.id)
        .order_by(OutreachDispatchDB.dispatched_at.desc())
    ).all()
    return {
        "id": item.id,
        "user_id": item.user_id,
        "job_id": item.job_id,
        "status": item.status,
        "channel_type": item.channel_type,
        "recruiter_name": item.recruiter_name,
        "recruiter_email": item.recruiter_email,
        "job_title": item.job_title_snapshot,
        "company_name": item.company_snapshot,
        "job_url": item.job_url_snapshot,
        "tailored_cv_doc_id": item.tailored_cv_doc_id,
        "cover_letter_doc_id": item.cover_letter_doc_id,
        "frozen_snapshot_id": item.frozen_snapshot_id,
        "notes": item.notes,
        "compensation_notes": item.compensation_notes,
        "saved_at": item.saved_at.isoformat(),
        "applied_at": item.applied_at.isoformat() if item.applied_at else None,
        "follow_up_due_at": item.follow_up_due_at.isoformat() if item.follow_up_due_at else None,
        "interview_date": item.interview_date.isoformat() if item.interview_date else None,
        "updated_at": item.updated_at.isoformat(),
        "rounds": [r.model_dump() for r in rounds],
        "dispatches": [d.model_dump() for d in dispatches],
    }


def _delete_user_pipeline(user_id: str) -> None:
    with Session(engine) as session:
        items = session.exec(select(PipelineItemDB).where(PipelineItemDB.user_id == user_id)).all()
        for it in items:
            session.exec(delete(InterviewRoundNoteDB).where(InterviewRoundNoteDB.pipeline_item_id == it.id))
            session.exec(delete(OutreachDispatchDB).where(OutreachDispatchDB.pipeline_item_id == it.id))
        session.exec(delete(PipelineItemDB).where(PipelineItemDB.user_id == user_id))
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=PIPELINE_TABLES)
    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable (%s)", exc)
    app.state.redpanda_producer = producer

    relay = OutboxRelay(
        session_factory=lambda: Session(engine),
        producer=producer,
        service_name=settings.service_name,
    )
    await relay.start()

    internal_http = InternalHttpClient(
        caller_service=settings.service_name,
        hmac_secret=settings.internal_hmac_secret,
        timeout_seconds=5.0,
    )
    app.state.internal_http = internal_http

    async def on_identity_event(env: EventEnvelope) -> None:
        if env.event_type == "user.erasure.requested":
            uid = env.payload.get("user_id") or env.actor.user_id
            if uid:
                _delete_user_pipeline(uid)

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["identity.lifecycle.v1"],
        group_id="pipeline-erasure-cg",
        handler=on_identity_event,
        dlq_producer=producer,
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("Consumer delayed (%s)", exc)

    try:
        yield
    finally:
        await consumer.stop()
        await internal_http.close()
        await relay.stop()
        await producer.stop()


app = create_service_app(
    settings,
    title="Tailored Application Pipeline CRM Service",
    lifespan=lifespan,
)


# --- Schemas ---

class PipelineCreateRequest(BaseModel):
    job_id: str
    status: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_name: str = ""
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_url: Optional[str] = None
    tailored_cv_doc_id: Optional[str] = None
    cover_letter_doc_id: Optional[str] = None
    notes: str = ""


class PipelineUpdateRequest(BaseModel):
    status: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_name: Optional[str] = None
    tailored_cv_doc_id: Optional[str] = None
    cover_letter_doc_id: Optional[str] = None
    notes: Optional[str] = None
    compensation_notes: Optional[str] = None
    interview_date: Optional[datetime] = None


class InterviewRoundCreate(BaseModel):
    round_title: str
    interviewer: str = ""
    notes: str = ""
    outcome: str = "pending"
    scheduled_at: Optional[datetime] = None


class DispatchRequest(BaseModel):
    dispatch_channel: str = "gmail_web"
    to_email: Optional[str] = None
    subject: Optional[str] = None
    body_preview: str = ""
    cv_doc_id: Optional[str] = None
    cl_doc_id: Optional[str] = None


class BatchImportRequest(BaseModel):
    items: List[PipelineCreateRequest] = Field(default_factory=list)


# --- Helpers ---

async def _freeze_snapshot(
    client: InternalHttpClient,
    *,
    user_id: str,
    item: PipelineItemDB,
) -> Optional[str]:
    try:
        resp = await client.post(
            f"{settings.documents_service_url}/internal/documents/freeze-snapshot",
            json={
                "user_id": user_id,
                "pipeline_item_id": item.id,
                "cv_doc_id": item.tailored_cv_doc_id,
                "cl_doc_id": item.cover_letter_doc_id,
            },
        )
        if resp.status_code == 200:
            return resp.json().get("snapshot_id")
    except Exception as exc:
        logger.warning("Snapshot freeze skipped (%s)", exc)
    return None


# --- Endpoints ---

@app.get("/api/v1/pipeline")
async def list_pipeline(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    q: Optional[str] = Query(default=None),
    ctx: RequestContext = Depends(require_user),
) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        stmt = select(PipelineItemDB).where(PipelineItemDB.user_id == ctx.user_id)
        if status_filter and status_filter != "all":
            stmt = stmt.where(PipelineItemDB.status == status_filter)
        rows = session.exec(stmt.order_by(PipelineItemDB.updated_at.desc())).all()
        if q:
            ql = q.lower()
            rows = [
                r
                for r in rows
                if ql in r.job_title_snapshot.lower()
                or ql in r.company_snapshot.lower()
                or ql in (r.recruiter_email or "").lower()
            ]
        return [_item_to_dict(session, r) for r in rows]


@app.get("/api/v1/pipeline/metrics")
async def get_metrics(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        rows = session.exec(select(PipelineItemDB).where(PipelineItemDB.user_id == ctx.user_id)).all()
        now = utc_now()
        overdue = 0
        for r in rows:
            if r.status == "applied" and r.follow_up_due_at:
                f_due = r.follow_up_due_at
                if f_due.tzinfo is None:
                    f_due = f_due.replace(tzinfo=now.tzinfo)
                if f_due <= now and not r.follow_up_sent_at:
                    overdue += 1
        return {
            "total": len(rows),
            "saved": sum(1 for r in rows if r.status == "saved"),
            "in_process": sum(1 for r in rows if r.status == "in_process"),
            "applied": sum(1 for r in rows if r.status == "applied"),
            "interview": sum(1 for r in rows if r.status == "interview"),
            "archived": sum(1 for r in rows if r.status == "archived"),
            "with_email": sum(1 for r in rows if bool(r.recruiter_email)),
            "overdue_followups": overdue,
        }


@app.post("/api/v1/pipeline", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="pipeline.item.create", resource_type="pipeline_item", action="create")
async def create_pipeline_item(
    payload: PipelineCreateRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    job_ctx: Dict[str, Any] = {}
    try:
        jr = await client.get(
            f"{settings.jobs_service_url}/internal/jobs/{payload.job_id}/fit-context",
            params={"user_id": ctx.user_id},
        )
        if jr.status_code == 200:
            job_ctx = jr.json()
    except Exception:
        pass

    recruiter_email = payload.recruiter_email or job_ctx.get("recruiter_email")
    channel = "direct_email" if recruiter_email else "external_portal"
    initial_status = payload.status or ("in_process" if recruiter_email else "saved")

    with Session(engine) as session:
        existing = session.exec(
            select(PipelineItemDB).where(
                PipelineItemDB.user_id == ctx.user_id,
                PipelineItemDB.job_id == payload.job_id,
            )
        ).first()
        if existing:
            if payload.status:
                existing.status = payload.status
            if recruiter_email:
                existing.recruiter_email = recruiter_email
                existing.channel_type = "direct_email"
            if payload.tailored_cv_doc_id:
                existing.tailored_cv_doc_id = payload.tailored_cv_doc_id
            if payload.cover_letter_doc_id:
                existing.cover_letter_doc_id = payload.cover_letter_doc_id
            existing.updated_at = utc_now()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return _item_to_dict(session, existing)

        item = PipelineItemDB(
            user_id=ctx.user_id,
            job_id=payload.job_id,
            status=initial_status,
            channel_type=channel,
            recruiter_name=payload.recruiter_name,
            recruiter_email=recruiter_email,
            job_title_snapshot=payload.job_title or job_ctx.get("title") or "Target Role",
            company_snapshot=payload.company_name or job_ctx.get("company_name") or "Target Company",
            job_url_snapshot=payload.job_url or job_ctx.get("url") or "",
            tailored_cv_doc_id=payload.tailored_cv_doc_id,
            cover_letter_doc_id=payload.cover_letter_doc_id,
            notes=payload.notes,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return _item_to_dict(session, item)


@app.get("/api/v1/pipeline/{item_id}")
async def get_pipeline_item(item_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")
        return _item_to_dict(session, item)


@app.patch("/api/v1/pipeline/{item_id}")
@audit_feature(feature_key="pipeline.stage.update", resource_type="pipeline_item", action="update")
async def update_pipeline_item(
    item_id: str,
    payload: PipelineUpdateRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")

        old_status = item.status
        for field_name, val in payload.model_dump(exclude_none=True).items():
            setattr(item, field_name, val)

        if payload.recruiter_email:
            item.channel_type = "direct_email"

        if payload.status == "applied" and old_status != "applied":
            now = utc_now()
            item.applied_at = item.applied_at or now
            item.follow_up_due_at = now + timedelta(days=7)
            snap_id = await _freeze_snapshot(client, user_id=ctx.user_id, item=item)
            if snap_id:
                item.frozen_snapshot_id = snap_id
            _enqueue_outbox(
                session,
                event_type="pipeline.item.applied",
                user_id=ctx.user_id,
                anon_id=ctx.analytics_anon_id,
                feature_key="pipeline.stage.update",
                payload={
                    "user_id": ctx.user_id,
                    "pipeline_item_id": item.id,
                    "job_id": item.job_id,
                    "company_name": item.company_snapshot,
                    "job_title": item.job_title_snapshot,
                    "frozen_snapshot_id": item.frozen_snapshot_id,
                },
            )
        item.updated_at = utc_now()
        session.add(item)
        session.commit()
        session.refresh(item)
        return _item_to_dict(session, item)


@app.delete("/api/v1/pipeline/{item_id}")
async def delete_pipeline_item(item_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")
        session.exec(delete(InterviewRoundNoteDB).where(InterviewRoundNoteDB.pipeline_item_id == item.id))
        session.exec(delete(OutreachDispatchDB).where(OutreachDispatchDB.pipeline_item_id == item.id))
        session.delete(item)
        session.commit()
        return {"deleted": item_id}


@app.post("/api/v1/pipeline/{item_id}/rounds", status_code=status.HTTP_201_CREATED)
async def add_interview_round(
    item_id: str, payload: InterviewRoundCreate, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")
        note = InterviewRoundNoteDB(
            pipeline_item_id=item.id,
            round_title=payload.round_title,
            interviewer=payload.interviewer,
            notes=payload.notes,
            outcome=payload.outcome,
            scheduled_at=payload.scheduled_at,
        )
        session.add(note)
        session.commit()
        session.refresh(note)
        return note.model_dump()


@app.get("/api/v1/pipeline/{item_id}/outreach")
async def get_outreach_package(
    item_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    prof: Dict[str, Any] = {}
    try:
        pr = await client.get(f"{settings.profile_service_url}/internal/profiles/{ctx.user_id}/summary")
        if pr.status_code == 200:
            prof = pr.json().get("profile") or {}
    except Exception:
        pass
    pi = prof.get("personal_info") or {}
    cand_name = pi.get("full_name") or "Candidate"
    cand_email = pi.get("primary_email") or ""
    nums = pi.get("contact_numbers") or []
    cand_phone = f"{nums[0].get('dial_code', '')} {nums[0].get('phone_number', '')}".strip() if nums else ""

    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")
        to_email = item.recruiter_email or ""
        subject = f"Application for {item.job_title_snapshot} — {cand_name}"
        body = (
            f"Dear {item.recruiter_name or item.company_snapshot + ' Hiring Team'},\n\n"
            f"Please find my tailored CV attached for the {item.job_title_snapshot} position at {item.company_snapshot}.\n\n"
            f"Best regards,\n{cand_name}\n{cand_phone}"
        )
        q_to = urllib.parse.quote(to_email)
        q_sub = urllib.parse.quote(subject)
        q_body = urllib.parse.quote(body)
        return {
            "item_id": item.id,
            "job_title": item.job_title_snapshot,
            "company_name": item.company_snapshot,
            "to_email": to_email,
            "subject": subject,
            "body_markdown": body,
            "gmail_web_url": f"https://mail.google.com/mail/?view=cm&fs=1&to={q_to}&su={q_sub}&body={q_body}",
            "mailto_url": f"mailto:{to_email}?subject={q_sub}&body={q_body}",
            "cv_pdf_download_url": (
                f"/api/v1/cv-fit/{item.tailored_cv_doc_id}/download/pdf"
                if item.tailored_cv_doc_id
                else None
            ),
            "cover_letter_download_url": (
                f"/api/v1/cover-letter/{item.cover_letter_doc_id}/download"
                if item.cover_letter_doc_id
                else None
            ),
            "candidate_name": cand_name,
            "candidate_email": cand_email,
            "candidate_phone": cand_phone,
        }


@app.post("/api/v1/pipeline/{item_id}/dispatch")
@audit_feature(feature_key="pipeline.outreach.dispatch", resource_type="outreach_dispatch", action="dispatch")
async def dispatch_application(
    item_id: str,
    payload: DispatchRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    with Session(engine) as session:
        item = session.get(PipelineItemDB, item_id)
        if not item or item.user_id != ctx.user_id:
            raise NotFoundError("Pipeline item not found.")
        if payload.cv_doc_id:
            item.tailored_cv_doc_id = payload.cv_doc_id
        if payload.cl_doc_id:
            item.cover_letter_doc_id = payload.cl_doc_id
        snap_id = await _freeze_snapshot(client, user_id=ctx.user_id, item=item)
        if snap_id:
            item.frozen_snapshot_id = snap_id
        now = utc_now()
        item.status = "applied"
        item.applied_at = now
        item.follow_up_due_at = now + timedelta(days=7)
        item.updated_at = now
        session.add(item)

        dispatch = OutreachDispatchDB(
            pipeline_item_id=item.id,
            dispatch_channel=payload.dispatch_channel,
            to_email=payload.to_email or item.recruiter_email,
            subject=payload.subject or f"Application for {item.job_title_snapshot}",
            body_preview=payload.body_preview[:500],
        )
        session.add(dispatch)
        _enqueue_outbox(
            session,
            event_type="pipeline.item.applied",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="pipeline.outreach.dispatch",
            payload={
                "user_id": ctx.user_id,
                "pipeline_item_id": item.id,
                "job_id": item.job_id,
                "company_name": item.company_snapshot,
                "job_title": item.job_title_snapshot,
                "frozen_snapshot_id": item.frozen_snapshot_id,
            },
        )
        session.commit()
        session.refresh(item)
        return _item_to_dict(session, item)


@app.post("/api/v1/pipeline/batch-import")
async def batch_import(
    payload: BatchImportRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    imported = 0
    for item_in in payload.items:
        await create_pipeline_item(item_in, request, ctx)
        imported += 1
    return {"imported": imported}


@app.patch("/internal/pipeline/by-job/{job_id}")
async def internal_update_by_job(
    job_id: str,
    payload: Dict[str, Any],
    request: Request,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    user_id = payload.get("user_id")
    next_status = payload.get("status", "applied")
    if not user_id:
        raise NotFoundError("user_id required")
    client: InternalHttpClient = request.app.state.internal_http

    with Session(engine) as session:
        item = session.exec(
            select(PipelineItemDB).where(
                PipelineItemDB.user_id == user_id,
                PipelineItemDB.job_id == job_id,
            )
        ).first()
        if not item:
            item = PipelineItemDB(
                user_id=user_id,
                job_id=job_id,
                status=next_status,
                job_title_snapshot=payload.get("job_title", "Target Role"),
                company_snapshot=payload.get("company_name", "Target Company"),
            )
            session.add(item)
            session.flush()
        else:
            item.status = next_status
        if next_status == "applied":
            now = utc_now()
            item.applied_at = now
            item.follow_up_due_at = now + timedelta(days=7)
            snap_id = await _freeze_snapshot(client, user_id=user_id, item=item)
            if snap_id:
                item.frozen_snapshot_id = snap_id
        item.updated_at = utc_now()
        session.add(item)
        session.commit()
        session.refresh(item)
        return _item_to_dict(session, item)


@app.get("/internal/pipeline/overdue-followups")
async def internal_overdue_followups(
    _: RequestContext = Depends(require_internal_service),
) -> List[Dict[str, Any]]:
    now = utc_now()
    with Session(engine) as session:
        rows = session.exec(
            select(PipelineItemDB).where(
                PipelineItemDB.status == "applied",
                PipelineItemDB.follow_up_due_at.is_not(None),
                PipelineItemDB.follow_up_due_at <= now,
            )
        ).all()
        return [
            {
                "id": it.id,
                "user_id": it.user_id,
                "job_id": it.job_id,
                "company_name": it.company_snapshot,
                "job_title": it.job_title_snapshot,
                "recruiter_email": it.recruiter_email,
            }
            for it in rows
        ]
