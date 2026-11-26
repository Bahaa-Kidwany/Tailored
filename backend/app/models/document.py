from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field as DBField

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class GeneratedDocumentDB(SQLModel, table=True):
    """
    Persisted generated documents (Tailored CVs and Cover Letters)
    linked to jobs and stored in PostgreSQL / SQLite.
    """
    __tablename__ = "generated_documents"

    id: Optional[int] = DBField(default=None, primary_key=True)
    doc_id: str = DBField(index=True, unique=True)
    doc_type: str = DBField(default="tailored_cv", index=True)  # "tailored_cv" | "cover_letter"
    
    # User Profile & Persona linkage
    profile_id: Optional[int] = DBField(default=None, foreign_key="user_profiles.id", index=True)
    persona_id: Optional[str] = DBField(default=None, index=True)
    
    # Optional link to a JobDB record from Phase 2
    job_id: Optional[int] = DBField(default=None, index=True)
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website_url: Optional[str] = None
    company_about_text: Optional[str] = None
    job_description_text: Optional[str] = None
    location: Optional[str] = None
    location_type: Optional[str] = None
    fit_score: Optional[float] = None
    parsed_skills_json: Optional[str] = None
    
    status: str = DBField(default="completed")
    generation_mode: Optional[str] = DBField(default="llm")
    tailoring_applied: bool = DBField(default=False)
    
    # Document storage paths and artifacts
    artifact_folder: Optional[str] = None
    generated_tex_path: Optional[str] = None
    generated_pdf_path: Optional[str] = None
    generated_tex_sha256: Optional[str] = None
    generated_pdf_sha256: Optional[str] = None
    generated_tex_size_bytes: Optional[int] = None
    generated_pdf_size_bytes: Optional[int] = None
    compile_status: str = DBField(default="pending")  # "ok" | "failed" | "not_installed"
    
    # Content storage for text / markdown / LaTeX
    content_text: Optional[str] = None
    base_latex_content: Optional[str] = None
    tailored_latex_content: Optional[str] = None
    
    # Base CV reference
    base_cv_tex_sha256: Optional[str] = None
    user_comments: Optional[str] = None
    
    # Review & analysis metadata stored as JSON
    raw_metadata_json: Optional[str] = None
    
    created_at: datetime = DBField(default_factory=utc_now)
    updated_at: datetime = DBField(default_factory=utc_now)

    @property
    def cv_fit_id(self) -> str:
        """Backward-compatible property for legacy references."""
        return self.doc_id
