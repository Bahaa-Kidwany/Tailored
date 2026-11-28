from __future__ import annotations

import base64
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.client import Config as BotoConfig
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

from app.models import JobDB, JobFitScoreDB, ScrapeRunDB, UserJobInteractionDB, utc_now
from app.ranking import (
    compute_canonical_hash,
    evaluate_job_all_personas,
    extract_recruiter_email,
    extract_skills_and_meta,
)

logger = logging.getLogger(__name__)


class JobsSettings(ServiceSettings):
    service_name: str = "jobs-service"
    database_url: str = "postgresql+psycopg://jobs_svc:tailored_jobs_pass@postgres:5432/jobs_db"
    profile_service_url: str = "http://profile-service:8002"
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "tailored_minio"
    minio_root_password: str = "tailored_minio_dev_pass"


settings = JobsSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)

JOBS_TABLES = [
    JobDB.__table__,
    JobFitScoreDB.__table__,
    UserJobInteractionDB.__table__,
    ScrapeRunDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]

SEED_JOBS = [
    {
        "legacy_int_id": 101,
        "source_id": "linkedin_mena_101",
        "title": "Lead Data Scientist (Dynamic Pricing & Fleet Optimization)",
        "company_name": "Swvl",
        "location": "Cairo, Egypt (Hybrid)",
        "country": "Egypt",
        "work_mode": "Hybrid",
        "url": "https://www.linkedin.com/jobs/view/3920192801",
        "source_type": "linkedin",
        "raw_description": (
            "Swvl is seeking a Lead Data Scientist to build dynamic route pricing regression models and "
            "predictive demand forecasting algorithms with Python, PyTorch, SQL, FastAPI, Docker, PostgreSQL, "
            "and AWS ECS. 3+ years production ML experience."
        ),
    },
    {
        "legacy_int_id": 102,
        "source_id": "linkedin_mena_102",
        "title": "Senior Machine Learning Engineer (Search & Recommendations)",
        "company_name": "Noon",
        "location": "Riyadh, Saudi Arabia",
        "country": "Saudi Arabia",
        "work_mode": "On-site",
        "url": "https://www.linkedin.com/jobs/view/3920192802",
        "source_type": "linkedin",
        "raw_description": (
            "Join Noon in Riyadh as a Senior Machine Learning Engineer designing product search ranking and "
            "personalized recommendation engines using Python, PyTorch, HuggingFace, Docker, FastAPI, and Kubernetes. "
            "4+ years experience."
        ),
    },
    {
        "legacy_int_id": 103,
        "source_id": "wuzzuf_mena_103",
        "title": "Senior Product Data Analyst (Cross-Functional Growth)",
        "company_name": "Fawry Fintech",
        "location": "Cairo, Egypt",
        "country": "Egypt",
        "work_mode": "On-site",
        "url": "https://wuzzuf.net/jobs/p/fawry-senior-product-data-analyst",
        "source_type": "wuzzuf",
        "raw_description": (
            "Fawry is hiring a Senior Product Data Analyst to drive merchant conversion telemetry, cohort experiments, "
            "SQL warehousing, Python analytics, and executive KPI reporting across digital payments. 2+ years experience."
        ),
    },
    {
        "legacy_int_id": 104,
        "source_id": "linkedin_post_recruiter_104",
        "title": "Senior AI Systems Engineer (Direct Recruiter Post)",
        "company_name": "TechStart MENA",
        "location": "Remote (Egypt / KSA)",
        "country": "Saudi Arabia",
        "work_mode": "Remote",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7192837465",
        "source_type": "recruiter_post",
        "raw_description": (
            "Hiring immediately for a Senior AI Systems Engineer to build RAG evaluation harnesses, Python FastAPI "
            "orchestrators, and Dockerized LLM workflows. Send your tailored CV directly to sara.mansour@techstart-mena.io — "
            "3+ years experience."
        ),
    },
    {
        "legacy_int_id": 105,
        "source_id": "custom_post_105",
        "title": "Staff ML Platform Lead",
        "company_name": "Instabug",
        "location": "Cairo, Egypt (Hybrid)",
        "country": "Egypt",
        "work_mode": "Hybrid",
        "url": "https://www.linkedin.com/posts/instabug_ml-platform-lead-activity-719991122",
        "source_type": "recruiter_post",
        "raw_description": (
            "We are looking for a Staff ML Platform Lead to scale anomaly detection pipelines over mobile telemetry using "
            "Python, PyTorch, Ray, Kafka, and Docker. Apply directly at careers@instabug-demo.io. 4+ years experience."
        ),
    },
    {
        "legacy_int_id": 106,
        "source_id": "linkedin_mena_106",
        "title": "Senior BI & Marketplace Analytics Specialist",
        "company_name": "Careem",
        "location": "Riyadh, Saudi Arabia",
        "country": "Saudi Arabia",
        "work_mode": "On-site",
        "url": "https://www.linkedin.com/jobs/view/3920192806",
        "source_type": "linkedin",
        "raw_description": (
            "Careem is looking for a BI Specialist to build real-time ride tracking and captain retention dashboards. "
            "Requirements: SQL, Power BI, Python, Metabase, and A/B Testing metric formulation. 2+ years experience in Riyadh."
        ),
    },
]


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _enqueue_outbox(
    session: Session,
    *,
    topic: str,
    event_type: str,
    user_id: Optional[str],
    anon_id: Optional[str],
    feature_key: str,
    partition_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type="job",
            aggregate_id=partition_key,
            topic=topic,
            event_type=event_type,
            partition_key=partition_key,
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


def _upsert_raw_job(session: Session, item: Dict[str, Any], *, is_public: bool = False) -> JobDB:
    title = (item.get("title") or "Target Role").strip()
    company = (item.get("company_name") or "Target Company").strip()
    location = (item.get("location") or "Remote").strip()
    chash = item.get("canonical_hash") or compute_canonical_hash(company, title, location)

    existing = session.exec(select(JobDB).where(JobDB.canonical_hash == chash)).first()
    if existing:
        return existing

    raw_desc = item.get("raw_description") or ""
    skills, responsibilities, min_years, inferred_mode = extract_skills_and_meta(raw_desc, title)
    recruiter_email = item.get("recruiter_email") or extract_recruiter_email(raw_desc)
    work_mode = item.get("work_mode") or inferred_mode

    insights = {
        "normalized_title": title,
        "work_mode": work_mode,
        "minimum_years": min_years,
        "core_responsibilities": responsibilities,
        "skills_and_technologies": {"mandatory_skills": skills, "nice_to_have_skills": []},
    }
    job = JobDB(
        legacy_int_id=item.get("legacy_int_id"),
        source_id=item.get("source_id") or f"ingest_{uuid4().hex[:10]}",
        canonical_hash=chash,
        title=title,
        company_name=company,
        location=location,
        country=item.get("country") or ("Saudi Arabia" if "riyadh" in location.lower() else "Egypt"),
        work_mode=work_mode,
        url=item.get("url") or "",
        source_type=item.get("source_type") or ("recruiter_post" if recruiter_email else "web"),
        recruiter_email=recruiter_email,
        raw_description=raw_desc,
        insights_json=json.dumps(insights),
        parsed_skills_json=json.dumps(skills),
        is_public_explore=is_public,
    )
    session.add(job)
    session.flush()
    return job


def _seed_initial_jobs() -> None:
    with Session(engine) as session:
        if session.exec(select(JobDB)).first():
            return
        for item in SEED_JOBS:
            _upsert_raw_job(session, item, is_public=True)
        session.commit()


def _job_to_dict(
    job: JobDB,
    *,
    fit: Optional[JobFitScoreDB] = None,
    interaction: Optional[UserJobInteractionDB] = None,
    strip_pii: bool = False,
) -> Dict[str, Any]:
    insights = json.loads(job.insights_json or "{}")
    skills = json.loads(job.parsed_skills_json or "[]")
    data: Dict[str, Any] = {
        "id": job.id,
        "legacy_int_id": job.legacy_int_id,
        "source_id": job.source_id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "country": job.country,
        "location_type": job.work_mode,
        "work_mode": job.work_mode,
        "url": job.url,
        "source_type": job.source_type,
        "raw_description": job.raw_description,
        "parsed_skills": skills,
        "responsibilities": insights.get("core_responsibilities") or [],
        "created_at": job.created_at.isoformat(),
    }
    if not strip_pii:
        data["recruiter_email"] = job.recruiter_email
    if fit:
        data["fit_score"] = round(fit.overall_score, 1)
        data["is_high_match"] = fit.overall_score >= 85.0
        data["match_level"] = fit.match_level
        data["best_persona_id"] = fit.best_persona_id
        data["dimensions"] = json.loads(fit.dimensions_json or "{}")
        data["persona_breakdown"] = json.loads(fit.persona_breakdown_json or "[]")
        data["tailoring_guidance"] = json.loads(fit.tailoring_guidance_json or "{}")
    if interaction:
        data["in_interest_list"] = interaction.in_interest_list
        data["is_hidden"] = interaction.is_hidden
    return data


async def _fetch_user_profile(client: InternalHttpClient, user_id: str) -> Dict[str, Any]:
    try:
        resp = await client.get(f"{settings.profile_service_url}/internal/profiles/{user_id}/summary")
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning("Failed fetching profile summary for user_id=%s: %s", user_id, exc)
    return {"version": 1, "profile": {}}


def _score_and_cache(
    session: Session,
    *,
    user_id: str,
    job: JobDB,
    profile_summary: Dict[str, Any],
) -> JobFitScoreDB:
    profile = profile_summary.get("profile") or {}
    p_version = int(profile_summary.get("version") or 1)
    existing = session.exec(
        select(JobFitScoreDB).where(JobFitScoreDB.user_id == user_id, JobFitScoreDB.job_id == job.id)
    ).first()
    if existing and existing.profile_version == p_version:
        return existing

    insights = json.loads(job.insights_json or "{}")
    job_payload = {
        "title": job.title,
        "location": job.location,
        "work_mode": job.work_mode,
        "parsed_skills": json.loads(job.parsed_skills_json or "[]"),
        "min_years": insights.get("minimum_years", 2),
        "raw_description": job.raw_description,
    }
    eval_res = evaluate_job_all_personas(job_payload, profile)

    if existing:
        fit = existing
    else:
        fit = JobFitScoreDB(user_id=user_id, job_id=job.id)

    fit.best_persona_id = eval_res["best_persona_id"]
    fit.overall_score = eval_res["overall_score"]
    fit.match_level = eval_res["match_level"]
    fit.dimensions_json = json.dumps(eval_res["dimensions"])
    fit.persona_breakdown_json = json.dumps(eval_res["persona_breakdown"])
    fit.tailoring_guidance_json = json.dumps(eval_res["tailoring_guidance"])
    fit.profile_version = p_version
    fit.computed_at = utc_now()
    session.add(fit)
    session.flush()
    return fit


def _delete_user_jobs_data(user_id: str) -> None:
    with Session(engine) as session:
        session.exec(delete(JobFitScoreDB).where(JobFitScoreDB.user_id == user_id))
        session.exec(delete(UserJobInteractionDB).where(UserJobInteractionDB.user_id == user_id))
        session.exec(delete(ScrapeRunDB).where(ScrapeRunDB.user_id == user_id))
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=JOBS_TABLES)
    _seed_initial_jobs()

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
        timeout_seconds=4.0,
    )
    app.state.internal_http = internal_http

    async def on_job_event(env: EventEnvelope) -> None:
        if env.event_type == "job.raw.discovered":
            with Session(engine) as session:
                job = _upsert_raw_job(session, env.payload, is_public=False)
                uid = env.actor.user_id or env.payload.get("user_id")
                if uid:
                    prof = await _fetch_user_profile(internal_http, uid)
                    fit = _score_and_cache(session, user_id=uid, job=job, profile_summary=prof)
                    if fit.overall_score >= 85.0:
                        _enqueue_outbox(
                            session,
                            topic="jobs.events.v1",
                            event_type="job.high_match.detected",
                            user_id=uid,
                            anon_id=env.actor.analytics_anon_id,
                            feature_key="radar.auto_search",
                            partition_key=uid,
                            payload={
                                "user_id": uid,
                                "job_id": job.id,
                                "title": job.title,
                                "company_name": job.company_name,
                                "fit_score": fit.overall_score,
                            },
                        )
                session.commit()

    async def on_identity_event(env: EventEnvelope) -> None:
        if env.event_type == "user.erasure.requested":
            uid = env.payload.get("user_id") or env.actor.user_id
            if uid:
                _delete_user_jobs_data(uid)

    job_consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["jobs.events.v1"],
        group_id="jobs-ingest-cg",
        handler=on_job_event,
        dlq_producer=producer,
    )
    erasure_consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["identity.lifecycle.v1"],
        group_id="jobs-erasure-cg",
        handler=on_identity_event,
        dlq_producer=producer,
    )
    try:
        await job_consumer.start()
        await erasure_consumer.start()
    except Exception as exc:
        logger.warning("Consumers delayed (%s)", exc)

    try:
        yield
    finally:
        await erasure_consumer.stop()
        await job_consumer.stop()
        await internal_http.close()
        await relay.stop()
        await producer.stop()


