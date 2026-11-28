from __future__ import annotations

import hashlib
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, delete
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    ConflictError,
    EventEnvelope,
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

from app.latex_parser import LatexCvParser
from app.latex_template import generate_base_latex_from_profile
from app.models import (
    BaseCvTemplateDB,
    CareerPersonaDB,
    ContactNumberDB,
    EducationRecordDB,
    MasterProfileDB,
    SpokenLanguageDB,
    TargetLocationDB,
    utc_now,
)
from app.schemas import (
    CareerPersona,
    Certification,
    ContactNumber,
    CustomSection,
    Education,
    ExperienceHighlight,
    FeaturedProject,
    LanguageProficiency,
    PersonalInfo,
    ResidenceAndMobility,
    SkillsAndTools,
    TargetLocation,
    UserProfile,
)

logger = logging.getLogger(__name__)


class ProfileSettings(ServiceSettings):
    service_name: str = "profile-service"
    database_url: str = "postgresql+psycopg://profile_svc:tailored_profile_pass@postgres:5432/profile_db"


settings = ProfileSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
latex_parser = LatexCvParser()

PROFILE_TABLES = [
    MasterProfileDB.__table__,
    ContactNumberDB.__table__,
    TargetLocationDB.__table__,
    CareerPersonaDB.__table__,
    EducationRecordDB.__table__,
    SpokenLanguageDB.__table__,
    BaseCvTemplateDB.__table__,
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
            aggregate_type="profile",
            aggregate_id=user_id,
            topic="profile.events.v1",
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


def _assemble_profile(session: Session, mp: MasterProfileDB) -> Dict[str, Any]:
    contacts = session.exec(select(ContactNumberDB).where(ContactNumberDB.profile_id == mp.id)).all()
    locations = session.exec(select(TargetLocationDB).where(TargetLocationDB.profile_id == mp.id)).all()
    personas = session.exec(select(CareerPersonaDB).where(CareerPersonaDB.profile_id == mp.id)).all()
    education = session.exec(select(EducationRecordDB).where(EducationRecordDB.profile_id == mp.id)).all()
    languages = session.exec(select(SpokenLanguageDB).where(SpokenLanguageDB.profile_id == mp.id)).all()

    profile = UserProfile(
        version="1.1.0",
        personal_info=PersonalInfo(
            full_name=mp.full_name,
            primary_email=mp.primary_email,
            contact_numbers=[
                ContactNumber(
                    country_code=c.country_code,
                    dial_code=c.dial_code,
                    phone_number=c.phone_number,
                    is_primary=c.is_primary,
                    label=c.label,
                )
                for c in contacts
            ],
            links=json.loads(mp.links_json or "{}"),
        ),
        residence_and_mobility=ResidenceAndMobility(
            current_residence={"city": mp.current_city, "country": mp.current_country},
            willing_to_relocate=mp.willing_to_relocate,
            target_locations=[
                TargetLocation(
                    location_id=l.location_id,
                    city=l.city,
                    country=l.country,
                    work_modes=json.loads(l.work_modes or '["Remote","Hybrid"]'),
                    is_active_for_search=l.is_active_for_search,
                )
                for l in locations
            ],
        ),
        education=[
            Education(
                institution=e.institution,
                degree=e.degree,
                field_of_study=e.field_of_study,
                graduation_year=e.graduation_year,
                grade_or_gpa=e.grade_or_gpa,
            )
            for e in education
        ],
        languages=[
            LanguageProficiency(language=lang.language, proficiency=lang.proficiency)
            for lang in languages
        ],
        career_personas=[
            CareerPersona(
                persona_id=p.persona_id,
                target_title=p.target_title,
                alternative_titles=json.loads(p.alternative_titles or "[]"),
                is_primary=p.is_primary,
                seniority_level=p.seniority_level,
                years_of_experience=p.years_of_experience,
                summary_bio=p.summary_bio,
                skills_and_tools=SkillsAndTools(**json.loads(p.skills_json or "{}")),
                experience_highlights=[
                    ExperienceHighlight(**item)
                    for item in json.loads(p.experience_highlights_json or "[]")
                ],
                featured_projects=[
                    FeaturedProject(**item)
                    for item in json.loads(p.featured_projects_json or "[]")
                ],
                certifications=[
                    Certification(**item)
                    for item in json.loads(p.certifications_json or "[]")
                ],
            )
            for p in personas
        ],
        custom_sections=[CustomSection(**item) for item in json.loads(mp.custom_sections_json or "[]")],
    )
    return {
        "id": mp.id,
        "user_id": mp.user_id,
        "version": mp.version,
        "active_persona_id": mp.active_persona_id,
        "onboarding_step": mp.onboarding_step,
        "onboarding_completed": mp.onboarding_completed,
        "profile": profile.model_dump(),
    }


def _replace_children(session: Session, mp: MasterProfileDB, profile_data: UserProfile) -> None:
    for tbl in (ContactNumberDB, TargetLocationDB, CareerPersonaDB, EducationRecordDB, SpokenLanguageDB):
        session.exec(delete(tbl).where(tbl.profile_id == mp.id))

    for c in profile_data.personal_info.contact_numbers:
        session.add(
            ContactNumberDB(
                profile_id=mp.id,
                country_code=c.country_code,
                dial_code=c.dial_code,
                phone_number=c.phone_number,
                is_primary=c.is_primary,
                label=c.label,
            )
        )
    for l in profile_data.residence_and_mobility.target_locations:
        session.add(
            TargetLocationDB(
                profile_id=mp.id,
                location_id=l.location_id,
                city=l.city,
                country=l.country,
                work_modes=json.dumps(l.work_modes),
                is_active_for_search=l.is_active_for_search,
            )
        )
    for p in profile_data.career_personas:
        session.add(
            CareerPersonaDB(
                profile_id=mp.id,
                persona_id=p.persona_id,
                target_title=p.target_title,
                alternative_titles=json.dumps(p.alternative_titles),
                is_primary=p.is_primary,
                seniority_level=p.seniority_level,
                years_of_experience=p.years_of_experience,
                summary_bio=p.summary_bio,
                skills_json=p.skills_and_tools.model_dump_json(),
                experience_highlights_json=json.dumps([x.model_dump() for x in p.experience_highlights]),
                featured_projects_json=json.dumps([x.model_dump() for x in p.featured_projects]),
                certifications_json=json.dumps([x.model_dump() for x in p.certifications]),
            )
        )
    for e in profile_data.education:
        session.add(
            EducationRecordDB(
                profile_id=mp.id,
                institution=e.institution,
                degree=e.degree,
                field_of_study=e.field_of_study,
                graduation_year=e.graduation_year,
                grade_or_gpa=e.grade_or_gpa,
            )
        )
    for lang in profile_data.languages:
        session.add(
            SpokenLanguageDB(
                profile_id=mp.id,
                language=lang.language,
                proficiency=lang.proficiency,
            )
        )


def _delete_user_profile_data(user_id: str) -> None:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == user_id)).first()
        if not mp:
            return
        for tbl in (
            ContactNumberDB,
            TargetLocationDB,
            CareerPersonaDB,
            EducationRecordDB,
            SpokenLanguageDB,
            BaseCvTemplateDB,
        ):
            session.exec(delete(tbl).where(tbl.profile_id == mp.id))
        session.exec(delete(MasterProfileDB).where(MasterProfileDB.id == mp.id))
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=PROFILE_TABLES)
    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable on startup (%s)", exc)
    app.state.redpanda_producer = producer

    relay = OutboxRelay(
        session_factory=lambda: Session(engine),
        producer=producer,
        service_name=settings.service_name,
    )
    await relay.start()

    async def on_identity_event(env: EventEnvelope) -> None:
        if env.event_type == "user.erasure.requested":
            uid = env.payload.get("user_id") or env.actor.user_id
            if uid:
                _delete_user_profile_data(uid)

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["identity.lifecycle.v1"],
        group_id="profile-erasure-cg",
        handler=on_identity_event,
        dlq_producer=producer,
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("Consumer start delayed (%s)", exc)

    try:
        yield
    finally:
        await consumer.stop()
        await relay.stop()
        await producer.stop()


