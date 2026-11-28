from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class MasterProfileDB(SQLModel, table=True):
    __tablename__ = "master_profiles"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, unique=True, max_length=64)
    full_name: str = Field(default="", max_length=200)
    primary_email: str = Field(default="", max_length=320)
    current_city: str = Field(default="Cairo", max_length=96)
    current_country: str = Field(default="Egypt", max_length=96)
    willing_to_relocate: bool = Field(default=True)
    links_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    custom_sections_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    active_persona_id: Optional[str] = Field(default=None, max_length=64)
    onboarding_step: int = Field(default=1)
    onboarding_completed: bool = Field(default=False)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ContactNumberDB(SQLModel, table=True):
    __tablename__ = "contact_numbers"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    country_code: str = Field(default="EG", max_length=8)
    dial_code: str = Field(default="+20", max_length=12)
    phone_number: str = Field(default="", max_length=32)
    is_primary: bool = Field(default=False)
    label: str = Field(default="Mobile", max_length=32)


class TargetLocationDB(SQLModel, table=True):
    __tablename__ = "target_locations"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    location_id: str = Field(default="loc_default", max_length=64)
    city: str = Field(default="Cairo", max_length=96)
    country: str = Field(default="Egypt", max_length=96)
    work_modes: str = Field(
        default='["Remote","Hybrid"]',
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    is_active_for_search: bool = Field(default=True)


class CareerPersonaDB(SQLModel, table=True):
    __tablename__ = "career_personas"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    persona_id: str = Field(index=True, max_length=64)
    target_title: str = Field(default="", max_length=200)
    alternative_titles: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    is_primary: bool = Field(default=True)
    seniority_level: str = Field(default="Mid-Level", max_length=32)
    years_of_experience: int = Field(default=0)
    summary_bio: str = Field(default="")
    skills_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    experience_highlights_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    featured_projects_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    certifications_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    updated_at: datetime = Field(default_factory=utc_now)


class EducationRecordDB(SQLModel, table=True):
    __tablename__ = "education_records"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    institution: str = Field(default="", max_length=200)
    degree: str = Field(default="", max_length=200)
    field_of_study: Optional[str] = Field(default=None, max_length=200)
    graduation_year: Optional[int] = Field(default=None)
    grade_or_gpa: Optional[str] = Field(default=None, max_length=32)


class SpokenLanguageDB(SQLModel, table=True):
    __tablename__ = "spoken_languages"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    language: str = Field(default="English", max_length=64)
    proficiency: str = Field(default="Professional", max_length=32)


class BaseCvTemplateDB(SQLModel, table=True):
    __tablename__ = "base_cv_templates"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    profile_id: str = Field(foreign_key="master_profiles.id", index=True, max_length=64)
    name: str = Field(default="Default ATS LaTeX Template", max_length=128)
    source_type: str = Field(default="synthesized", max_length=24)  # synthesized | uploaded_tex
    latex_content: str = Field(default="")
    sha256: str = Field(default="", max_length=64)
    is_default: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