app = create_service_app(
    settings,
    title="Tailored Jobs & 5-D Ranking Service",
    lifespan=lifespan,
)


# --- Schemas ---

class AutoSearchRequest(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    persona_id: Optional[str] = None
    min_score: float = 0.0
    source: Optional[str] = None
    enable_live_apify: bool = False


class IngestUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None


class IngestDescriptionRequest(BaseModel):
    description: str
    title: Optional[str] = None
    company_name: Optional[str] = None
    url: Optional[str] = None
    location: Optional[str] = None


class IngestScreenshotRequest(BaseModel):
    image_base64: Optional[str] = None
    extracted_text: str = ""
    title: Optional[str] = None
    company_name: Optional[str] = None


class HideJobRequest(BaseModel):
    reason: Optional[str] = "not_interested"


# --- Endpoints ---

@app.get("/api/v1/explore/jobs")
@audit_feature(feature_key="explore.public.feed", resource_type="job", action="list_public")
async def explore_public_jobs(request: Request) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        jobs = session.exec(
            select(JobDB)
            .where(JobDB.is_public_explore == True, JobDB.is_active == True)  # noqa: E712
            .order_by(JobDB.created_at.desc())
        ).all()
        return [_job_to_dict(j, strip_pii=True) for j in jobs]


@app.get("/api/v1/jobs")
@audit_feature(feature_key="radar.feed.rank", resource_type="job", action="rank_feed")
async def list_ranked_jobs(
    request: Request,
    persona_id: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    min_score: float = Query(default=0.0),
    include_hidden: bool = Query(default=False),
    ctx: RequestContext = Depends(require_user),
) -> List[Dict[str, Any]]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    with Session(engine) as session:
        jobs = session.exec(select(JobDB).where(JobDB.is_active == True)).all()  # noqa: E712
        interactions = {
            i.job_id: i
            for i in session.exec(
                select(UserJobInteractionDB).where(UserJobInteractionDB.user_id == ctx.user_id)
            ).all()
        }
        items: List[Dict[str, Any]] = []
        for job in jobs:
            inter = interactions.get(job.id)
            if not include_hidden and inter and inter.is_hidden:
                continue
            if source and source != "all" and job.source_type.lower() != source.lower():
                continue
            fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
            # Zero-Drop: if min_score is provided > 0 for UI filtering, still keep default 0.0 Zero-Drop
            if fit.overall_score < min_score:
                continue
            item = _job_to_dict(job, fit=fit, interaction=inter, strip_pii=False)
            if persona_id:
                for pb in item.get("persona_breakdown", []):
                    if pb.get("persona_id") == persona_id:
                        item["fit_score"] = pb["overall_score"]
                        item["match_level"] = pb["match_level"]
            items.append(item)
        session.commit()
        items.sort(key=lambda x: x.get("fit_score", 0.0), reverse=True)
        return items


@app.get("/api/v1/jobs/{job_id}")
async def get_job_detail(
    job_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    with Session(engine) as session:
        job = session.get(JobDB, job_id)
        if not job and job_id.isdigit():
            job = session.exec(select(JobDB).where(JobDB.legacy_int_id == int(job_id))).first()
        if not job:
            raise NotFoundError(f"Job {job_id} not found.")
        fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id))
        session.commit()
        return _job_to_dict(job, fit=fit, interaction=inter)


