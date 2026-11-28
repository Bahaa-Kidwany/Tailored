import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

SKILL_ALIASES = {
    "pytorch": {"deep learning", "neural networks", "ml"},
    "tensorflow": {"deep learning", "ml"},
    "fastapi": {"python", "rest api", "backend"},
    "postgresql": {"sql", "postgres", "rdbms"},
    "docker": {"containers", "devops"},
    "aws ecs": {"aws", "docker", "cloud"},
    "kubernetes": {"k8s", "containers", "orchestration"},
    "scikit-learn": {"machine learning", "ml", "data science"},
}

COMMON_SKILLS_VOCAB = [
    "Python",
    "PyTorch",
    "TensorFlow",
    "SQL",
    "PostgreSQL",
    "FastAPI",
    "Docker",
    "Kubernetes",
    "AWS",
    "AWS ECS",
    "HuggingFace",
    "LLMs",
    "RAG",
    "Kafka",
    "Ray",
    "Spark",
    "Airflow",
    "Redis",
    "React",
    "TypeScript",
    "A/B Testing",
    "Power BI",
    "Metabase",
    "Data Analytics",
    "Machine Learning",
]


def compute_canonical_hash(company_name: str, title: str, location: str) -> str:
    norm_company = re.sub(r"[^a-z0-9]", "", (company_name or "").lower())
    norm_title = re.sub(r"[^a-z0-9]", "", (title or "").lower())
    norm_loc = re.sub(r"[^a-z0-9]", "", (location or "").lower())
    return hashlib.sha256(f"{norm_company}:{norm_title}:{norm_loc}".encode("utf-8")).hexdigest()


