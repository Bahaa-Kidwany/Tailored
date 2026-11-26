import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, delete
from pydantic import BaseModel, Field

from app.core.database import get_session, engine
from app.schemas.user_profile import (
    UserProfile,
    CareerPersona,
)
from app.schemas.search_request import SearchRequest, SearchLocation, IngestionSources, SearchConstraints
from app.schemas.cv_fit import CvFitSummaryResponse
from app.ai.tailor.cv_fit_service import cv_fit_service
from app.models.profile import (
    UserProfileDB,
    ContactNumberDB,
    TargetLocationDB,
    CareerPersonaDB,
    EducationDB,
    LanguageDB,
    assemble_user_profile_schema,
    utc_now,
)
from app.pipeline.latex_cv_parser import latex_cv_parser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

# --- Response & Request Schemas ---

class ParseLatexRequest(BaseModel):
    latex_content: str

class ParseLatexResponse(BaseModel):
    success: bool
    message: str
    stats: Dict[str, Any]
    profile: Dict[str, Any]

class ProfileSummary(BaseModel):
    id: int
    full_name: str
    primary_email: str
    current_city: str
    current_country: str
    willing_to_relocate: bool
    persona_count: int
    primary_persona_title: Optional[str] = None
    created_at: str
    updated_at: str

class FullProfileResponse(BaseModel):
    id: int
    profile: UserProfile

class DBStatusResponse(BaseModel):
    status: str
    engine_type: str
    database_url_masked: str
    counts: Dict[str, int]

# --- Helper to load full profile by ID ---

def _load_assembled_profile(profile_id: int, session: Session) -> tuple[UserProfileDB, UserProfile]:
    profile_db = session.get(UserProfileDB, profile_id)
    if not profile_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile with id={profile_id} was not found."
        )

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

    full_profile = assemble_user_profile_schema(
        profile_db=profile_db,
        contacts=contacts,
        locations=locations,
        personas=personas,
        education=education,
        languages=languages,
    )

    return profile_db, full_profile

# --- Endpoints ---