@app.post("/api/v1/jobs/auto-search")
@audit_feature(feature_key="radar.auto_search", resource_type="scrape_run", action="auto_search")
async def trigger_auto_search(
    payload: AutoSearchRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    with Session(engine) as session:
        run = ScrapeRunDB(
            user_id=ctx.user_id,
            query_text=payload.query or "AI & Data Science",
            location=payload.location or "Egypt, Saudi Arabia, Remote",
            status="queued",
        )
        session.add(run)
        session.flush()
        _enqueue_outbox(
            session,
            topic="jobs.commands.v1",
            event_type="scrape.radar.requested",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="radar.auto_search",
            partition_key=ctx.user_id,
            payload={
                "scrape_run_id": run.id,
                "user_id": ctx.user_id,
                "query": run.query_text,
                "location": run.location,
                "enable_live_apify": payload.enable_live_apify,
            },
        )
        jobs = session.exec(select(JobDB).where(JobDB.is_active == True)).all()  # noqa: E712
        ranked: List[Dict[str, Any]] = []
        for j in jobs:
            fit = _score_and_cache(session, user_id=ctx.user_id, job=j, profile_summary=profile_summary)
            ranked.append(_job_to_dict(j, fit=fit))
        session.commit()
        ranked.sort(key=lambda x: x.get("fit_score", 0.0), reverse=True)
        return {"scrape_run_id": run.id, "jobs": ranked}


@app.post("/api/v1/jobs/ingest-url", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="ingest.url", resource_type="job", action="ingest_url")
async def ingest_url(
    payload: IngestUrlRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    url_low = payload.url.lower()
    is_post = any(tok in url_low for tok in ("/posts/", "/feed/update/", "activity"))
    src_type = "recruiter_post" if is_post else ("wuzzuf" if "wuzzuf" in url_low else "linkedin")
    title = payload.title or ("Direct Recruiter Opportunity" if is_post else "Imported Opportunity")
    company = payload.company_name or "Target Organization"

    with Session(engine) as session:
        job = _upsert_raw_job(
            session,
            {
                "url": payload.url,
                "title": title,
                "company_name": company,
                "location": payload.location or "Cairo / Remote",
                "source_type": src_type,
                "raw_description": f"Imported from {payload.url}. Role: {title} at {company}. Python, FastAPI, SQL, Docker.",
            },
        )
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id)) or UserJobInteractionDB(
            user_id=ctx.user_id, job_id=job.id, ingest_origin="url"
        )
        inter.in_interest_list = True
        inter.is_hidden = False
        session.add(inter)
        fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
        _enqueue_outbox(
            session,
            topic="jobs.commands.v1",
            event_type="ingest.url.requested",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="ingest.url",
            partition_key=ctx.user_id,
            payload={"job_id": job.id, "url": payload.url, "user_id": ctx.user_id},
        )
        session.commit()
        return _job_to_dict(job, fit=fit, interaction=inter)