app = create_service_app(
    settings,
    title="Tailored Profile Service",
    lifespan=lifespan,
)


# --- Schemas ---

class ParseLatexRequest(BaseModel):
    latex_content: str


class OnboardingStepRequest(BaseModel):
    step: int = Field(ge=1, le=6)
    completed: bool = False
    profile: UserProfile


class ActivePersonaPatch(BaseModel):
    persona_id: str


class BaseTemplateCreate(BaseModel):
    name: str = "Custom ATS Template"
    source_type: str = "uploaded_tex"
    latex_content: Optional[str] = None
    persona_id: Optional[str] = None
    is_default: bool = True


# --- Endpoints ---

@app.get("/api/v1/profiles/me")
async def get_my_profile(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            mp = MasterProfileDB(user_id=ctx.user_id)
            session.add(mp)
            session.commit()
            session.refresh(mp)
        return _assemble_profile(session, mp)


@app.put("/api/v1/profiles/me")
@audit_feature(feature_key="profile.master.update", resource_type="master_profile", action="update")
async def update_my_profile(
    payload: UserProfile,
    request: Request,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            mp = MasterProfileDB(user_id=ctx.user_id)
            session.add(mp)
            session.flush()
        elif if_match is not None:
            try:
                expected_v = int(if_match.strip().strip('"'))
            except ValueError:
                expected_v = mp.version
            if expected_v != mp.version:
                raise ConflictError(
                    f"Profile version conflict: expected {expected_v}, current {mp.version}."
                )

        mp.full_name = payload.personal_info.full_name
        mp.primary_email = payload.personal_info.primary_email
        mp.current_city = payload.residence_and_mobility.current_residence.get("city", mp.current_city)
        mp.current_country = payload.residence_and_mobility.current_residence.get("country", mp.current_country)
        mp.willing_to_relocate = payload.residence_and_mobility.willing_to_relocate
        mp.links_json = json.dumps(payload.personal_info.links)
        mp.custom_sections_json = json.dumps([s.model_dump() for s in payload.custom_sections])
        primary_p = payload.get_primary_persona()
        if primary_p and not mp.active_persona_id:
            mp.active_persona_id = primary_p.persona_id
        mp.version += 1
        mp.updated_at = utc_now()
        session.add(mp)
        session.flush()

        _replace_children(session, mp, payload)
        _enqueue_outbox(
            session,
            event_type="profile.updated",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="profile.master.update",
            payload={"user_id": ctx.user_id, "profile_id": mp.id, "version": mp.version},
        )
        session.commit()
        session.refresh(mp)
        return _assemble_profile(session, mp)


@app.post("/api/v1/profiles/me/onboarding-step")
@audit_feature(feature_key="onboarding.step.save", resource_type="master_profile", action="onboarding")
async def save_onboarding_step(
    payload: OnboardingStepRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            mp = MasterProfileDB(user_id=ctx.user_id)
            session.add(mp)
            session.flush()
        mp.full_name = payload.profile.personal_info.full_name or mp.full_name
        mp.primary_email = payload.profile.personal_info.primary_email or mp.primary_email
        mp.current_city = payload.profile.residence_and_mobility.current_residence.get("city", mp.current_city)
        mp.current_country = payload.profile.residence_and_mobility.current_residence.get("country", mp.current_country)
        mp.willing_to_relocate = payload.profile.residence_and_mobility.willing_to_relocate
        mp.links_json = json.dumps(payload.profile.personal_info.links)
        mp.custom_sections_json = json.dumps([s.model_dump() for s in payload.profile.custom_sections])
        mp.onboarding_step = max(mp.onboarding_step, payload.step)
        mp.onboarding_completed = mp.onboarding_completed or payload.completed
        primary_p = payload.profile.get_primary_persona()
        if primary_p:
            mp.active_persona_id = primary_p.persona_id
        mp.version += 1
        mp.updated_at = utc_now()
        session.add(mp)
        session.flush()
        _replace_children(session, mp, payload.profile)
        _enqueue_outbox(
            session,
            event_type="profile.updated",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="onboarding.step.save",
            payload={"user_id": ctx.user_id, "step": payload.step, "completed": mp.onboarding_completed},
        )
        session.commit()
        session.refresh(mp)
        return _assemble_profile(session, mp)


@app.post("/api/v1/profiles/parse-latex")
@audit_feature(feature_key="onboarding.latex_drop.parse", resource_type="latex_cv", action="parse")
async def parse_latex_cv(payload: ParseLatexRequest, request: Request) -> Dict[str, Any]:
    parsed = latex_parser.parse(payload.latex_content)
    return {
        "success": True,
        "message": "LaTeX CV parsed cleanly.",
        "stats": parsed.get("stats", {}),
        "profile": parsed.get("profile", parsed),
    }


@app.post("/api/v1/profiles/me/personas", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="profile.persona.create", resource_type="career_persona", action="create")
async def add_persona(
    persona: CareerPersona, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            mp = MasterProfileDB(user_id=ctx.user_id)
            session.add(mp)
            session.flush()
        if persona.is_primary:
            existing = session.exec(select(CareerPersonaDB).where(CareerPersonaDB.profile_id == mp.id)).all()
            for ep in existing:
                ep.is_primary = False
                session.add(ep)
            mp.active_persona_id = persona.persona_id
        db_p = CareerPersonaDB(
            profile_id=mp.id,
            persona_id=persona.persona_id,
            target_title=persona.target_title,
            alternative_titles=json.dumps(persona.alternative_titles),
            is_primary=persona.is_primary,
            seniority_level=persona.seniority_level,
            years_of_experience=persona.years_of_experience,
            summary_bio=persona.summary_bio,
            skills_json=persona.skills_and_tools.model_dump_json(),
            experience_highlights_json=json.dumps([x.model_dump() for x in persona.experience_highlights]),
            featured_projects_json=json.dumps([x.model_dump() for x in persona.featured_projects]),
            certifications_json=json.dumps([x.model_dump() for x in persona.certifications]),
        )
        mp.version += 1
        session.add(db_p)
        session.add(mp)
        _enqueue_outbox(
            session,
            event_type="persona.changed",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="profile.persona.create",
            payload={"user_id": ctx.user_id, "persona_id": persona.persona_id},
        )
        session.commit()
        return _assemble_profile(session, mp)


@app.patch("/api/v1/profiles/me/personas/{persona_id}")
async def update_persona(
    persona_id: str, persona: CareerPersona, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            raise NotFoundError("Master profile not found.")
        db_p = session.exec(
            select(CareerPersonaDB).where(
                CareerPersonaDB.profile_id == mp.id,
                CareerPersonaDB.persona_id == persona_id,
            )
        ).first()
        if not db_p:
            raise NotFoundError("Persona not found.")
        db_p.target_title = persona.target_title
        db_p.alternative_titles = json.dumps(persona.alternative_titles)
        db_p.is_primary = persona.is_primary
        db_p.seniority_level = persona.seniority_level
        db_p.years_of_experience = persona.years_of_experience
        db_p.summary_bio = persona.summary_bio
        db_p.skills_json = persona.skills_and_tools.model_dump_json()
        db_p.experience_highlights_json = json.dumps([x.model_dump() for x in persona.experience_highlights])
        db_p.featured_projects_json = json.dumps([x.model_dump() for x in persona.featured_projects])
        db_p.certifications_json = json.dumps([x.model_dump() for x in persona.certifications])
        db_p.updated_at = utc_now()
        mp.version += 1
        session.add(db_p)
        session.add(mp)
        session.commit()
        return _assemble_profile(session, mp)


@app.delete("/api/v1/profiles/me/personas/{persona_id}")
async def delete_persona(persona_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            raise NotFoundError("Master profile not found.")
        db_p = session.exec(
            select(CareerPersonaDB).where(
                CareerPersonaDB.profile_id == mp.id,
                CareerPersonaDB.persona_id == persona_id,
            )
        ).first()
        if not db_p:
            raise NotFoundError("Persona not found.")
        session.delete(db_p)
        mp.version += 1
        session.add(mp)
        session.commit()
        return {"deleted": persona_id}


@app.patch("/api/v1/profiles/me/active-persona")
@audit_feature(feature_key="profile.persona.switch", resource_type="career_persona", action="switch")
async def switch_active_persona(
    payload: ActivePersonaPatch, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            raise NotFoundError("Master profile not found.")
        mp.active_persona_id = payload.persona_id
        mp.updated_at = utc_now()
        session.add(mp)
        _enqueue_outbox(
            session,
            event_type="persona.changed",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="profile.persona.switch",
            payload={"user_id": ctx.user_id, "active_persona_id": payload.persona_id},
        )
        session.commit()
        return {"active_persona_id": mp.active_persona_id}


@app.get("/api/v1/profiles/me/base-templates")
async def list_base_templates(ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            return []
        rows = session.exec(select(BaseCvTemplateDB).where(BaseCvTemplateDB.profile_id == mp.id)).all()
        if not rows:
            assembled = _assemble_profile(session, mp)
            user_profile = UserProfile(**assembled["profile"])
            latex = generate_base_latex_from_profile(user_profile, persona_id=mp.active_persona_id)
            sha = hashlib.sha256(latex.encode("utf-8")).hexdigest()
            tpl = BaseCvTemplateDB(
                profile_id=mp.id,
                name="Master Profile ATS Template",
                source_type="synthesized",
                latex_content=latex,
                sha256=sha,
                is_default=True,
            )
            session.add(tpl)
            session.commit()
            session.refresh(tpl)
            rows = [tpl]
        return [r.model_dump() for r in rows]


@app.post("/api/v1/profiles/me/base-templates", status_code=status.HTTP_201_CREATED)
async def create_base_template(
    payload: BaseTemplateCreate, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == ctx.user_id)).first()
        if not mp:
            mp = MasterProfileDB(user_id=ctx.user_id)
            session.add(mp)
            session.flush()
        latex = payload.latex_content
        if not latex:
            assembled = _assemble_profile(session, mp)
            latex = generate_base_latex_from_profile(
                UserProfile(**assembled["profile"]), persona_id=payload.persona_id or mp.active_persona_id
            )
        if payload.is_default:
            for existing in session.exec(select(BaseCvTemplateDB).where(BaseCvTemplateDB.profile_id == mp.id)).all():
                existing.is_default = False
                session.add(existing)
        sha = hashlib.sha256(latex.encode("utf-8")).hexdigest()
        tpl = BaseCvTemplateDB(
            profile_id=mp.id,
            name=payload.name,
            source_type=payload.source_type,
            latex_content=latex,
            sha256=sha,
            is_default=payload.is_default,
        )
        session.add(tpl)
        session.commit()
        session.refresh(tpl)
        return tpl.model_dump()


@app.get("/internal/profiles/{user_id}/summary")
async def internal_profile_summary(
    user_id: str, _: RequestContext = Depends(require_internal_service)
) -> Dict[str, Any]:
    with Session(engine) as session:
        mp = session.exec(select(MasterProfileDB).where(MasterProfileDB.user_id == user_id)).first()
        if not mp:
            return {"user_id": user_id, "exists": False, "profile": UserProfile().model_dump()}
        data = _assemble_profile(session, mp)
        data["exists"] = True
        tpl = session.exec(
            select(BaseCvTemplateDB).where(BaseCvTemplateDB.profile_id == mp.id, BaseCvTemplateDB.is_default == True)  # noqa: E712
        ).first()
        data["default_base_latex"] = (
            tpl.latex_content
            if tpl
            else generate_base_latex_from_profile(
                UserProfile(**data["profile"]), persona_id=mp.active_persona_id
            )
        )
        return data