def extract_recruiter_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    valid = [e for e in emails if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"))]
    return valid[0] if valid else None


def extract_skills_and_meta(raw_description: str, title: str = "") -> Tuple[List[str], List[str], int, str]:
    text_low = f"{title}\n{raw_description}".lower()
    found: List[str] = []
    for sk in COMMON_SKILLS_VOCAB:
        if re.search(rf"(?<![a-z0-9]){re.escape(sk.lower())}(?![a-z0-9])", text_low):
            found.append(sk)
    if not found:
        found = ["Python", "SQL"]

    yrs_m = re.search(r"(\d+)\s*\+?\s*(?:years|yrs)\b", text_low)
    min_years = int(yrs_m.group(1)) if yrs_m else 2

    if "remote" in text_low:
        work_mode = "Remote"
    elif "hybrid" in text_low:
        work_mode = "Hybrid"
    else:
        work_mode = "On-site"

    sentences = [s.strip("•- \t\n") for s in re.split(r"[\n.;]+", raw_description) if len(s.strip()) > 24]
    responsibilities = sentences[:4]
    return found, responsibilities, min_years, work_mode


def _persona_all_skills(persona: Dict[str, Any]) -> List[str]:
    st = persona.get("skills_and_tools") or {}
    combined: List[str] = []
    for key in ("core_skills", "programming_languages", "frameworks_and_libraries", "tools_and_platforms"):
        combined.extend(st.get(key) or [])
    for proj in persona.get("featured_projects") or []:
        combined.extend(proj.get("tech_stack") or [])
    return combined


def _expand_skill_set(skills: List[str]) -> set[str]:
    out = {s.lower().strip() for s in skills if s}
    for s in list(out):
        out.update(SKILL_ALIASES.get(s, set()))
    return out


def score_job_against_persona(
    *,
    job_title: str,
    job_location: str,
    job_work_mode: str,
    job_skills: List[str],
    job_min_years: int,
    job_description: str,
    persona: Dict[str, Any],
    mobility: Dict[str, Any],
) -> Dict[str, Any]:
    cand_skills_raw = _persona_all_skills(persona)
    cand_skills = _expand_skill_set(cand_skills_raw)
    req_skills = [s for s in job_skills if s] or ["Python"]

    matched: List[str] = []
    missing: List[str] = []
    for req in req_skills:
        req_l = req.lower().strip()
        if req_l in cand_skills or any(req_l in cs or cs in req_l for cs in cand_skills):
            matched.append(req)
        else:
            missing.append(req)
    skill_score = (len(matched) / max(len(req_skills), 1)) * 100.0

    # 2. Title Alignment (20%)
    target_titles = [persona.get("target_title", "")] + (persona.get("alternative_titles") or [])
    job_tokens = set(re.findall(r"[a-z0-9]+", job_title.lower()))
    best_title_sim = 0.0
    for tt in target_titles:
        tt_tokens = set(re.findall(r"[a-z0-9]+", tt.lower()))
        if not tt_tokens:
            continue
        inter = len(job_tokens & tt_tokens)
        sim = inter / max(len(tt_tokens | job_tokens) * 0.65, 1)
        best_title_sim = max(best_title_sim, min(1.0, sim))
    title_score = max(45.0, best_title_sim * 100.0) if target_titles else 70.0

    # 3. Continuous Experience Proximity (20% — Zero-Drop ADR-008)
    cand_years = int(persona.get("years_of_experience") or 2)
    req_years = max(int(job_min_years or 0), 1)
    if cand_years >= req_years:
        exp_score = 100.0
    else:
        gap = req_years - cand_years
        exp_score = max(40.0, 100.0 - gap * 14.0)

    # 4. Project & Domain Relevance (15%)
    jd_tokens = set(re.findall(r"[a-z0-9]{3,}", job_description.lower()))
    proj_text = " ".join(
        [persona.get("summary_bio", "")]
        + [p.get("summary", "") for p in (persona.get("featured_projects") or [])]
        + [" ".join(e.get("achievements") or []) for e in (persona.get("experience_highlights") or [])]
    ).lower()
    proj_tokens = set(re.findall(r"[a-z0-9]{3,}", proj_text))
    overlap = len(jd_tokens & proj_tokens)
    project_score = min(100.0, max(52.0, overlap * 5.5))

    # 5. Location & Work Mode Fit (10%)
    loc_low = job_location.lower()
    willing = bool(mobility.get("willing_to_relocate", True))
    targets = mobility.get("target_locations") or []
    loc_score = 72.0
    if job_work_mode.lower() == "remote":
        loc_score = 96.0
    elif any(
        (t.get("city", "").lower() in loc_low or t.get("country", "").lower() in loc_low)
        and (job_work_mode in (t.get("work_modes") or ["Remote", "Hybrid", "On-site"]))
        for t in targets
    ):
        loc_score = 100.0
    elif willing:
        loc_score = 84.0

    composite = round(
        0.35 * skill_score
        + 0.20 * title_score
        + 0.20 * exp_score
        + 0.15 * project_score
        + 0.10 * loc_score,
        1,
    )
    if composite >= 85.0:
        level = "Exceptional Match"
    elif composite >= 70.0:
        level = "Strong Match"
    elif composite >= 50.0:
        level = "Moderate Fit"
    else:
        level = "Exploratory Fit"

    return {
        "persona_id": persona.get("persona_id", "default"),
        "persona_title": persona.get("target_title", "General Track"),
        "overall_score": composite,
        "match_level": level,
        "matched_skills": matched,
        "missing_skills": missing,
        "dimensions": {
            "technical_skills": {"score": round(skill_score, 1), "weight": 0.35},
            "title_alignment": {"score": round(title_score, 1), "weight": 0.20},
            "experience_proximity": {"score": round(exp_score, 1), "weight": 0.20},
            "project_relevance": {"score": round(project_score, 1), "weight": 0.15},
            "location_mode_fit": {"score": round(loc_score, 1), "weight": 0.10},
        },
    }


def evaluate_job_all_personas(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    personas = profile.get("career_personas") or [
        {
            "persona_id": "default",
            "target_title": "Software & Data Engineer",
            "alternative_titles": [],
            "years_of_experience": 3,
            "summary_bio": "",
            "skills_and_tools": {"core_skills": ["Python", "SQL", "FastAPI", "Docker"]},
        }
    ]
    mobility = profile.get("residence_and_mobility") or {"willing_to_relocate": True, "target_locations": []}
    results = [
        score_job_against_persona(
            job_title=job.get("title", ""),
            job_location=job.get("location", ""),
            job_work_mode=job.get("work_mode", "Hybrid"),
            job_skills=job.get("parsed_skills") or [],
            job_min_years=job.get("min_years", 2),
            job_description=job.get("raw_description", ""),
            persona=p,
            mobility=mobility,
        )
        for p in personas
    ]
    best = max(results, key=lambda r: r["overall_score"])

    strengths = [
        f"Strong coverage on {', '.join(best['matched_skills'][:4])}"
        if best["matched_skills"]
        else "Transferable engineering problem-solving background"
    ]
    opportunities = [
        f"Bridge {', '.join(best['missing_skills'][:2])} by surfacing adjacent production architecture work."
        if best["missing_skills"]
        else "Front-load quantified production metrics matching the top responsibilities."
    ]
    return {
        "best_persona_id": best["persona_id"],
        "best_persona_title": best["persona_title"],
        "overall_score": best["overall_score"],
        "match_level": best["match_level"],
        "matched_skills": best["matched_skills"],
        "missing_skills": best["missing_skills"],
        "dimensions": best["dimensions"],
        "persona_breakdown": results,
        "tailoring_guidance": {
            "key_strengths_to_highlight": strengths,
            "tailoring_opportunities": opportunities,
        },
    }