@app.post("/api/v1/jobs/extract-description", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="ingest.jd_text", resource_type="job", action="extract_jd")
async def ingest_description(
    payload: IngestDescriptionRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    email = extract_recruiter_email(payload.description)
    with Session(engine) as session:
        job = _upsert_raw_job(
            session,
            {
                "title": payload.title or "Custom Target Role",
                "company_name": payload.company_name or "Target Organization",
                "location": payload.location or "Remote",
                "url": payload.url or f"custom://{uuid4().hex[:8]}",
                "source_type": "recruiter_post" if email else "custom_jd",
                "recruiter_email": email,
                "raw_description": payload.description,
            },
        )
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id)) or UserJobInteractionDB(
            user_id=ctx.user_id, job_id=job.id, ingest_origin="jd"
        )
        inter.in_interest_list = True
        inter.is_hidden = False
        session.add(inter)
        fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
        session.commit()
        return _job_to_dict(job, fit=fit, interaction=inter)


@app.post("/api/v1/jobs/ingest-screenshot", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="ingest.screenshot_ocr", resource_type="job", action="ingest_screenshot")
async def ingest_screenshot(
    payload: IngestScreenshotRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    object_key: Optional[str] = None
    if payload.image_base64:
        try:
            raw_bytes = base64.b64decode(payload.image_base64.split(",")[-1])
            object_key = f"jd-screens/{ctx.user_id}/{uuid4().hex[:12]}.png"
            _s3_client().put_object(Bucket="user-uploads", Key=object_key, Body=raw_bytes, ContentType="image/png")
        except Exception as exc:
            logger.warning("MinIO screenshot upload skipped (%s)", exc)

    text = payload.extracted_text.strip() or "Role imported from job post screenshot. Python, FastAPI, SQL, Docker."
    email = extract_recruiter_email(text)
    with Session(engine) as session:
        job = _upsert_raw_job(
            session,
            {
                "title": payload.title or "Screenshot Imported Role",
                "company_name": payload.company_name or "Target Organization",
                "location": "Remote",
                "url": f"screenshot://{uuid4().hex[:8]}",
                "source_type": "recruiter_post" if email else "screenshot",
                "recruiter_email": email,
                "raw_description": text,
            },
        )
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id)) or UserJobInteractionDB(
            user_id=ctx.user_id, job_id=job.id, ingest_origin="screenshot"
        )
        inter.in_interest_list = True
        inter.screenshot_object_key = object_key
        session.add(inter)
        fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
        session.commit()
        return _job_to_dict(job, fit=fit, interaction=inter)