@router.post("", response_model=FullProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: UserProfile,
    session: Session = Depends(get_session),
):
    """
    Creates a new Master Profile along with regional contact numbers,
    target search locations, career persona tracks, education, and spoken languages.
    """
    try:
        # 1. Master Profile record
        profile_db = UserProfileDB(
            full_name=profile_data.personal_info.full_name,
            primary_email=profile_data.personal_info.primary_email,
            current_city=profile_data.residence_and_mobility.current_residence.get("city", "Cairo"),
            current_country=profile_data.residence_and_mobility.current_residence.get("country", "Egypt"),
            willing_to_relocate=profile_data.residence_and_mobility.willing_to_relocate,
            links_json=json.dumps(profile_data.personal_info.links),
            custom_sections_json=json.dumps([s.model_dump() for s in (profile_data.custom_sections or [])]),
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(profile_db)
        session.flush()  # assign profile_db.id

        # 2. Regional Contact numbers
        for contact in profile_data.personal_info.contact_numbers:
            contact_db = ContactNumberDB(
                profile_id=profile_db.id,
                country_code=contact.country_code,
                dial_code=contact.dial_code,
                phone_number=contact.phone_number,
                is_primary=contact.is_primary,
                label=contact.label,
            )
            session.add(contact_db)

        # 3. Target Locations
        for loc in profile_data.residence_and_mobility.target_locations:
            loc_db = TargetLocationDB(
                profile_id=profile_db.id,
                location_id=loc.location_id,
                city=loc.city,
                country=loc.country,
                work_modes_json=json.dumps(loc.work_modes),
                is_active_for_search=loc.is_active_for_search,
            )
            session.add(loc_db)

        # 4. Career Personas
        for persona in profile_data.career_personas:
            persona_db = CareerPersonaDB(
                profile_id=profile_db.id,
                persona_id=persona.persona_id,
                target_title=persona.target_title,
                alternative_titles_json=json.dumps(persona.alternative_titles),
                is_primary=persona.is_primary,
                seniority_level=persona.seniority_level,
                years_of_experience=persona.years_of_experience,
                summary_bio=persona.summary_bio,
                skills_json=json.dumps(persona.skills_and_tools.model_dump()),
                experience_highlights_json=json.dumps([h.model_dump() for h in persona.experience_highlights]),
                featured_projects_json=json.dumps([p.model_dump() for p in persona.featured_projects]),
                certifications_json=json.dumps([c.model_dump() for c in persona.certifications]),
            )
            session.add(persona_db)

        # 5. Education
        for edu in profile_data.education:
            edu_db = EducationDB(
                profile_id=profile_db.id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                graduation_year=edu.graduation_year,
                grade_or_gpa=edu.grade_or_gpa,
            )
            session.add(edu_db)

        # 6. Languages
        for lang in profile_data.languages:
            lang_db = LanguageDB(
                profile_id=profile_db.id,
                language=lang.language,
                proficiency=lang.proficiency,
            )
            session.add(lang_db)

        session.commit()
        session.refresh(profile_db)

        _, full_profile = _load_assembled_profile(profile_db.id, session)
        return FullProfileResponse(id=profile_db.id, profile=full_profile)

    except Exception as exc:
        session.rollback()
        logger.error("Failed to create profile: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not persist profile: {str(exc)}"
        )


@router.get("", response_model=List[ProfileSummary])
def list_profiles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Lists summary info for all saved Master Profiles."""
    profiles_db = session.exec(
        select(UserProfileDB).offset(skip).limit(limit).order_by(UserProfileDB.id.desc())
    ).all()

    summaries = []
    for p in profiles_db:
        personas = session.exec(
            select(CareerPersonaDB).where(CareerPersonaDB.profile_id == p.id)
        ).all()
        primary_persona = next((per for per in personas if per.is_primary), None)
        if not primary_persona and personas:
            primary_persona = personas[0]

        summaries.append(
            ProfileSummary(
                id=p.id,
                full_name=p.full_name,
                primary_email=p.primary_email,
                current_city=p.current_city,
                current_country=p.current_country,
                willing_to_relocate=p.willing_to_relocate,
                persona_count=len(personas),
                primary_persona_title=primary_persona.target_title if primary_persona else None,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
        )
    return summaries


@router.get("/{profile_id}", response_model=FullProfileResponse)
def get_profile(
    profile_id: int,
    session: Session = Depends(get_session),
):
    """Retrieves a full User Profile by ID, formatted to standard UserProfile schema."""
    profile_db, full_profile = _load_assembled_profile(profile_id, session)
    return FullProfileResponse(id=profile_db.id, profile=full_profile)


@router.put("/{profile_id}", response_model=FullProfileResponse)
def update_profile(
    profile_id: int,
    profile_data: UserProfile,
    session: Session = Depends(get_session),
):
    """Updates an existing Master Profile and synchronizes its child tables."""
    profile_db = session.get(UserProfileDB, profile_id)
    if not profile_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id={profile_id} not found."
        )

    try:
        # Update Master Profile
        profile_db.full_name = profile_data.personal_info.full_name
        profile_db.primary_email = profile_data.personal_info.primary_email
        profile_db.current_city = profile_data.residence_and_mobility.current_residence.get("city", "Cairo")
        profile_db.current_country = profile_data.residence_and_mobility.current_residence.get("country", "Egypt")
        profile_db.willing_to_relocate = profile_data.residence_and_mobility.willing_to_relocate
        profile_db.links_json = json.dumps(profile_data.personal_info.links)
        profile_db.custom_sections_json = json.dumps([s.model_dump() for s in (profile_data.custom_sections or [])])
        profile_db.updated_at = utc_now()
        session.add(profile_db)

        # Clear and recreate child items
        session.exec(delete(ContactNumberDB).where(ContactNumberDB.profile_id == profile_id))
        session.exec(delete(TargetLocationDB).where(TargetLocationDB.profile_id == profile_id))
        session.exec(delete(CareerPersonaDB).where(CareerPersonaDB.profile_id == profile_id))
        session.exec(delete(EducationDB).where(EducationDB.profile_id == profile_id))
        session.exec(delete(LanguageDB).where(LanguageDB.profile_id == profile_id))

        # Re-insert contacts
        for contact in profile_data.personal_info.contact_numbers:
            session.add(
                ContactNumberDB(
                    profile_id=profile_id,
                    country_code=contact.country_code,
                    dial_code=contact.dial_code,
                    phone_number=contact.phone_number,
                    is_primary=contact.is_primary,
                    label=contact.label,
                )
            )

        # Re-insert locations
        for loc in profile_data.residence_and_mobility.target_locations:
            session.add(
                TargetLocationDB(
                    profile_id=profile_id,
                    location_id=loc.location_id,
                    city=loc.city,
                    country=loc.country,
                    work_modes_json=json.dumps(loc.work_modes),
                    is_active_for_search=loc.is_active_for_search,
                )
            )

        # Re-insert personas
        for persona in profile_data.career_personas:
            session.add(
                CareerPersonaDB(
                    profile_id=profile_id,
                    persona_id=persona.persona_id,
                    target_title=persona.target_title,
                    alternative_titles_json=json.dumps(persona.alternative_titles),
                    is_primary=persona.is_primary,
                    seniority_level=persona.seniority_level,
                    years_of_experience=persona.years_of_experience,
                    summary_bio=persona.summary_bio,
                    skills_json=json.dumps(persona.skills_and_tools.model_dump()),
                    experience_highlights_json=json.dumps([h.model_dump() for h in persona.experience_highlights]),
                    featured_projects_json=json.dumps([p.model_dump() for p in persona.featured_projects]),
                    certifications_json=json.dumps([c.model_dump() for c in persona.certifications]),
                )
            )

        # Re-insert education
        for edu in profile_data.education:
            session.add(
                EducationDB(
                    profile_id=profile_id,
                    institution=edu.institution,
                    degree=edu.degree,
                    field_of_study=edu.field_of_study,
                    graduation_year=edu.graduation_year,
                    grade_or_gpa=edu.grade_or_gpa,
                )
            )

        # Re-insert languages
        for lang in profile_data.languages:
            session.add(
                LanguageDB(
                    profile_id=profile_id,
                    language=lang.language,
                    proficiency=lang.proficiency,
                )
            )

        session.commit()
        session.refresh(profile_db)

        _, full_profile = _load_assembled_profile(profile_id, session)
        return FullProfileResponse(id=profile_id, profile=full_profile)

    except Exception as exc:
        session.rollback()
        logger.error("Failed to update profile: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update profile: {str(exc)}"
        )


@router.delete("/{profile_id}", status_code=status.HTTP_200_OK)
def delete_profile(
    profile_id: int,
    session: Session = Depends(get_session),
):
    """Deletes a Master Profile and all associated child tables."""
    profile_db = session.get(UserProfileDB, profile_id)
    if not profile_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id={profile_id} not found."
        )

    try:
        session.exec(delete(ContactNumberDB).where(ContactNumberDB.profile_id == profile_id))
        session.exec(delete(TargetLocationDB).where(TargetLocationDB.profile_id == profile_id))
        session.exec(delete(CareerPersonaDB).where(CareerPersonaDB.profile_id == profile_id))
        session.exec(delete(EducationDB).where(EducationDB.profile_id == profile_id))
        session.exec(delete(LanguageDB).where(LanguageDB.profile_id == profile_id))
        session.delete(profile_db)
        session.commit()

        return {"deleted": True, "id": profile_id, "message": f"Profile {profile_id} successfully deleted."}
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(exc)}"
        )


@router.post("/{profile_id}/personas", response_model=FullProfileResponse)
def add_persona_to_profile(
    profile_id: int,
    persona_data: CareerPersona,
    session: Session = Depends(get_session),
):
    """Appends a new Career Persona track to an existing profile."""
    profile_db = session.get(UserProfileDB, profile_id)
    if not profile_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id={profile_id} not found."
        )

    # Check for duplicate persona_id
    existing = session.exec(
        select(CareerPersonaDB).where(
            CareerPersonaDB.profile_id == profile_id,
            CareerPersonaDB.persona_id == persona_data.persona_id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persona '{persona_data.persona_id}' already exists on this profile."
        )

    # If this new one is marked primary, unmark existing ones
    if persona_data.is_primary:
        existing_personas = session.exec(
            select(CareerPersonaDB).where(CareerPersonaDB.profile_id == profile_id)
        ).all()
        for p in existing_personas:
            p.is_primary = False
            session.add(p)

    persona_db = CareerPersonaDB(
        profile_id=profile_id,
        persona_id=persona_data.persona_id,
        target_title=persona_data.target_title,
        alternative_titles_json=json.dumps(persona_data.alternative_titles),
        is_primary=persona_data.is_primary,
        seniority_level=persona_data.seniority_level,
        years_of_experience=persona_data.years_of_experience,
        summary_bio=persona_data.summary_bio,
        skills_json=json.dumps(persona_data.skills_and_tools.model_dump()),
        experience_highlights_json=json.dumps([h.model_dump() for h in persona_data.experience_highlights]),
        featured_projects_json=json.dumps([p.model_dump() for p in persona_data.featured_projects]),
        certifications_json=json.dumps([c.model_dump() for c in persona_data.certifications]),
    )
    session.add(persona_db)
    profile_db.updated_at = utc_now()
    session.add(profile_db)
    session.commit()

    _, full_profile = _load_assembled_profile(profile_id, session)
    return FullProfileResponse(id=profile_id, profile=full_profile)


@router.patch("/{profile_id}/personas/{persona_id}/primary", response_model=FullProfileResponse)
def set_primary_persona(
    profile_id: int,
    persona_id: str,
    session: Session = Depends(get_session),
):
    """Sets a specific persona as the primary active track on the profile."""
    personas = session.exec(
        select(CareerPersonaDB).where(CareerPersonaDB.profile_id == profile_id)
    ).all()
    if not personas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No personas found for profile id={profile_id}."
        )

    found = False
    for p in personas:
        if p.persona_id == persona_id:
            p.is_primary = True
            found = True
        else:
            p.is_primary = False
        session.add(p)

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found in profile {profile_id}."
        )

    profile_db = session.get(UserProfileDB, profile_id)
    if profile_db:
        profile_db.updated_at = utc_now()
        session.add(profile_db)

    session.commit()
    _, full_profile = _load_assembled_profile(profile_id, session)
    return FullProfileResponse(id=profile_id, profile=full_profile)


@router.get("/{profile_id}/search-request/{persona_id}", response_model=SearchRequest)
def get_derived_search_request(
    profile_id: int,
    persona_id: str,
    session: Session = Depends(get_session),
):
    """
    Derives an API SearchRequest payload for Apify LinkedIn & Wuzzuf scrapers
    using the active locations from the profile and target query terms from the persona.
    """
    _, full_profile = _load_assembled_profile(profile_id, session)
    persona = full_profile.get_persona(persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found on profile {profile_id}."
        )

    active_locations = [
        SearchLocation(
            city=loc.city,
            country=loc.country,
            work_modes=loc.work_modes,
            is_remote="Remote" in loc.work_modes or loc.city.lower() in ["remote", "worldwide"],
        )
        for loc in full_profile.get_active_search_locations()
    ]

    query_terms = persona.get_search_query_titles()

    return SearchRequest(
        persona_id=persona.persona_id,
        derived_from_persona=True,
        query_terms=query_terms,
        target_locations=active_locations,
        seniority_filter=[persona.seniority_level],
        date_posted_filter="past-24h",
        enabled_sources=IngestionSources(
            enable_linkedin=True,
            enable_wuzzuf=True,
            enable_company_ats=True,
        ),
        constraints=SearchConstraints(
            max_results_per_source_per_location=20,
            exclude_keywords=["unpaid", "internship", "volunteer"],
            must_have_skills=persona.skills_and_tools.core_skills[:5],
        ),
    )


@router.get("/{profile_id}/tailored-cvs", response_model=List[CvFitSummaryResponse])
def list_profile_tailored_cvs(profile_id: int):
    """Returns all tailored CV documents persisted for the specified candidate profile."""
    return cv_fit_service.list_cv_fits(profile_id=profile_id)


@router.get("/system/db-status", response_model=DBStatusResponse)
def get_db_status(session: Session = Depends(get_session)):
    """Returns database connection status, active engine (Postgres vs SQLite), and entity counts."""
    engine_name = engine.dialect.name
    masked_url = str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url)

    profiles_count = len(session.exec(select(UserProfileDB.id)).all())
    personas_count = len(session.exec(select(CareerPersonaDB.id)).all())
    locations_count = len(session.exec(select(TargetLocationDB.id)).all())
    contacts_count = len(session.exec(select(ContactNumberDB.id)).all())

    return DBStatusResponse(
        status="healthy",
        engine_type="postgresql" if "postgres" in engine_name else "sqlite",
        database_url_masked=masked_url,
        counts={
            "profiles": profiles_count,
            "personas": personas_count,
            "target_locations": locations_count,
            "contact_numbers": contacts_count,
        },
    )


@router.post("/parse-latex", response_model=ParseLatexResponse)
def parse_latex_cv(payload: ParseLatexRequest):
    """
    Parses LaTeX CV / Resume source code and automatically extracts candidate
    personal details, target title, experiences, education, and skills.
    """
    if not payload.latex_content or not payload.latex_content.strip():
        raise HTTPException(status_code=400, detail="LaTeX content cannot be empty.")

    try:
        parsed = latex_cv_parser.parse(payload.latex_content)
        stats = parsed.get("stats", {})
        summary_msg = (
            f"Extracted {stats.get('experience_count', 0)} experiences, "
            f"{stats.get('education_count', 0)} degrees, and "
            f"{stats.get('skills_count', 0)} skills."
        )
        return ParseLatexResponse(
            success=True,
            message=summary_msg,
            stats=stats,
            profile=parsed,
        )
    except Exception as exc:
        logger.error("Failed to parse LaTeX CV: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to parse LaTeX CV: {str(exc)}")
