from typing import List, Optional
from pydantic import BaseModel, Field

class JobLocationInsight(BaseModel):
    city: str = Field(default="Unknown", description="City of the position if specified, or Remote")
    country: str = Field(default="Unknown", description="Country of the position if specified")
    is_relocation_offered: bool = Field(default=False, description="True if company explicitly mentions relocation assistance")
    geography_restrictions: Optional[str] = Field(default=None, description="Any residency, timezone, or regional restrictions")

class ExperienceRequirement(BaseModel):
    minimum_years: int = Field(default=0, description="Minimum required years of experience, or 0 if not specified")
    maximum_years: Optional[int] = Field(default=None, description="Upper bound of years of experience if mentioned")
    education_level: Optional[str] = Field(default=None, description="Required education level (e.g. Bachelor's in CS, High School, etc.)")

class SkillsTaxonomy(BaseModel):
    mandatory_skills: List[str] = Field(default_factory=list, description="Core technical or functional skills explicitly required")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Bonus, preferred, or nice-to-have skills")
    soft_skills: List[str] = Field(default_factory=list, description="Interpersonal or communication skills mentioned")

class CompensationInsight(BaseModel):
    is_salary_disclosed: bool = Field(default=False, description="True if compensation is mentioned in the job description")
    currency: Optional[str] = Field(default=None, description="Currency code (e.g. USD, EGP, SAR, EUR)")
    min_salary: Optional[float] = Field(default=None, description="Minimum disclosed salary")
    max_salary: Optional[float] = Field(default=None, description="Maximum disclosed salary")
    benefits: List[str] = Field(default_factory=list, description="Key perks & benefits mentioned")

class DealbreakersAndFlags(BaseModel):
    is_unpaid: bool = Field(default=False, description="True if this is an unpaid role or volunteer")
    is_internship: bool = Field(default=False, description="True if the role is explicitly an internship")
    requires_visa_sponsorship: bool = Field(default=False, description="True if company requires existing work authorization")

class JobInsights(BaseModel):
    normalized_title: str = Field(description="Standardized industry professional title (e.g. Senior Python Developer)")
    seniority_level: str = Field(default="Mid-Level", description="One of: Entry-Level, Junior, Mid-Level, Senior, Lead, Director")
    employment_type: str = Field(default="Full-time", description="One of: Full-time, Part-time, Contract, Internship")
    work_mode: str = Field(default="On-site", description="One of: Remote, Hybrid, On-site")
    location: JobLocationInsight = Field(default_factory=JobLocationInsight)
    experience_requirements: ExperienceRequirement = Field(default_factory=ExperienceRequirement)
    skills_and_technologies: SkillsTaxonomy = Field(default_factory=SkillsTaxonomy)
    core_responsibilities: List[str] = Field(default_factory=list, description="3 to 5 clear bullet points of daily duties")
    compensation_and_benefits: CompensationInsight = Field(default_factory=CompensationInsight)
    dealbreakers_and_flags: DealbreakersAndFlags = Field(default_factory=DealbreakersAndFlags)

class ExtractedJobRecord(BaseModel):
    source_id: str
    canonical_hash: str
    raw_title: str
    company_name: str
    url: str
    extracted_insights: JobInsights
