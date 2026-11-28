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


class JobDB(SQLModel, table=True):
    __tablename__ = "jobs"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    legacy_int_id: Optional[int] = Field(default=None, index=True)
    source_id: str = Field(index=True, max_length=160)
    canonical_hash: str = Field(index=True, unique=True, max_length=64)
    title: str = Field(max_length=256)
    company_name: str = Field(max_length=200)
    location: str = Field(default="Cairo, Egypt", max_length=160)
    country: str = Field(default="Egypt", max_length=64)
    work_mode: str = Field(default="Hybrid", max_length=24)
    url: str = Field(default="")
    source_type: str = Field(default="linkedin", max_length=32)
    recruiter_email: Optional[str] = Field(default=None, max_length=320)
    raw_description: str = Field(default="")
    insights_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    parsed_skills_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    is_public_explore: bool = Field(default=False, index=True)
    is_active: bool = Field(default=True)
    posted_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class JobFitScoreDB(SQLModel, table=True):
    __tablename__ = "job_fit_scores"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_fit_user_job"),)

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    job_id: str = Field(foreign_key="jobs.id", index=True, max_length=64)
    best_persona_id: str = Field(default="default", max_length=64)
    overall_score: float = Field(default=0.0, index=True)
    match_level: str = Field(default="Moderate Fit", max_length=32)
    dimensions_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    persona_breakdown_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    tailoring_guidance_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    profile_version: int = Field(default=1)
    computed_at: datetime = Field(default_factory=utc_now)


class UserJobInteractionDB(SQLModel, table=True):
    __tablename__ = "user_job_interactions"

    user_id: str = Field(primary_key=True, max_length=64)
    job_id: str = Field(foreign_key="jobs.id", primary_key=True, max_length=64)
    in_interest_list: bool = Field(default=False, index=True)
    is_hidden: bool = Field(default=False, index=True)
    hide_reason: Optional[str] = Field(default=None, max_length=64)
    ingest_origin: str = Field(default="radar", max_length=32)
    screenshot_object_key: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=utc_now)


class ScrapeRunDB(SQLModel, table=True):
    __tablename__ = "scrape_runs"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: Optional[str] = Field(default=None, index=True, max_length=64)
    query_text: str = Field(default="")
    location: str = Field(default="")
    sources_json: str = Field(
        default='["linkedin","wuzzuf"]',
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    status: str = Field(default="queued", max_length=24)
    items_fetched: int = Field(default=0)
    items_deduped: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    finished_at: Optional[datetime] = Field(default=None)
