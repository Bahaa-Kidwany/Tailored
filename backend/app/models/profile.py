import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field as DBField, select, Session
from app.schemas.user_profile import (
    UserProfile,
    PersonalInfo,
    ContactNumber,
    TargetLocation,
    ResidenceAndMobility,
    Education,
    LanguageProficiency,
    CareerPersona,
    SkillsAndTools,
    ExperienceHighlight,
    FeaturedProject,
    Certification,
    CustomSection,
    CustomSectionItem,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class UserProfileDB(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: Optional[int] = DBField(default=None, primary_key=True)
    full_name: str = DBField(index=True)
    primary_email: str = DBField(index=True)
    current_city: str = DBField(default="Cairo")
    current_country: str = DBField(default="Egypt")
    willing_to_relocate: bool = DBField(default=True)
    links_json: str = DBField(default="{}")
    custom_sections_json: str = DBField(default="[]")
    created_at: datetime = DBField(default_factory=utc_now)
    updated_at: datetime = DBField(default_factory=utc_now)

    def get_links(self) -> Dict[str, str]:
        try:
            return json.loads(self.links_json) if self.links_json else {}
        except Exception:
            return {}

    def get_custom_sections(self) -> List[CustomSection]:
        try:
            items = json.loads(self.custom_sections_json) if self.custom_sections_json else []
            return [CustomSection(**item) for item in items]
        except Exception:
            return []

class ContactNumberDB(SQLModel, table=True):
    __tablename__ = "contact_numbers"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    country_code: str = DBField(default="EG")
    dial_code: str = DBField(default="+20")
    phone_number: str
    is_primary: bool = DBField(default=False)
    label: str = DBField(default="Mobile")

class TargetLocationDB(SQLModel, table=True):
    __tablename__ = "target_locations"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    location_id: str = DBField(default="loc_default")
    city: str
    country: str
    work_modes_json: str = DBField(default='["Remote", "Hybrid"]')
    is_active_for_search: bool = DBField(default=True)

    def get_work_modes(self) -> List[str]:
        try:
            return json.loads(self.work_modes_json) if self.work_modes_json else ["Remote", "Hybrid"]
        except Exception:
            return ["Remote", "Hybrid"]

class CareerPersonaDB(SQLModel, table=True):
    __tablename__ = "career_personas"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    persona_id: str = DBField(index=True)
    target_title: str
    alternative_titles_json: str = DBField(default="[]")
    is_primary: bool = DBField(default=True)
    seniority_level: str = DBField(default="Mid-Level")
    years_of_experience: int = DBField(default=0)
    summary_bio: str = DBField(default="")
    skills_json: str = DBField(default="{}")
    experience_highlights_json: str = DBField(default="[]")
    featured_projects_json: str = DBField(default="[]")
    certifications_json: str = DBField(default="[]")

    def get_alternative_titles(self) -> List[str]:
        try:
            return json.loads(self.alternative_titles_json) if self.alternative_titles_json else []
        except Exception:
            return []

    def get_skills_and_tools(self) -> SkillsAndTools:
        try:
            data = json.loads(self.skills_json) if self.skills_json else {}
            return SkillsAndTools(**data)
        except Exception:
            return SkillsAndTools()

    def get_experience_highlights(self) -> List[ExperienceHighlight]:
        try:
            items = json.loads(self.experience_highlights_json) if self.experience_highlights_json else []
            return [ExperienceHighlight(**item) for item in items]
        except Exception:
            return []

    def get_featured_projects(self) -> List[FeaturedProject]:
        try:
            items = json.loads(self.featured_projects_json) if self.featured_projects_json else []
            return [FeaturedProject(**item) for item in items]
        except Exception:
            return []

    def get_certifications(self) -> List[Certification]:
        try:
            items = json.loads(self.certifications_json) if self.certifications_json else []
            return [Certification(**item) for item in items]
        except Exception:
            return []

class EducationDB(SQLModel, table=True):
    __tablename__ = "education_records"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    grade_or_gpa: Optional[str] = None

class LanguageDB(SQLModel, table=True):
    __tablename__ = "spoken_languages"

    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    language: str
    proficiency: str = DBField(default="Professional")


def assemble_user_profile_schema(
    profile_db: UserProfileDB,
    contacts: List[ContactNumberDB],
    locations: List[TargetLocationDB],
    personas: List[CareerPersonaDB],
    education: List[EducationDB],
    languages: List[LanguageDB],
) -> UserProfile:
    """Reconstructs the full Pydantic UserProfile object from SQLModel DB rows."""
    contact_models = [
        ContactNumber(
            country_code=c.country_code,
            dial_code=c.dial_code,
            phone_number=c.phone_number,
            is_primary=c.is_primary,
            label=c.label,
        )
        for c in contacts
    ]

    location_models = [
        TargetLocation(
            location_id=l.location_id,
            city=l.city,
            country=l.country,
            work_modes=l.get_work_modes(),
            is_active_for_search=l.is_active_for_search,
        )
        for l in locations
    ]

    persona_models = [
        CareerPersona(
            persona_id=p.persona_id,
            target_title=p.target_title,
            alternative_titles=p.get_alternative_titles(),
            is_primary=p.is_primary,
            seniority_level=p.seniority_level,
            years_of_experience=p.years_of_experience,
            summary_bio=p.summary_bio,
            skills_and_tools=p.get_skills_and_tools(),
            experience_highlights=p.get_experience_highlights(),
            featured_projects=p.get_featured_projects(),
            certifications=p.get_certifications(),
        )
        for p in personas
    ]

    education_models = [
        Education(
            institution=e.institution,
            degree=e.degree,
            field_of_study=e.field_of_study,
            graduation_year=e.graduation_year,
            grade_or_gpa=e.grade_or_gpa,
        )
        for e in education
    ]

    language_models = [
        LanguageProficiency(
            language=lang.language,
            proficiency=lang.proficiency,
        )
        for lang in languages
    ]

    return UserProfile(
        version="1.1.0",
        personal_info=PersonalInfo(
            full_name=profile_db.full_name,
            primary_email=profile_db.primary_email,
            contact_numbers=contact_models,
            links=profile_db.get_links(),
        ),
        residence_and_mobility=ResidenceAndMobility(
            current_residence={
                "city": profile_db.current_city,
                "country": profile_db.current_country,
            },
            willing_to_relocate=profile_db.willing_to_relocate,
            target_locations=location_models,
        ),
        education=education_models,
        languages=language_models,
        career_personas=persona_models,
        custom_sections=profile_db.get_custom_sections(),
    )


def load_assembled_profile_by_id(profile_id: int, session: Session) -> Optional[UserProfile]:
    """Helper to load and assemble a full UserProfile schema from database given profile_id."""
    profile_db = session.get(UserProfileDB, profile_id)
    if not profile_db:
        return None

    contacts = session.exec(
        select(ContactNumberDB).where(ContactNumberDB.profile_id == profile_id)
    ).all()
    locations = session.exec(
        select(TargetLocationDB).where(TargetLocationDB.profile_id == profile_id)
    ).all()
    personas = session.exec(
        select(CareerPersonaDB).where(CareerPersonaDB.profile_id == profile_id)
    ).all()
    education = session.exec(
        select(EducationDB).where(EducationDB.profile_id == profile_id)
    ).all()
    languages = session.exec(
        select(LanguageDB).where(LanguageDB.profile_id == profile_id)
    ).all()

    return assemble_user_profile_schema(
        profile_db=profile_db,
        contacts=contacts,
        locations=locations,
        personas=personas,
        education=education,
        languages=languages,
    )

