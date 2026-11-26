import re
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.core.database import engine
from app.models.job import JobDB, UserProfile
from app.pipeline.job_search_service import JobSearchService

router = APIRouter(prefix="/jobs", tags=["jobs"])

# --- Request / Response Models ---

class AutoSearchRequest(BaseModel):
    profile_id: Optional[int] = None
    persona_id: Optional[str] = None
    query: Optional[str] = None
    location: Optional[str] = None
    min_score: float = 60.0
    enable_live_apify: bool = False
    source: Optional[str] = None

class IngestUrlRequest(BaseModel):
    url: str
    profile_id: Optional[int] = None
    persona_id: Optional[str] = None

class IngestDescriptionRequest(BaseModel):
    description: str
    company_name: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    profile_id: Optional[int] = None
    persona_id: Optional[str] = None

class JobDetailResponse(BaseModel):
    id: int
    source_id: str
    title: str
    company_name: str
    location: str
    url: str
    raw_description: str
    fit_score: float
    is_high_match: bool
    source_type: str
    parsed_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    location_type: str = "Hybrid"
    created_at: str
    recruiter_email: Optional[str] = None

def extract_recruiter_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))]
    return valid_emails[0] if valid_emails else None

def format_job_response(job: JobDB) -> JobDetailResponse:
    parsed = job.get_parsed_job()
    skills = []
    responsibilities = []
    location_type = "Hybrid"
    if parsed:
        skills = parsed.required_skills + parsed.nice_to_have_skills
        responsibilities = parsed.core_responsibilities
        location_type = parsed.location_type

    sid_low = (job.source_id or "").lower()
    url_low = (job.url or "").lower()
    if (
        "linkedin_post" in sid_low
        or "recruiter" in sid_low
        or "custom_post" in sid_low
        or "/feed/update/" in url_low
        or "/posts/" in url_low
        or "activity-" in url_low
        or "activity:" in url_low
    ):
        source_type = "recruiter_post" if "custom" in sid_low or "recruiter" in sid_low else "linkedin_posts"
    elif "linkedin" in sid_low or "linkedin" in url_low or "lnkd.in" in url_low:
        source_type = "linkedin"
    elif "wuzzuf" in sid_low or "wuzzuf" in url_low:
        source_type = "wuzzuf"
    else:
        source_type = "web"

    recruiter_email = extract_recruiter_email(job.raw_description)

    return JobDetailResponse(
        id=job.id,
        source_id=job.source_id,
        title=job.title,
        company_name=job.company_name,
        location=job.location,
        url=job.url,
        raw_description=job.raw_description,
        fit_score=round(job.fit_score, 1),
        is_high_match=job.fit_score >= 85.0,
        source_type=source_type,
        parsed_skills=skills,
        responsibilities=responsibilities,
        location_type=location_type,
        created_at=job.created_at.isoformat(),
        recruiter_email=recruiter_email,
    )

# --- Routes ---

@router.post("/auto-search", response_model=List[JobDetailResponse])
def trigger_auto_search(payload: AutoSearchRequest):
    """
    Triggers automated multi-source job discovery & candidate alignment scoring
    using the candidate's active persona and target locations.
    """
    service = JobSearchService()
    saved_jobs = service.execute_search_and_ingestion(
        profile_id=payload.profile_id,
        persona_id=payload.persona_id,
        query_override=payload.query,
        location_override=payload.location,
        min_score=payload.min_score,
        enable_live_apify=payload.enable_live_apify,
        source_override=payload.source,
    )
    return [format_job_response(j) for j in saved_jobs]


@router.post("/ingest-url", response_model=JobDetailResponse)
def ingest_job_from_url(payload: IngestUrlRequest):
    """
    Ingests a single job posting by URL (LinkedIn, Wuzzuf, or any career page),
    extracts structured requirements, scores candidate alignment, and commits to database.
    """
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="A valid job URL is required.")

    service = JobSearchService()
    try:
        saved_job = service.ingest_job_from_url(
            url=payload.url,
            profile_id=payload.profile_id,
            persona_id=payload.persona_id,
        )
        return format_job_response(saved_job)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest job from URL: {str(exc)}")


@router.post("/extract-description", response_model=JobDetailResponse)
def extract_and_ingest_description(payload: IngestDescriptionRequest):
    """
    Auto-extracts job requirements, contacts, and candidate alignment from a pasted
    job description or recruiter post, saves to database, and returns the structured job.
    """
    if not payload.description or len(payload.description.strip()) < 15:
        raise HTTPException(status_code=400, detail="Please provide a valid job description (at least 15 characters).")

    service = JobSearchService()
    try:
        saved_job = service.ingest_job_from_description(
            raw_description=payload.description.strip(),
            title=payload.title,
            company_name=payload.company_name,
            url=payload.url,
            profile_id=payload.profile_id,
            persona_id=payload.persona_id,
        )
        return format_job_response(saved_job)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to extract and save job description: {str(exc)}")


@router.get("", response_model=List[JobDetailResponse])
def list_jobs(
    query: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=100.0),
    source: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    Retrieves saved and scored jobs with optional keyword, location, and minimum score filters.
    """
    with Session(engine) as session:
        statement = select(JobDB).order_by(JobDB.fit_score.desc())

        if min_score is not None:
            statement = statement.where(JobDB.fit_score >= min_score)

        jobs = session.exec(statement).all()

        # In-memory post filtering for text search flexibility
        filtered = []
        for j in jobs:
            if query and query.strip():
                q = query.lower().strip()
                if q not in j.title.lower() and q not in j.company_name.lower() and q not in j.raw_description.lower():
                    continue
            if location and location.strip() and location.lower() != "all":
                loc = location.lower().strip()
                if loc not in j.location.lower():
                    continue
            if source and source.strip() and source.lower() != "all":
                src = source.lower().strip()
                sid_low = j.source_id.lower()
                url_low = j.url.lower()
                is_linkedin_post = (
                    "linkedin_post" in sid_low
                    or "recruiter" in sid_low
                    or "custom_post" in sid_low
                    or "/feed/update/" in url_low
                    or "/posts/" in url_low
                    or "activity-" in url_low
                    or "activity:" in url_low
                )
                is_linkedin_job = (
                    ("linkedin" in sid_low or "linkedin" in url_low or "lnkd.in" in url_low)
                    and not is_linkedin_post
                )
                is_wuzzuf = "wuzzuf" in sid_low or "wuzzuf" in url_low
                if src == "linkedin_posts" and not is_linkedin_post:
                    continue
                if src == "linkedin" and not is_linkedin_job:
                    continue
                if src == "wuzzuf" and not is_wuzzuf:
                    continue
            filtered.append(j)

        paginated = filtered[skip : skip + limit]
        return [format_job_response(j) for j in paginated]


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int):
    """Retrieve full details, parsed requirements, and evaluation score for a job."""
    with Session(engine) as session:
        job = session.get(JobDB, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return format_job_response(job)
