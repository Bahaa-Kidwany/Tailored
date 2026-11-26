"""
Re-export domain models from app.models.job and app.models.document for backward compatibility.
"""
from app.models.job import (
    RawJob,
    ParsedJob,
    UserProfile,
    MetricScore,
    JobEvaluation,
    JobDB,
)
from app.models.profile import (
    UserProfileDB,
    ContactNumberDB,
    TargetLocationDB,
    CareerPersonaDB,
    EducationDB,
    LanguageDB,
    assemble_user_profile_schema,
)

__all__ = [
    "RawJob",
    "ParsedJob",
    "MetricScore",
    "JobEvaluation",
    "JobDB",
    "UserProfile",
    "UserProfileDB",
    "ContactNumberDB",
    "TargetLocationDB",
    "CareerPersonaDB",
    "EducationDB",
    "LanguageDB",
    "assemble_user_profile_schema",
]

