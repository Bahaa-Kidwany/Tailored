import re
from typing import List
from app.models.job import RawJob, ParsedJob

COMMON_SKILLS_TAXONOMY = [
    "Python", "SQL", "FastAPI", "Docker", "PostgreSQL", "PyTorch", "TensorFlow",
    "Machine Learning", "Deep Learning", "AWS", "GCP", "Azure", "Kubernetes",
    "React", "TypeScript", "JavaScript", "Node.js", "Next.js", "TailwindCSS",
    "Redis", "Kafka", "Git", "CI/CD", "Linux", "REST APIs", "GraphQL",
    "Pandas", "NumPy", "Scikit-Learn", "NLP", "Computer Vision", "LLMs", "RAG",
    "Tableau", "Power BI", "Excel", "Data Modeling", "ETL", "Spark", "Databricks",
    "Go", "Golang", "Java", "C++", "C#", ".NET", "Rust", "MongoDB", "MySQL",
    "Microservices", "System Design", "Agile", "Scrum", "Jira", "Terraform"
]

class JobExtractor:
    """
    Handles Information Extraction (IE) converting unstructured RawJob description
    into structured ParsedJob. Uses fast rule-based taxonomy extraction with LLM client support.
    """
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def extract(self, raw_job: RawJob) -> ParsedJob:
        """
        Parses raw description to extract required skills, experience, location type, and responsibilities.
        """
        title = raw_job.title
        desc = raw_job.raw_description
        title_lower = title.lower()
        desc_lower = desc.lower()

        # 1. Seniority
        is_senior = any(w in title_lower for w in ["senior", "sr", "lead", "principal", "staff", "head", "director"])

        # 2. Location Type
        location_type = "On-site"
        combined_text = f"{raw_job.location} {desc}".lower()
        if "remote" in combined_text or "work from home" in combined_text or "wfh" in combined_text:
            location_type = "Remote"
        elif "hybrid" in combined_text or "flexible" in combined_text:
            location_type = "Hybrid"

        # 3. Minimum Years of Experience
        min_years = 4 if is_senior else 1
        exp_match = re.search(r"(\d+)\s*\+?\s*(?:to\s*(\d+))?\s*(?:years?|yrs?)\b", desc_lower)
        if exp_match:
            try:
                min_years = int(exp_match.group(1))
            except ValueError:
                pass

        # 4. Extract Real Skills Mentioned in Description
        found_skills: List[str] = []
        for skill in COMMON_SKILLS_TAXONOMY:
            # Word boundary regex check
            pattern = rf"(?<![a-zA-Z0-9]){re.escape(skill.lower())}(?![a-zA-Z0-9])"
            if re.search(pattern, desc_lower) or re.search(pattern, title_lower):
                found_skills.append(skill)

        # Fallbacks if text was brief or non-standard
        if not found_skills:
            if any(term in title_lower for term in ["data", "ml", "ai", "scientist"]):
                found_skills = ["Python", "SQL", "Machine Learning", "PyTorch"]
            elif "analyst" in title_lower or "analytics" in title_lower:
                found_skills = ["SQL", "Tableau", "Power BI", "Excel", "Python"]
            elif any(term in title_lower for term in ["frontend", "react", "web"]):
                found_skills = ["React", "TypeScript", "JavaScript", "HTML/CSS"]
            else:
                found_skills = ["Python", "FastAPI", "SQL", "Docker"]

        # Split into required (up to 5) and nice-to-have
        required = found_skills[:5]
        nice_to_have = found_skills[5:10]

        # 5. Extract Responsibilities or synthesize clean bullets
        responsibilities = []
        bullet_lines = [
            line.strip().lstrip("•-* ").strip()
            for line in desc.splitlines()
            if len(line.strip()) > 20 and any(line.strip().startswith(bullet) for bullet in ["•", "-", "*", "1.", "2.", "3."])
        ]
        if bullet_lines:
            responsibilities = bullet_lines[:4]
        else:
            responsibilities = [
                f"Design, build, and optimize systems as a {title} at {raw_job.company_name}.",
                f"Collaborate with engineering and product teams to deliver high-quality solutions.",
                f"Apply best practices in {required[0] if required else 'software engineering'} and continuous delivery.",
            ]

        return ParsedJob(
            required_skills=required,
            nice_to_have_skills=nice_to_have,
            minimum_years_experience=min_years,
            location_type=location_type,
            is_senior_role=is_senior,
            core_responsibilities=responsibilities,
        )
