from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchLocation(BaseModel):
    city: str
    country: str
    work_modes: List[str] = Field(default_factory=lambda: ["Remote", "Hybrid"])
    is_remote: bool = False

    @property
    def query_string(self) -> str:
        if self.country.lower() in ["remote", "global"] or self.city.lower() in ["remote", "worldwide"]:
            return "Remote"
        return f"{self.city}, {self.country}".strip(", ")

class IngestionSources(BaseModel):
    enable_linkedin: bool = True
    enable_linkedin_posts: bool = True
    enable_wuzzuf: bool = True
    enable_company_ats: bool = True
    enable_indeed: bool = False

class SearchConstraints(BaseModel):
    max_results_per_source_per_location: int = 2
    apify_max_items_per_actor: int = 2
    exclude_keywords: List[str] = Field(default_factory=lambda: ["unpaid", "internship", "volunteer"])
    must_have_skills: List[str] = Field(default_factory=list)

class SearchRequest(BaseModel):
    persona_id: str
    derived_from_persona: bool = True
    query_terms: List[str] = Field(default_factory=list)
    target_locations: List[SearchLocation] = Field(default_factory=list)
    seniority_filter: List[str] = Field(default_factory=lambda: ["Mid-Level", "Senior"])
    date_posted_filter: str = "past-24h"
    enabled_sources: IngestionSources = Field(default_factory=IngestionSources)
    constraints: SearchConstraints = Field(default_factory=SearchConstraints)
