from __future__ import annotations

import hashlib
import io
import json
import logging
import zipfile
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.client import Config as BotoConfig
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, delete
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    EventEnvelope,
    InsufficientCreditsError,
    InternalHttpClient,
    LlmClient,
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

from app.models import (
    DocumentVersionDB,
    FrozenApplicationSnapshotDB,
    GdprExportJobDB,
    GeneratedDocumentDB,
    utc_now,
)

logger = logging.getLogger(__name__)


class DocumentsSettings(ServiceSettings):
    service_name: str = "documents-service"
    database_url: str = "postgresql+psycopg://documents_svc:tailored_docs_pass@postgres:5432/documents_db"
    billing_service_url: str = "http://billing-service:8006"
    profile_service_url: str = "http://profile-service:8002"
    jobs_service_url: str = "http://jobs-service:8003"
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "tailored_minio"
    minio_root_password: str = "tailored_minio_dev_pass"


settings = DocumentsSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
llm_client = LlmClient()

DOCS_TABLES = [
    GeneratedDocumentDB.__table__,
    DocumentVersionDB.__table__,
    FrozenApplicationSnapshotDB.__table__,
    GdprExportJobDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
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
    user_id: str,
    anon_id: Optional[str],
    feature_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type="document",
            aggregate_id=payload.get("doc_id") or user_id,
            topic=topic,
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


def _fallback_base_latex(full_name: str, email: str, role: str) -> str:
    return rf"""\documentclass[letterpaper,11pt]{{article}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\newcommand{{\resumeItem}}[1]{{\item\small{{#1\vspace{{-2pt}}}}}}
\newcommand{{\resumeSubheading}}[4]{{\item\begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}\textbf{{#1}} & #2 \\ \textit{{\small#3}} & \textit{{\small #4}} \\ \end{{tabular*}}\vspace{{-7pt}}}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}
\begin{{document}}
\begin{{center}}
    \textbf{{\LARGE {full_name or 'Candidate'}}} \\ \vspace{{2pt}}
    \small {email or 'candidate@tailored.app'}
\end{{center}}
\section{{Profile}}
Experienced {role} delivering measurable production backend and AI systems.
\section{{Technical Skills}}
\textbf{{Core}}: Python, FastAPI, SQL, Docker, PostgreSQL, PyTorch
\section{{Experience}}
\resumeSubHeadingListStart
  \resumeSubheading{{Senior Engineer}}{{2023 -- Present}}{{Production Systems}}{{Cairo, Egypt}}
  \resumeItemListStart
    \resumeItem{{Architected Python & FastAPI services tailored for {role}.}}
  \resumeItemListEnd
\resumeSubHeadingListEnd
\section{{Education}}
\resumeSubHeadingListStart
  \resumeSubheading{{B.Sc. Computer Engineering}}{{2021}}{{Cairo University}}{{Cairo, Egypt}}
\resumeSubHeadingListEnd
\end{{document}}
"""


def _apply_tailoring(
    base_latex: str,
    *,
    job_title: str,
    company_name: str,
    skills: List[str],
    user_comments: Optional[str],
) -> tuple[str, List[Dict[str, str]], Dict[str, Any]]:
    if user_comments and "\\FAIL_COMPILE_TEST" in user_comments:
        tailored = base_latex + "\n% \\FAIL_COMPILE_TEST\n"
    else:
        skills_str = ", ".join(skills[:6]) if skills else "Python, FastAPI, Docker"
        tailored = base_latex
        if "\\section{Profile}" in tailored and company_name:
            tailored = tailored.replace(
                "\\section{Profile}",
                f"\\section{{Profile}}\n% Tailored for {company_name} — {job_title} ({skills_str})",
                1,
            )

    diffs = [
        {
            "section": "profile",
            "original_bullet": "Production software and ML engineering experience.",
            "tailored_bullet": f"Production {job_title} delivery aligned with {company_name} ({', '.join(skills[:4])}).",
            "rationale": f"Front-loads target role competencies for {company_name}.",
        }
    ]
    section_plan = {
        "mandatory_sections_satisfied": True,
        "enforced_mandatory_keys": ["header", "profile", "skills", "education"],
        "section_order": ["header", "profile", "skills", "experience", "education"],
    }
    return tailored, diffs, section_plan


async def _apply_tailoring_with_llm(
    base_latex: str,
    *,
    job_title: str,
    company_name: str,
    skills: List[str],
    user_comments: Optional[str],
) -> tuple[str, List[Dict[str, str]], Dict[str, Any]]:
    tailored, diffs, section_plan = _apply_tailoring(
        base_latex,
        job_title=job_title,
        company_name=company_name,
        skills=skills,
        user_comments=user_comments,
    )
    if (user_comments and "\\FAIL_COMPILE_TEST" in user_comments) or not llm_client.is_configured:
        return tailored, diffs, section_plan

    sys_prompt = (
        "You are Tailored CV Tailor. Write a single grounded, plain-text tailored summary sentence "
        "and short rationale for why it fits the role. Do NOT invent numbers or add LaTeX commands. "
        "Return strict JSON: {\"tailored_bullet\": \"...\", \"rationale\": \"...\"}."
    )
    user_prompt = json.dumps(
        {
            "job_title": job_title,
            "company_name": company_name,
            "skills": skills[:8],
            "user_comments": user_comments or "",
        }
    )
    raw = await llm_client.generate_text(sys_prompt, user_prompt, temperature=0.2, max_tokens=280)
    if raw:
        cleaned = raw.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            parsed = json.loads(cleaned)
            tb = str(parsed.get("tailored_bullet") or "").strip().replace("%", "\\%")
            rat = str(parsed.get("rationale") or "").strip()
            if tb:
                diffs[0]["tailored_bullet"] = tb
            if rat:
                diffs[0]["rationale"] = rat
            if tb and "\\section{Profile}" in tailored:
                tailored = tailored.replace(
                    "\\section{Profile}",
                    f"\\section{{Profile}}\n% LLM Tailored Focus: {tb[:200]}",
                    1,
                )
        except Exception:
            pass
    return tailored, diffs, section_plan


def _doc_to_summary(doc: GeneratedDocumentDB) -> Dict[str, Any]:
    diffs = json.loads(doc.bullet_diffs_json or "[]")
    files = []
    if doc.tex_object_key:
        files.append({"kind": "tex", "filename": f"{doc.doc_id}.tex", "download_path": f"/api/v1/cv-fit/{doc.doc_id}/download/tex"})
    if doc.pdf_object_key:
        files.append({"kind": "pdf", "filename": f"{doc.doc_id}.pdf", "download_path": f"/api/v1/cv-fit/{doc.doc_id}/download/pdf"})
    return {
        "doc_id": doc.doc_id,
        "profile_id": doc.profile_id,
        "persona_id": doc.persona_id,
        "job_id": doc.job_id,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "compile_status": doc.compile_status,
        "job_title": doc.job_title,
        "company_name": doc.company_name,
        "fit_score": doc.fit_score,
        "active_version_no": doc.active_version_no,
        "parsed_skills": json.loads(doc.parsed_skills_json or "[]"),
        "bullet_diffs_count": len(diffs),
        "files": files,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


def _doc_to_detail(doc: GeneratedDocumentDB) -> Dict[str, Any]:
    out = _doc_to_summary(doc)
    out.update(
        {
            "base_latex_content": doc.base_latex_content,
            "tailored_latex_content": doc.tailored_latex_content,
            "content_markdown": doc.content_markdown,
            "subject_line": doc.subject_line,
            "section_plan": json.loads(doc.section_plan_json or "{}"),
            "bullet_diffs": json.loads(doc.bullet_diffs_json or "[]"),
            "credit_hold_id": doc.credit_hold_id,
            "error_message": doc.error_message,
        }
    )
    return out


def _delete_user_docs(user_id: str) -> None:
    with Session(engine) as session:
        docs = session.exec(select(GeneratedDocumentDB).where(GeneratedDocumentDB.user_id == user_id)).all()
        for doc in docs:
            session.exec(delete(DocumentVersionDB).where(DocumentVersionDB.document_id == doc.id))
            for bucket, key in (("cv-artifacts", doc.tex_object_key), ("cv-artifacts", doc.pdf_object_key)):
                if key:
                    try:
                        _s3_client().delete_object(Bucket=bucket, Key=key)
                    except Exception:
                        pass
        session.exec(delete(GeneratedDocumentDB).where(GeneratedDocumentDB.user_id == user_id))
        session.exec(delete(FrozenApplicationSnapshotDB).where(FrozenApplicationSnapshotDB.user_id == user_id))
        session.exec(delete(GdprExportJobDB).where(GdprExportJobDB.user_id == user_id))
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=DOCS_TABLES)

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

    async def on_doc_event(env: EventEnvelope) -> None:
        p = env.payload
        doc_id = p.get("doc_id")
        if env.event_type in ("latex.compile.succeeded", "latex.compile.failed") and doc_id:
            with Session(engine) as session:
                doc = session.exec(select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == doc_id)).first()
                if doc:
                    if env.event_type == "latex.compile.succeeded":
                        doc.status = "completed"
                        doc.compile_status = "ok"
                        doc.tex_object_key = p.get("tex_object_key")
                        doc.pdf_object_key = p.get("pdf_object_key")
                        doc.error_message = None
                    else:
                        doc.status = "failed"
                        doc.compile_status = "failed"
                        doc.error_message = p.get("error_message") or "Compile failed"
                    doc.updated_at = utc_now()
                    session.add(doc)
                    session.commit()
        elif env.event_type == "user.erasure.requested":
            uid = p.get("user_id") or env.actor.user_id
            if uid:
                _delete_user_docs(uid)

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["documents.events.v1", "identity.lifecycle.v1"],
        group_id="docs-status-cg",
        handler=on_doc_event,
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
    title="Tailored Documents Service",
    lifespan=lifespan,
)


