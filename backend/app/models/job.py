import json
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field as DBField

import re
import hashlib
from typing import List, Optional, Dict, Any

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def compute_canonical_hash(company_name: str, title: str, location: str) -> str:
    """Computes a deterministic SHA256 canonical hash to deduplicate jobs across sources."""
    norm_company = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
    norm_title = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
    norm_loc = re.sub(r"[^a-zA-Z0-9]", "", location.lower())
    composite = f"{norm_company}:{norm_title}:{norm_loc}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()

# --- Pydantic Domain Models ---

class RawJob(BaseModel):
    """The raw unstructured data fetched from a source (scraper or API)."""
    source_id: str
    title: str
    url: str
    raw_description: str
    company_name: str
    location: str
    source_type: str = "unknown"
    posted_at: Optional[datetime] = None
    canonical_hash: Optional[str] = None
    source_metadata: Dict[str, Any] = PydanticField(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.canonical_hash:
            self.canonical_hash = compute_canonical_hash(
                company_name=self.company_name,
                title=self.title,
                location=self.location
            )

class ParsedJob(BaseModel):
    """The structured data extracted by the LLM from the raw description."""
    required_skills: List[str] = PydanticField(default_factory=list)
    nice_to_have_skills: List[str] = PydanticField(default_factory=list)
    minimum_years_experience: int = 0
    location_type: str = "On-site"  # "Remote", "On-site", "Hybrid"
    is_senior_role: bool = False
    core_responsibilities: List[str] = PydanticField(default_factory=list)

class UserProfile(BaseModel):
    """The user's skills and preferences."""
    target_titles: List[str] = PydanticField(default_factory=list)
    core_skills: List[str] = PydanticField(default_factory=list)
    years_of_experience: int = 0
    preferred_location_type: str = "Remote"

class MetricScore(BaseModel):
    """The individual score for a specific evaluation metric."""
    metric_name: str
    score: float  # 0.0 to 1.0
    weight: float
    reasoning: str

class JobEvaluation(BaseModel):
    """The final evaluation result for a job."""
    raw_job_id: str
    total_score: float  # Percentage out of 100
    metrics: List[MetricScore] = PydanticField(default_factory=list)
    is_passed: bool

# --- SQLModel Database Table ---

class JobDB(SQLModel, table=True):
    """Persisted discovered job that passed the evaluation threshold."""
    __tablename__ = "jobs"

    id: Optional[int] = DBField(default=None, primary_key=True)
    source_id: str = DBField(index=True)
    title: str
    company_name: str
    location: str
    url: str
    raw_description: str
    fit_score: float = DBField(default=0.0)
    
    # Serialized JSON representations
    parsed_job_json: Optional[str] = None
    evaluation_json: Optional[str] = None
    
    created_at: datetime = DBField(default_factory=utc_now)
    updated_at: datetime = DBField(default_factory=utc_now)

    def get_parsed_job(self) -> Optional[ParsedJob]:
        if not self.parsed_job_json:
            return None
        try:
            return ParsedJob.model_validate_json(self.parsed_job_json)
        except Exception:
            return None

    def get_evaluation(self) -> Optional[JobEvaluation]:
        if not self.evaluation_json:
            return None
        try:
            return JobEvaluation.model_validate_json(self.evaluation_json)
        except Exception:
            return None

