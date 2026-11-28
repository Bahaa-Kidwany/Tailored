from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class GeneratedDocumentDB(SQLModel, table=True):
    __tablename__ = "generated_documents"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    doc_id: str = Field(unique=True, index=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    profile_id: Optional[str] = Field(default=None, max_length=64)
    persona_id: str = Field(default="default", max_length=64)
    job_id: Optional[str] = Field(default=None, index=True, max_length=64)
    doc_type: str = Field(default="tailored_cv", index=True, max_length=24)  # tailored_cv | cover_letter
    status: str = Field(default="queued", max_length=24)  # queued | compiling | completed | failed
    compile_status: str = Field(default="pending", max_length=24)
    credit_hold_id: Optional[str] = Field(default=None, max_length=64)
    job_title: str = Field(default="", max_length=256)
    company_name: str = Field(default="", max_length=200)
    fit_score: float = Field(default=0.0)
    active_version_no: int = Field(default=1)
    base_latex_content: str = Field(default="")
    tailored_latex_content: str = Field(default="")
    content_markdown: str = Field(default="")
    subject_line: str = Field(default="", max_length=320)
    tex_object_key: Optional[str] = Field(default=None)
    pdf_object_key: Optional[str] = Field(default=None)
    pdf_sha256: Optional[str] = Field(default=None, max_length=64)
    section_plan_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    bullet_diffs_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    parsed_skills_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class DocumentVersionDB(SQLModel, table=True):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_no", name="uq_doc_ver_no"),)

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    document_id: str = Field(foreign_key="generated_documents.id", index=True, max_length=64)
    version_no: int
    source: str = Field(default="initial_tailor", max_length=32)
    proposal_card_id: Optional[str] = Field(default=None, max_length=64)
    content_text: str = Field(default="")
    pdf_object_key: Optional[str] = Field(default=None)
    diff_summary_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    created_at: datetime = Field(default_factory=utc_now)


class FrozenApplicationSnapshotDB(SQLModel, table=True):
    __tablename__ = "frozen_application_snapshots"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    pipeline_item_id: str = Field(index=True, max_length=64)
    cv_doc_id: Optional[str] = Field(default=None, max_length=64)
    cv_version_no: Optional[int] = Field(default=None)
    cl_doc_id: Optional[str] = Field(default=None, max_length=64)
    cl_version_no: Optional[int] = Field(default=None)
    frozen_cv_pdf_key: Optional[str] = Field(default=None)
    frozen_cv_tex_key: Optional[str] = Field(default=None)
    frozen_cl_pdf_key: Optional[str] = Field(default=None)
    frozen_at: datetime = Field(default_factory=utc_now)


class GdprExportJobDB(SQLModel, table=True):
    __tablename__ = "gdpr_export_jobs"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    status: str = Field(default="ready", max_length=24)
    zip_object_key: Optional[str] = Field(default=None)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)
