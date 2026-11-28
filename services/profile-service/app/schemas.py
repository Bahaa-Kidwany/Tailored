import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContactNumber(BaseModel):
    country_code: str = "EG"
    dial_code: str = "+20"
    phone_number: str = ""
    is_primary: bool = False
    label: str = "Mobile"


class PersonalInfo(BaseModel):
    full_name: str = ""
    primary_email: str = ""
    contact_numbers: List[ContactNumber] = Field(default_factory=list)
    links: Dict[str, str] = Field(default_factory=dict)

    def get_contact_for_country(self, country_code: str) -> Optional[ContactNumber]:
        normalized_target = country_code.upper().strip()
        for contact in self.contact_numbers:
            if contact.country_code.upper() == normalized_target:
                return contact
        for contact in self.contact_numbers:
            if contact.is_primary:
                return contact
        return self.contact_numbers[0] if self.contact_numbers else None


class TargetLocation(BaseModel):
    location_id: str = Field(default_factory=lambda: f"loc_{uuid.uuid4().hex[:8]}")
    city: str = "Cairo"
    country: str = "Egypt"
    work_modes: List[str] = Field(default_factory=lambda: ["Remote", "Hybrid"])
    is_active_for_search: bool = True


class ResidenceAndMobility(BaseModel):
    current_residence: Dict[str, str] = Field(default_factory=lambda: {"city": "Cairo", "country": "Egypt"})
    willing_to_relocate: bool = True
    target_locations: List[TargetLocation] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    grade_or_gpa: Optional[str] = None


class LanguageProficiency(BaseModel):
    language: str
    proficiency: str = "Professional"


class SkillsAndTools(BaseModel):
    core_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_libraries: List[str] = Field(default_factory=list)
    tools_and_platforms: List[str] = Field(default_factory=list)

    def all_skills_flat(self) -> List[str]:
        return (
            self.core_skills
            + self.programming_languages
            + self.frameworks_and_libraries
            + self.tools_and_platforms
        )


class ExperienceHighlight(BaseModel):
    company: str
    role: str
    start_date: str = ""
    end_date: str = "Present"
    location: str = ""
    achievements: List[str] = Field(default_factory=list)


class FeaturedProject(BaseModel):
    name: str
    tech_stack: List[str] = Field(default_factory=list)
    summary: str = ""
    link: Optional[str] = None


class Certification(BaseModel):
    name: str
    issuer: str = ""
    issue_date: Optional[str] = None


class CustomSectionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    subtitle: Optional[str] = None
    date: Optional[str] = None
    location_or_link: Optional[str] = None
    description: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)


class CustomSection(BaseModel):
    id: str = Field(default_factory=lambda: f"sec_{str(uuid.uuid4())[:8]}")
    section_title: str
    section_type: str = "items"
    content_text: Optional[str] = None
    items: List[CustomSectionItem] = Field(default_factory=list)


class CareerPersona(BaseModel):
    persona_id: str = Field(default_factory=lambda: f"persona_{uuid.uuid4().hex[:8]}")
    target_title: str
    alternative_titles: List[str] = Field(default_factory=list)
    is_primary: bool = False
    seniority_level: str = "Mid-Level"
    years_of_experience: int = 0
    summary_bio: str = ""
    skills_and_tools: SkillsAndTools = Field(default_factory=SkillsAndTools)
    experience_highlights: List[ExperienceHighlight] = Field(default_factory=list)
    featured_projects: List[FeaturedProject] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)

    def get_search_query_titles(self) -> List[str]:
        titles = [self.target_title]
        for alt in self.alternative_titles:
            if alt not in titles:
                titles.append(alt)
        return titles


class UserProfile(BaseModel):
    version: str = "1.1.0"
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    residence_and_mobility: ResidenceAndMobility = Field(default_factory=ResidenceAndMobility)
    education: List[Education] = Field(default_factory=list)
    languages: List[LanguageProficiency] = Field(default_factory=list)
    career_personas: List[CareerPersona] = Field(default_factory=list)
    custom_sections: List[CustomSection] = Field(default_factory=list)

    def get_primary_persona(self) -> Optional[CareerPersona]:
        for p in self.career_personas:
            if p.is_primary:
                return p
        return self.career_personas[0] if self.career_personas else None

    def get_persona(self, persona_id: str) -> Optional[CareerPersona]:
        for p in self.career_personas:
            if p.persona_id == persona_id:
                return p
        return None

    def get_active_search_locations(self) -> List[TargetLocation]:
        return [loc for loc in self.residence_and_mobility.target_locations if loc.is_active_for_search]


class CvSectionItem(BaseModel):
    section_key: str
    section_title: str
    is_mandatory: bool = False
    rationale: str = ""
    structure_directive: str = ""


class CvSectionPlan(BaseModel):
    mandatory_sections_satisfied: bool = True
    enforced_mandatory_keys: List[str] = Field(
        default_factory=lambda: ["header", "profile", "skills", "education"]
    )
    section_order: List[str] = Field(default_factory=list)
    sections: List[CvSectionItem] = Field(default_factory=list)
    skills_structure_strategy: str = ""
    experience_structure_strategy: str = ""
    overall_structure_rationale: str = ""
