from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field as DBField


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineItemDB(SQLModel, table=True):
    """
    Persisted Application Pipeline item tracking candidate job opportunities
    through the application lifecycle (saved -> in_process -> applied -> interview -> archived).
    """
    __tablename__ = "pipeline_items"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: Optional[int] = DBField(default=None, foreign_key="user_profiles.id", index=True)
    job_id: int = DBField(foreign_key="jobs.id", index=True)
    status: str = DBField(default="saved", index=True)  # 'saved', 'in_process', 'applied', 'interview', 'archived'
    recruiter_email: Optional[str] = DBField(default=None)
    notes: Optional[str] = DBField(default=None)
    tailored_cv_doc_id: Optional[str] = DBField(default=None, index=True)
    cover_letter_doc_id: Optional[str] = DBField(default=None, index=True)
    saved_at: datetime = DBField(default_factory=utc_now)
    applied_at: Optional[datetime] = DBField(default=None)
    created_at: datetime = DBField(default_factory=utc_now)
    updated_at: datetime = DBField(default_factory=utc_now)


# --- Request & Response Schemas ---

class PipelineItemCreate(BaseModel):
    job_id: int
    profile_id: Optional[int] = None
    status: Optional[str] = None
    recruiter_email: Optional[str] = None
    notes: Optional[str] = None


class PipelineItemUpdate(BaseModel):
    status: Optional[str] = None
    recruiter_email: Optional[str] = None
    notes: Optional[str] = None
    tailored_cv_doc_id: Optional[str] = None
    cover_letter_doc_id: Optional[str] = None
    applied_at: Optional[datetime] = None


class PipelineItemResponse(BaseModel):
    id: int
    profile_id: Optional[int] = None
    job_id: int
    status: str
    recruiter_email: Optional[str] = None
    notes: Optional[str] = None
    tailored_cv_doc_id: Optional[str] = None
    cover_letter_doc_id: Optional[str] = None
    saved_at: str
    applied_at: Optional[str] = None
    created_at: str
    updated_at: str
    job: Optional[Dict[str, Any]] = None
    tailored_cv: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None


class PipelineMetricsResponse(BaseModel):
    total: int = 0
    in_process: int = 0
    applied: int = 0
    interview: int = 0
    saved: int = 0
    archived: int = 0
    with_email: int = 0


class OutreachPackageResponse(BaseModel):
    item_id: int
    job_title: str
    company_name: str
    to_email: str
    subject: str
    body_markdown: str
    gmail_web_url: str
    mailto_url: str
    cv_pdf_download_url: Optional[str] = None
    cover_letter_download_url: Optional[str] = None
    candidate_name: str
    candidate_email: str
    candidate_phone: str


class PipelineBatchImportItem(BaseModel):
    job_id: Optional[int] = None
    job_source_id: Optional[str] = None
    job_url: Optional[str] = None
    status: Optional[str] = "saved"
    recruiter_email: Optional[str] = None
    notes: Optional[str] = None
    tailored_cv_doc_id: Optional[str] = None
    cover_letter_doc_id: Optional[str] = None
    saved_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    job: Optional[Dict[str, Any]] = None


class PipelineBatchImportRequest(BaseModel):
    profile_id: Optional[int] = None
    items: List[PipelineBatchImportItem] = PydanticField(default_factory=list)
