from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class PipelineItemDB(SQLModel, table=True):
    __tablename__ = "pipeline_items"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_pipeline_user_job"),)

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    job_id: str = Field(index=True, max_length=64)
    status: str = Field(default="saved", index=True, max_length=24)  # saved | in_process | applied | interview | archived
    channel_type: str = Field(default="external_portal", max_length=24)  # direct_email | external_portal
    recruiter_name: str = Field(default="", max_length=160)
    recruiter_email: Optional[str] = Field(default=None, max_length=320)
    job_title_snapshot: str = Field(default="", max_length=256)
    company_snapshot: str = Field(default="", max_length=200)
    job_url_snapshot: str = Field(default="")
    tailored_cv_doc_id: Optional[str] = Field(default=None, max_length=64)
    cover_letter_doc_id: Optional[str] = Field(default=None, max_length=64)
    frozen_snapshot_id: Optional[str] = Field(default=None, max_length=64)
    notes: str = Field(default="")
    compensation_notes: str = Field(default="")
    saved_at: datetime = Field(default_factory=utc_now)
    applied_at: Optional[datetime] = Field(default=None)
    follow_up_due_at: Optional[datetime] = Field(default=None, index=True)
    follow_up_sent_at: Optional[datetime] = Field(default=None)
    interview_date: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=utc_now)


class InterviewRoundNoteDB(SQLModel, table=True):
    __tablename__ = "interview_round_notes"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    pipeline_item_id: str = Field(foreign_key="pipeline_items.id", index=True, max_length=64)
    round_title: str = Field(max_length=160)
    scheduled_at: Optional[datetime] = Field(default=None)
    interviewer: str = Field(default="", max_length=160)
    notes: str = Field(default="")
    outcome: str = Field(default="pending", max_length=32)
    created_at: datetime = Field(default_factory=utc_now)


class OutreachDispatchDB(SQLModel, table=True):
    __tablename__ = "outreach_dispatches"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    pipeline_item_id: str = Field(foreign_key="pipeline_items.id", index=True, max_length=64)
    dispatch_channel: str = Field(default="gmail_web", max_length=24)  # gmail_web | mailto | external_marked
    to_email: Optional[str] = Field(default=None, max_length=320)
    subject: str = Field(default="", max_length=320)
    body_preview: str = Field(default="")
    dispatched_at: datetime = Field(default_factory=utc_now)
