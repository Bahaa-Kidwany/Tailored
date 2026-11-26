from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

# --- CV Fit Schemas ---

class BulletDiff(BaseModel):
    section: str = "experience"
    original_bullet: str
    tailored_bullet: str
    rationale: str = ""


class CvSectionItem(BaseModel):
    section_key: str = Field(description="Canonical key or custom identifier for the section, e.g. profile, experience, skills, projects, education")
    section_title: str = Field(description="Exact section heading rendered in the CV")
    is_mandatory: bool = Field(default=False, description="True if this section is strictly mandatory for every CV")
    rationale: str = Field(default="", description="Why this section was selected and positioned here for the target role")
    structure_directive: str = Field(default="", description="How items/skills/experiences inside this section are structured")


class CvSectionPlan(BaseModel):
    mandatory_sections_satisfied: bool = True
    enforced_mandatory_keys: list[str] = Field(
        default_factory=lambda: ["header", "profile", "skills", "education"]
    )
    section_order: list[str] = Field(default_factory=list)
    sections: list[CvSectionItem] = Field(default_factory=list)
    skills_structure_strategy: str = ""
    experience_structure_strategy: str = ""
    overall_structure_rationale: str = ""

class CvFitCreateRequest(BaseModel):
    """
    Request to tailor a CV.
    Can reference an existing job discovered in Phase 2 via `job_id`,
    or provide job details ad-hoc.
    If `base_cv_latex` is omitted, it will be synthesized from `profile_id`.
    """
    profile_id: Optional[int] = Field(default=None, description="ID of the user profile")
    persona_id: Optional[str] = Field(default=None, description="Active career persona ID")
    base_cv_latex: Optional[str] = Field(default=None, description="Original LaTeX document source (optional if profile_id provided)")
    job_id: Optional[int] = Field(default=None, description="ID of a discovered job in the database")
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description_text: Optional[str] = None
    company_about_text: Optional[str] = None
    company_website_url: Optional[str] = None
    location: Optional[str] = None
    location_type: Optional[str] = None
    fit_score: Optional[float] = None
    parsed_skills: list[str] = Field(default_factory=list)
    user_comments: Optional[str] = None

class CvFitFileDescriptor(BaseModel):
    kind: Literal["tex", "pdf"]
    filename: str
    download_path: str
    artifact_path: Optional[str] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None

class CvFitSummaryResponse(BaseModel):
    doc_id: str
    profile_id: Optional[int] = None
    persona_id: Optional[str] = None
    job_id: Optional[int] = None
    status: str
    tailoring_applied: bool = False
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website_url: Optional[str] = None
    job_description_text: Optional[str] = None
    location: Optional[str] = None
    location_type: Optional[str] = None
    fit_score: Optional[float] = None
    parsed_skills: list[str] = Field(default_factory=list)
    compile_status: str
    notes_count: int = 0
    bullet_diffs_count: int = 0
    files: list[CvFitFileDescriptor] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @property
    def cv_fit_id(self) -> str:
        return self.doc_id

class CvFitDetailResponse(BaseModel):
    doc_id: str
    profile_id: Optional[int] = None
    persona_id: Optional[str] = None
    job_id: Optional[int] = None
    status: str
    generation_mode: Optional[str] = None
    tailoring_applied: bool = False
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website_url: Optional[str] = None
    company_about_text: Optional[str] = None
    job_description_text: Optional[str] = None
    location: Optional[str] = None
    location_type: Optional[str] = None
    fit_score: Optional[float] = None
    parsed_skills: list[str] = Field(default_factory=list)
    user_comments: Optional[str] = None
    compile_status: str
    base_cv_tex_sha256: str
    base_latex_content: Optional[str] = None
    tailored_latex_content: Optional[str] = None
    section_plan: Optional[CvSectionPlan] = None
    bullet_diffs: list[BulletDiff] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    files: list[CvFitFileDescriptor] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @property
    def cv_fit_id(self) -> str:
        return self.doc_id

# --- Cover Letter Schemas ---

class CoverLetterCreateRequest(BaseModel):
    """
    Request to generate a targeted cover letter.
    Can reference an existing job via `job_id`, or provide job details directly.
    """
    base_cv_text: str = Field(min_length=1, description="Candidate skills or base CV text summary")
    job_id: Optional[int] = Field(default=None, description="ID of a discovered job in the database")
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description_text: Optional[str] = None
    company_website_url: Optional[str] = None
    tone: str = "confident_professional"

class CoverLetterResponse(BaseModel):
    doc_id: str
    job_id: Optional[int] = None
    subject_line: str
    body_markdown: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    created_at: datetime

    @property
    def letter_id(self) -> str:
        return self.doc_id
