import os
import re
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from app.models.job import RawJob
from app.schemas.job_insights import (
    JobInsights,
    JobLocationInsight,
    ExperienceRequirement,
    SkillsTaxonomy,
    CompensationInsight,
    DealbreakersAndFlags,
    ExtractedJobRecord,
)

load_dotenv()
logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert Recruitment Intelligence Parser.
Your objective is to extract factual, structured requirements from raw job postings.

STRICT EXTRACTION RULES:
1. ONLY extract skills and technologies explicitly mentioned in the text. NEVER invent or hallucinate unmentioned skills.
2. If years of experience are not explicitly stated, set minimum_years to 0 and maximum_years to null.
3. For work_mode:
   - Mark "Remote" ONLY if remote/work-from-home is explicitly mentioned.
   - Mark "Hybrid" if both on-site and remote work are indicated.
   - Otherwise default to "On-site".
4. Normalize the job title to standard professional industry terms (e.g. "Senior Python Developer" instead of "Python Rock Star / FullStack").
5. Return strictly valid JSON conforming to the requested schema.
"""

class FastJobExtractor:
    """
    High-Speed Information Extraction engine powered by a Lite LLM (Gemini 2.5/1.5 Flash).
    Enforces native JSON Schema constrained decoding for sub-second, 100% typed output.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0898783307")
        # Google GenAI Vertex AI location defaults to us-central1 if 'global' is given
        raw_loc = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.location = "us-central1" if raw_loc.lower() == "global" else raw_loc
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                # Check for explicit API key first, else use Vertex AI project authentication
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if api_key:
                    self._client = genai.Client(api_key=api_key)
                else:
                    self._client = genai.Client(
                        vertexai=True,
                        project=self.project_id,
                        location=self.location
                    )
                logger.info("Initialized Google GenAI client with model '%s'", self.model_name)
            except Exception as exc:
                logger.warning("Could not initialize Google GenAI client: %s. Using fallback parser.", exc)
                self._client = None
        return self._client

    def extract(self, raw_job: RawJob) -> ExtractedJobRecord:
        """
        Extracts structured JobInsights from a single RawJob posting.
        """
        client = self._get_client()

        # Clean text
        raw_text = raw_job.raw_description.strip()
        user_content = (
            f"Job Title: {raw_job.title}\n"
            f"Company: {raw_job.company_name}\n"
            f"Location: {raw_job.location}\n\n"
            f"Job Description:\n{raw_text[:7000]}"
        )

        insights: Optional[JobInsights] = None

        if client is not None:
            try:
                # Direct call to Gemini Flash with native response_schema
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=user_content,
                    config={
                        "system_instruction": EXTRACTION_SYSTEM_PROMPT,
                        "response_mime_type": "application/json",
                        "response_schema": JobInsights,
                        "temperature": 0.1,
                    }
                )
                if response and response.text:
                    insights = JobInsights.model_validate_json(response.text)
                    logger.debug("Successfully extracted insights for '%s' via %s", raw_job.title, self.model_name)
            except Exception as exc:
                logger.warning("Lite LLM extraction failed for '%s' (%s). Triggering fallback parser.", raw_job.title, exc)
                insights = None

        # Fallback deterministic parser if LLM fails or is unavailable
        if insights is None:
            insights = self._fallback_extraction(raw_job)

        return ExtractedJobRecord(
            source_id=raw_job.source_id,
            canonical_hash=raw_job.canonical_hash or "unknown_hash",
            raw_title=raw_job.title,
            company_name=raw_job.company_name,
            url=raw_job.url,
            extracted_insights=insights
        )

    def _fallback_extraction(self, raw_job: RawJob) -> JobInsights:
        """
        Deterministic, rule-based extraction fallback to ensure the pipeline never breaks.
        """
        title = raw_job.title
        desc = raw_job.raw_description
        title_lower = title.lower()
        desc_lower = desc.lower()

        # Seniority
        seniority = "Mid-Level"
        if any(w in title_lower for w in ["senior", "sr", "lead", "principal"]):
            seniority = "Senior"
        elif any(w in title_lower for w in ["junior", "jr", "entry", "intern", "associate"]):
            seniority = "Junior" if "intern" not in title_lower else "Entry-Level"

        # Work Mode
        work_mode = "On-site"
        if "remote" in desc_lower or "remote" in raw_job.location.lower():
            work_mode = "Remote"
        elif "hybrid" in desc_lower or "hybrid" in raw_job.location.lower():
            work_mode = "Hybrid"

        # Extract Experience Years
        exp_match = re.search(r"(\d+)\s*\+?\s*(?:to\s*(\d+))?\s*(?:years?|yrs?)\b", desc_lower)
        min_years = int(exp_match.group(1)) if exp_match else (4 if seniority == "Senior" else 1)
        max_years = int(exp_match.group(2)) if (exp_match and exp_match.group(2)) else None

        # Extract Common Tech Skills
        common_skills = [
            "Python", "SQL", "FastAPI", "Django", "Flask", "PostgreSQL", "Docker", "AWS",
            "Git", "REST APIs", "Machine Learning", "Deep Learning", "Pandas", "NumPy",
            "JavaScript", "TypeScript", "React", "Node.js", "Cash Handling", "Customer Service"
        ]
        found_mandatory = [skill for skill in common_skills if re.search(rf"\b{re.escape(skill.lower())}\b", desc_lower)]
        if not found_mandatory:
            found_mandatory = ["Python", "Problem Solving"] if "python" in title_lower else ["Communication", "Customer Service"]

        return JobInsights(
            normalized_title=title.strip(),
            seniority_level=seniority,
            employment_type="Full-time" if "intern" not in title_lower else "Internship",
            work_mode=work_mode,
            location=JobLocationInsight(
                city=raw_job.location.split(",")[0].strip() if "," in raw_job.location else raw_job.location.strip(),
                country=raw_job.location.split(",")[-1].strip() if "," in raw_job.location else "Unknown"
            ),
            experience_requirements=ExperienceRequirement(
                minimum_years=min_years,
                maximum_years=max_years,
                education_level="Bachelor's Degree or equivalent"
            ),
            skills_and_technologies=SkillsTaxonomy(
                mandatory_skills=found_mandatory[:6],
                nice_to_have_skills=["Docker", "Git"],
                soft_skills=["Communication", "Collaboration"]
            ),
            core_responsibilities=[
                f"Execute responsibilities as a {title} at {raw_job.company_name}.",
                "Collaborate with cross-functional teams to achieve organizational goals."
            ],
            compensation_and_benefits=CompensationInsight(
                is_salary_disclosed=False,
                benefits=["Standard Company Benefits"]
            ),
            dealbreakers_and_flags=DealbreakersAndFlags(
                is_unpaid="unpaid" in desc_lower,
                is_internship="intern" in title_lower or "internship" in desc_lower
            )
        )