@app.get("/api/v1/interest")
async def list_interest(request: Request, ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    profile_summary = await _fetch_user_profile(request.app.state.internal_http, ctx.user_id)
    with Session(engine) as session:
        inters = session.exec(
            select(UserJobInteractionDB).where(
                UserJobInteractionDB.user_id == ctx.user_id,
                UserJobInteractionDB.in_interest_list == True,  # noqa: E712
            )
        ).all()
        out: List[Dict[str, Any]] = []
        for inter in inters:
            job = session.get(JobDB, inter.job_id)
            if not job:
                continue
            fit = _score_and_cache(session, user_id=ctx.user_id, job=job, profile_summary=profile_summary)
            out.append(_job_to_dict(job, fit=fit, interaction=inter))
        session.commit()
        return out


@app.post("/api/v1/interest/{job_id}")
@audit_feature(feature_key="interest.job.save", resource_type="user_job_interaction", action="save")
async def save_interest(
    job_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        job = session.get(JobDB, job_id)
        if not job:
            raise NotFoundError("Job not found.")
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id)) or UserJobInteractionDB(
            user_id=ctx.user_id, job_id=job.id
        )
        inter.in_interest_list = True
        inter.is_hidden = False
        inter.updated_at = utc_now()
        session.add(inter)
        session.commit()
        return {"job_id": job.id, "in_interest_list": True}