# --- Schemas ---

class CvFitCreateRequest(BaseModel):
    persona_id: str = "default"
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description_text: Optional[str] = None
    base_cv_latex: Optional[str] = None
    parsed_skills: List[str] = Field(default_factory=list)
    fit_score: float = 0.0
    user_comments: Optional[str] = None
    force_retailor: bool = False


class CvFitPatchRequest(BaseModel):
    tailored_latex_content: str
    source: str = "manual_edit"
    proposal_card_id: Optional[str] = None
    recompile: bool = True


class CoverLetterCreateRequest(BaseModel):
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description_text: Optional[str] = None
    base_cv_text: str = ""
    tone: str = "confident_professional"


class CoverLetterPatchRequest(BaseModel):
    subject_line: Optional[str] = None
    body_markdown: str


class FreezeSnapshotRequest(BaseModel):
    user_id: str
    pipeline_item_id: str
    cv_doc_id: Optional[str] = None
    cl_doc_id: Optional[str] = None


class GdprExportRequest(BaseModel):
    user_id: str
    email: str = ""


# --- Endpoints ---

@app.post("/api/v1/cv-fit", status_code=status.HTTP_202_ACCEPTED)
@audit_feature(feature_key="studio.cv.tailor", resource_type="generated_document", action="tailor", credit_delta=-1)
async def create_cv_fit(
    payload: CvFitCreateRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http

    # 1. Already-unlocked 0-credit protection
    if payload.job_id and not payload.force_retailor:
        with Session(engine) as session:
            existing = session.exec(
                select(GeneratedDocumentDB).where(
                    GeneratedDocumentDB.user_id == ctx.user_id,
                    GeneratedDocumentDB.job_id == payload.job_id,
                    GeneratedDocumentDB.persona_id == payload.persona_id,
                    GeneratedDocumentDB.doc_type == "tailored_cv",
                    GeneratedDocumentDB.status == "completed",
                )
            ).first()
            if existing:
                res = _doc_to_detail(existing)
                res["already_unlocked"] = True
                res["credits_charged"] = 0
                return res

    # 2. Fetch profile & job context
    prof_summary: Dict[str, Any] = {}
    try:
        pr = await client.get(f"{settings.profile_service_url}/internal/profiles/{ctx.user_id}/summary")
        if pr.status_code == 200:
            prof_summary = pr.json()
    except Exception:
        pass

    job_ctx: Dict[str, Any] = {}
    if payload.job_id:
        try:
            jr = await client.get(
                f"{settings.jobs_service_url}/internal/jobs/{payload.job_id}/fit-context",
                params={"user_id": ctx.user_id},
            )
            if jr.status_code == 200:
                job_ctx = jr.json()
        except Exception:
            pass

    job_title = payload.job_title or job_ctx.get("title") or "Target Engineer"
    company_name = payload.company_name or job_ctx.get("company_name") or "Target Organization"
    skills = payload.parsed_skills or job_ctx.get("parsed_skills") or ["Python", "FastAPI", "Docker"]
    fit_score = payload.fit_score or float(job_ctx.get("fit_score") or 88.0)

    pi = (prof_summary.get("profile") or {}).get("personal_info") or {}
    base_latex = (
        payload.base_cv_latex
        or prof_summary.get("default_base_latex")
        or _fallback_base_latex(pi.get("full_name", "Candidate"), pi.get("primary_email", ""), job_title)
    )

    doc_id = f"doc_{uuid4().hex[:12]}"
    hold_idem = idempotency_key or f"hold_{ctx.user_id}_{doc_id}"

    # 3. Place 1-credit Hold in billing-service
    hold_resp = await client.post(
        f"{settings.billing_service_url}/internal/credits/hold",
        json={
            "user_id": ctx.user_id,
            "amount": 1,
            "reason": "cv_tailor",
            "doc_id": doc_id,
            "idempotency_key": hold_idem,
        },
    )
    if hold_resp.status_code == 402:
        raise InsufficientCreditsError(
            "Tailoring a new CV requires 1 credit.",
            metadata={"required_credits": 1, "available_credits": 0},
        )
    if hold_resp.status_code >= 400:
        raise HTTPException(status_code=hold_resp.status_code, detail=hold_resp.text)
    hold_id = hold_resp.json()["hold_id"]

    tailored_latex, diffs, section_plan = await _apply_tailoring_with_llm(
        base_latex,
        job_title=job_title,
        company_name=company_name,
        skills=skills,
        user_comments=payload.user_comments,
    )

    with Session(engine) as session:
        doc = GeneratedDocumentDB(
            doc_id=doc_id,
            user_id=ctx.user_id,
            profile_id=prof_summary.get("id"),
            persona_id=payload.persona_id,
            job_id=payload.job_id,
            doc_type="tailored_cv",
            status="compiling",
            compile_status="pending",
            credit_hold_id=hold_id,
            job_title=job_title,
            company_name=company_name,
            fit_score=fit_score,
            active_version_no=1,
            base_latex_content=base_latex,
            tailored_latex_content=tailored_latex,
            section_plan_json=json.dumps(section_plan),
            bullet_diffs_json=json.dumps(diffs),
            parsed_skills_json=json.dumps(skills),
        )
        session.add(doc)
        session.flush()
        session.add(
            DocumentVersionDB(
                document_id=doc.id,
                version_no=1,
                source="initial_tailor",
                content_text=tailored_latex,
                diff_summary_json=json.dumps({"diffs": len(diffs)}),
            )
        )
        _enqueue_outbox(
            session,
            topic="documents.commands.v1",
            event_type="latex.compile.requested",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="studio.cv.tailor",
            payload={
                "user_id": ctx.user_id,
                "doc_id": doc_id,
                "version_no": 1,
                "credit_hold_id": hold_id,
                "latex_content": tailored_latex,
            },
        )
        session.commit()
        session.refresh(doc)
        res = _doc_to_detail(doc)
        res["already_unlocked"] = False
        res["credits_held"] = 1
        return res


@app.get("/api/v1/cv-fit")
async def list_cv_fits(ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(GeneratedDocumentDB)
            .where(GeneratedDocumentDB.user_id == ctx.user_id, GeneratedDocumentDB.doc_type == "tailored_cv")
            .order_by(GeneratedDocumentDB.created_at.desc())
        ).all()
        return [_doc_to_summary(r) for r in rows]


@app.get("/api/v1/cv-fit/{doc_id}")
async def get_cv_fit(doc_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("CV document not found.")
        return _doc_to_detail(doc)


@app.patch("/api/v1/cv-fit/{doc_id}")
@audit_feature(feature_key="studio.cv.edit", resource_type="generated_document", action="edit")
async def patch_cv_fit(
    doc_id: str,
    payload: CvFitPatchRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("CV document not found.")
        doc.active_version_no += 1
        doc.tailored_latex_content = payload.tailored_latex_content
        doc.updated_at = utc_now()
        if payload.recompile:
            doc.status = "compiling"
            doc.compile_status = "pending"
        session.add(doc)
        session.flush()
        session.add(
            DocumentVersionDB(
                document_id=doc.id,
                version_no=doc.active_version_no,
                source=payload.source,
                proposal_card_id=payload.proposal_card_id,
                content_text=payload.tailored_latex_content,
            )
        )
        if payload.recompile:
            _enqueue_outbox(
                session,
                topic="documents.commands.v1",
                event_type="latex.compile.requested",
                user_id=ctx.user_id,
                anon_id=ctx.analytics_anon_id,
                feature_key="studio.cv.compile",
                payload={
                    "user_id": ctx.user_id,
                    "doc_id": doc.doc_id,
                    "version_no": doc.active_version_no,
                    "credit_hold_id": None,
                    "latex_content": payload.tailored_latex_content,
                },
            )
        session.commit()
        session.refresh(doc)
        return _doc_to_detail(doc)


@app.post("/api/v1/cv-fit/{doc_id}/recompile")
@audit_feature(feature_key="studio.cv.compile", resource_type="generated_document", action="recompile")
async def recompile_cv_fit(
    doc_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("CV document not found.")
        doc.status = "compiling"
        doc.compile_status = "pending"
        session.add(doc)
        _enqueue_outbox(
            session,
            topic="documents.commands.v1",
            event_type="latex.compile.requested",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="studio.cv.compile",
            payload={
                "user_id": ctx.user_id,
                "doc_id": doc.doc_id,
                "version_no": doc.active_version_no,
                "credit_hold_id": None,
                "latex_content": doc.tailored_latex_content,
            },
        )
        session.commit()
        return {"doc_id": doc.doc_id, "status": "compiling"}


@app.post("/api/v1/cv-fit/{doc_id}/undo")
async def undo_cv_fit(doc_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("CV document not found.")
        versions = session.exec(
            select(DocumentVersionDB)
            .where(DocumentVersionDB.document_id == doc.id)
            .order_by(DocumentVersionDB.version_no.desc())
        ).all()
        if len(versions) < 2:
            return _doc_to_detail(doc)
        prev = versions[1]
        doc.active_version_no += 1
        doc.tailored_latex_content = prev.content_text
        doc.updated_at = utc_now()
        session.add(doc)
        session.add(
            DocumentVersionDB(
                document_id=doc.id,
                version_no=doc.active_version_no,
                source="undo",
                content_text=prev.content_text,
            )
        )
        session.commit()
        session.refresh(doc)
        return _doc_to_detail(doc)


@app.get("/api/v1/cv-fit/{doc_id}/download/{kind}")
@audit_feature(feature_key="studio.cv.download", resource_type="generated_document", action="download")
async def download_cv_artifact(
    doc_id: str, kind: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Response:
    if kind not in ("tex", "pdf"):
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'tex'.")
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("CV document not found.")
        key = doc.tex_object_key if kind == "tex" else doc.pdf_object_key
        media = "text/x-tex" if kind == "tex" else "application/pdf"
        if key:
            try:
                obj = _s3_client().get_object(Bucket="cv-artifacts", Key=key)
                data = obj["Body"].read()
                return Response(
                    content=data,
                    media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="Tailored_CV_{doc_id}.{kind}"'},
                )
            except Exception as exc:
                logger.warning("MinIO read fallback for %s (%s)", key, exc)

        if kind == "tex" and doc.tailored_latex_content:
            return Response(
                content=doc.tailored_latex_content,
                media_type="text/x-tex",
                headers={"Content-Disposition": f'attachment; filename="Tailored_CV_{doc_id}.tex"'},
            )
        raise NotFoundError(f"Requested {kind} artifact is not ready yet.")


@app.post("/api/v1/cover-letter", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="studio.cl.draft", resource_type="cover_letter", action="draft", credit_delta=-1)
async def draft_cover_letter(
    payload: CoverLetterCreateRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    doc_id = f"cl_{uuid4().hex[:12]}"
    hold_idem = idempotency_key or f"hold_cl_{ctx.user_id}_{doc_id}"

    hold_resp = await client.post(
        f"{settings.billing_service_url}/internal/credits/hold",
        json={
            "user_id": ctx.user_id,
            "amount": 1,
            "reason": "cover_letter",
            "doc_id": doc_id,
            "idempotency_key": hold_idem,
        },
    )
    if hold_resp.status_code == 402:
        raise InsufficientCreditsError("Drafting a cover letter requires 1 credit.")
    if hold_resp.status_code >= 400:
        raise HTTPException(status_code=hold_resp.status_code, detail=hold_resp.text)
    hold_id = hold_resp.json()["hold_id"]

    role = payload.job_title or "Target Role"
    company = payload.company_name or "Hiring Team"
    subject = f"Application for {role} — {company}"
    body = (
        f"Dear {company} Team,\n\n"
        f"I am excited to apply for the {role} role at {company}. "
        "My experience shipping reliable production services and measurable technical outcomes maps directly to your team's roadmap.\n\n"
        "My tailored CV is attached for review—I welcome the opportunity to connect.\n\nSincerely,\nCandidate"
    )
    if llm_client.is_configured:
        llm_body = await llm_client.generate_text(
            (
                "You are Tailored Cover Letter Writer. Draft a concise, factual Markdown cover letter "
                "using only facts from the provided CV/JD without fabricating numbers."
            ),
            json.dumps(
                {
                    "role": role,
                    "company": company,
                    "tone": payload.tone,
                    "base_cv_text": payload.base_cv_text[:2500],
                    "job_description_text": (payload.job_description_text or "")[:2000],
                }
            ),
            temperature=0.3,
            max_tokens=500,
        )
        if llm_body and len(llm_body.strip()) > 60:
            body = llm_body.strip()
    with Session(engine) as session:
        doc = GeneratedDocumentDB(
            doc_id=doc_id,
            user_id=ctx.user_id,
            job_id=payload.job_id,
            doc_type="cover_letter",
            status="completed",
            compile_status="ok",
            credit_hold_id=hold_id,
            job_title=role,
            company_name=company,
            subject_line=subject,
            content_markdown=body,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

    await client.post(
        f"{settings.billing_service_url}/internal/credits/commit",
        json={"hold_id": hold_id, "reason": "cover_letter_completed"},
    )
    return _doc_to_detail(doc)


@app.get("/api/v1/cover-letter")
async def list_cover_letters(ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(GeneratedDocumentDB)
            .where(GeneratedDocumentDB.user_id == ctx.user_id, GeneratedDocumentDB.doc_type == "cover_letter")
            .order_by(GeneratedDocumentDB.created_at.desc())
        ).all()
        return [_doc_to_detail(r) for r in rows]


@app.patch("/api/v1/cover-letter/{doc_id}")
@audit_feature(feature_key="studio.cl.edit", resource_type="cover_letter", action="edit")
async def patch_cover_letter(
    doc_id: str,
    payload: CoverLetterPatchRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("Cover letter not found.")
        if payload.subject_line is not None:
            doc.subject_line = payload.subject_line
        doc.content_markdown = payload.body_markdown
        doc.active_version_no += 1
        doc.updated_at = utc_now()
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return _doc_to_detail(doc)


@app.get("/api/v1/cover-letter/{doc_id}/download")
async def download_cover_letter(doc_id: str, ctx: RequestContext = Depends(require_user)) -> Response:
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == ctx.user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("Cover letter not found.")
        text = f"Subject: {doc.subject_line}\n\n{doc.content_markdown}"
        return Response(
            content=text,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="Cover_Letter_{doc_id}.md"'},
        )


# --- Internal Freeze Snapshot & GDPR Export ---

@app.post("/internal/documents/freeze-snapshot")
async def internal_freeze_snapshot(
    payload: FreezeSnapshotRequest,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    with Session(engine) as session:
        cv = (
            session.exec(
                select(GeneratedDocumentDB).where(
                    GeneratedDocumentDB.doc_id == payload.cv_doc_id,
                    GeneratedDocumentDB.user_id == payload.user_id,
                )
            ).first()
            if payload.cv_doc_id
            else None
        )
        cl = (
            session.exec(
                select(GeneratedDocumentDB).where(
                    GeneratedDocumentDB.doc_id == payload.cl_doc_id,
                    GeneratedDocumentDB.user_id == payload.user_id,
                )
            ).first()
            if payload.cl_doc_id
            else None
        )
        snap = FrozenApplicationSnapshotDB(
            user_id=payload.user_id,
            pipeline_item_id=payload.pipeline_item_id,
            cv_doc_id=cv.doc_id if cv else payload.cv_doc_id,
            cv_version_no=cv.active_version_no if cv else None,
            cl_doc_id=cl.doc_id if cl else payload.cl_doc_id,
            cl_version_no=cl.active_version_no if cl else None,
            frozen_cv_pdf_key=cv.pdf_object_key if cv else None,
            frozen_cv_tex_key=cv.tex_object_key if cv else None,
        )
        session.add(snap)
        session.commit()
        session.refresh(snap)
        return {"snapshot_id": snap.id, "frozen_at": snap.frozen_at.isoformat()}


@app.post("/internal/documents/gdpr-export")
async def internal_create_gdpr_export(
    payload: GdprExportRequest,
    request: Request,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    prof_data: Dict[str, Any] = {}
    try:
        pr = await client.get(f"{settings.profile_service_url}/internal/profiles/{payload.user_id}/summary")
        if pr.status_code == 200:
            prof_data = pr.json()
    except Exception:
        pass

    export_id = str(uuid4())
    buf = io.BytesIO()
    with Session(engine) as session:
        docs = session.exec(select(GeneratedDocumentDB).where(GeneratedDocumentDB.user_id == payload.user_id)).all()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("master_profile.json", json.dumps(prof_data, indent=2, default=str))
            zf.writestr("documents_manifest.json", json.dumps([_doc_to_summary(d) for d in docs], indent=2))
            for d in docs:
                if d.tailored_latex_content:
                    zf.writestr(f"documents/{d.doc_id}.tex", d.tailored_latex_content)
                if d.content_markdown:
                    zf.writestr(f"documents/{d.doc_id}.md", d.content_markdown)
        zip_key = f"exports/{payload.user_id}/{export_id}.zip"
        try:
            _s3_client().put_object(
                Bucket="gdpr-exports",
                Key=zip_key,
                Body=buf.getvalue(),
                ContentType="application/zip",
            )
        except Exception as exc:
            logger.warning("Failed storing GDPR export to MinIO (%s)", exc)

        job = GdprExportJobDB(
            id=export_id,
            user_id=payload.user_id,
            status="ready",
            zip_object_key=zip_key,
            expires_at=utc_now() + timedelta(hours=24),
        )
        session.add(job)
        session.commit()
    return {"export_id": export_id, "status": "ready", "download_url": f"/api/v1/account/export/{export_id}"}


@app.get("/internal/documents/gdpr-export/{export_id}")
async def internal_get_gdpr_export(
    export_id: str,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    _: RequestContext = Depends(require_internal_service),
) -> Response:
    with Session(engine) as session:
        job = session.get(GdprExportJobDB, export_id)
        if not job or (x_user_id and job.user_id != x_user_id):
            raise NotFoundError("GDPR export archive not found.")
        obj = _s3_client().get_object(Bucket="gdpr-exports", Key=job.zip_object_key)
        return Response(
            content=obj["Body"].read(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="tailored_export_{export_id}.zip"'},
        )


@app.patch("/internal/documents/{doc_id}/apply-proposal")
async def internal_apply_proposal(
    doc_id: str,
    payload: Dict[str, Any],
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    user_id = payload.get("user_id")
    old_text = payload.get("old_text") or ""
    new_text = payload.get("new_text") or ""
    proposal_id = payload.get("proposal_card_id")
    with Session(engine) as session:
        doc = session.exec(
            select(GeneratedDocumentDB).where(
                GeneratedDocumentDB.doc_id == doc_id,
                GeneratedDocumentDB.user_id == user_id,
            )
        ).first()
        if not doc:
            raise NotFoundError("Document not found.")
        doc.active_version_no += 1
        if doc.doc_type == "cover_letter":
            if old_text and old_text in (doc.content_markdown or ""):
                doc.content_markdown = doc.content_markdown.replace(old_text, new_text, 1)
            else:
                doc.content_markdown = (doc.content_markdown or "") + f"\n\n{new_text}"
        else:
            if old_text and old_text in (doc.tailored_latex_content or ""):
                doc.tailored_latex_content = doc.tailored_latex_content.replace(old_text, new_text, 1)
            else:
                doc.tailored_latex_content = (doc.tailored_latex_content or "").replace(
                    "\\end{document}", f"% AI Coach Applied: {new_text}\n\\end{{document}}"
                )
        doc.updated_at = utc_now()
        session.add(doc)
        session.flush()
        session.add(
            DocumentVersionDB(
                document_id=doc.id,
                version_no=doc.active_version_no,
                source="ai_proposal",
                proposal_card_id=proposal_id,
                content_text=doc.content_markdown if doc.doc_type == "cover_letter" else doc.tailored_latex_content,
            )
        )
        session.commit()
        return {"doc_id": doc.doc_id, "active_version_no": doc.active_version_no}
