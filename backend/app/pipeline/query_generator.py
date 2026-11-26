from typing import Optional, List
from app.schemas.user_profile import UserProfile, CareerPersona
from app.schemas.search_request import (
    SearchRequest,
    SearchLocation,
    IngestionSources,
    SearchConstraints
)

class QueryGenerator:
    """
    Translates a UserProfile and chosen CareerPersona into an actionable
    SearchRequest with multi-location and multi-source expansion.
    """

    @staticmethod
    def generate_search_request(
        profile: UserProfile,
        persona_id: Optional[str] = None,
        date_posted: str = "past-24h",
        max_results_per_location: int = 20
    ) -> SearchRequest:
        # 1. Resolve target persona
        persona: Optional[CareerPersona] = None
        if persona_id:
            persona = profile.get_persona(persona_id)
        if not persona:
            persona = profile.get_primary_persona()
        
        if not persona:
            raise ValueError("UserProfile contains no career personas to derive queries from.")

        # 2. Extract search terms
        query_terms = persona.get_search_query_titles()

        # 3. Extract and map active locations
        target_locations: List[SearchLocation] = []
        for loc in profile.get_active_search_locations():
            is_remote = "remote" in [m.lower() for m in loc.work_modes] or loc.country.lower() == "remote"
            target_locations.append(
                SearchLocation(
                    city=loc.city,
                    country=loc.country,
                    work_modes=loc.work_modes,
                    is_remote=is_remote
                )
            )

        # Fallback if no locations were marked active
        if not target_locations:
            target_locations.append(
                SearchLocation(
                    city=profile.residence_and_mobility.current_residence.get("city", "Cairo"),
                    country=profile.residence_and_mobility.current_residence.get("country", "Egypt"),
                    work_modes=["Remote", "Hybrid"],
                    is_remote=False
                )
            )

        # 4. Derive seniority filter
        seniority = [persona.seniority_level]
        if persona.seniority_level.lower() == "mid-level":
            seniority.append("Senior")
        elif persona.seniority_level.lower() == "entry-level":
            seniority.append("Junior")

        # 5. Derive constraints
        top_skills = persona.skills_and_tools.core_skills[:3]
        constraints = SearchConstraints(
            max_results_per_source_per_location=max_results_per_location,
            exclude_keywords=["unpaid", "internship", "volunteer"],
            must_have_skills=top_skills
        )

        return SearchRequest(
            persona_id=persona.persona_id,
            derived_from_persona=True,
            query_terms=query_terms,
            target_locations=target_locations,
            seniority_filter=seniority,
            date_posted_filter=date_posted,
            enabled_sources=IngestionSources(
                enable_linkedin=True,
                enable_linkedin_posts=True,
                enable_wuzzuf=True,
                enable_company_ats=True,
                enable_indeed=False
            ),
            constraints=constraints
        )