@app.delete("/api/v1/interest/{job_id}")
async def remove_interest(job_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job_id))
        if inter:
            inter.in_interest_list = False
            inter.updated_at = utc_now()
            session.add(inter)
            session.commit()
        return {"job_id": job_id, "in_interest_list": False}


@app.post("/api/v1/jobs/{job_id}/hide")
@audit_feature(feature_key="radar.job.hide", resource_type="user_job_interaction", action="hide")
async def hide_job(
    job_id: str,
    request: Request,
    payload: HideJobRequest = HideJobRequest(),
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        job = session.get(JobDB, job_id)
        if not job:
            raise NotFoundError("Job not found.")
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job.id)) or UserJobInteractionDB(
            user_id=ctx.user_id, job_id=job.id
        )
        inter.is_hidden = True
        inter.hide_reason = payload.reason
        inter.updated_at = utc_now()
        session.add(inter)
        session.commit()
        return {"job_id": job.id, "is_hidden": True}


@app.delete("/api/v1/jobs/{job_id}/hide")
async def unhide_job(job_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        inter = session.get(UserJobInteractionDB, (ctx.user_id, job_id))
        if inter:
            inter.is_hidden = False
            inter.hide_reason = None
            inter.updated_at = utc_now()
            session.add(inter)
            session.commit()
        return {"job_id": job_id, "is_hidden": False}


@app.get("/internal/jobs/{job_id}/fit-context")
async def internal_job_fit_context(
    job_id: str,
    user_id: Optional[str] = Query(default=None),
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    with Session(engine) as session:
        job = session.get(JobDB, job_id)
        if not job and job_id.isdigit():
            job = session.exec(select(JobDB).where(JobDB.legacy_int_id == int(job_id))).first()
        if not job:
            raise NotFoundError("Job not found.")
        fit = (
            session.exec(
                select(JobFitScoreDB).where(JobFitScoreDB.user_id == user_id, JobFitScoreDB.job_id == job.id)
            ).first()
            if user_id
            else None
        )
        return _job_to_dict(job, fit=fit)
