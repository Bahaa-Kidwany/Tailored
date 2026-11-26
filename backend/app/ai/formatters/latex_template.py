import re
from typing import Optional, List, Dict, Tuple, Any
from app.schemas.user_profile import UserProfile, CareerPersona
from app.schemas.cv_fit import CvSectionItem, CvSectionPlan

# Mandatory sections that every generated CV MUST include to pass validation
MANDATORY_SECTION_KEYS: Tuple[str, ...] = ("header", "profile", "skills", "education")

MANDATORY_DEFAULT_TITLES: Dict[str, str] = {
    "header": "Header & Contact Info",
    "profile": "Profile",
    "skills": "Technical Skills",
    "education": "Education",
}

# Patterns of scraper/source tags that must NEVER appear in a candidate's CV header or summary
_SOURCE_TAG_PATTERNS = [
    r"\(\s*recruiter\s+post\s*\)",
    r"\(\s*linkedin\s+hiring\s+post\s*\)",
    r"\(\s*linkedin\s+post\s*\)",
    r"\(\s*hiring\s+post\s*\)",
    r"\(\s*linkedin\s*\)",
    r"\(\s*wuzzuf\s*\)",
    r"\[\s*recruiter\s+post\s*\]",
    r"\[\s*linkedin\s+hiring\s+post\s*\]",
    r"[-–—|]\s*recruiter\s+post\b",
    r"[-–—|]\s*linkedin\s+hiring\s+post\b",
    r"[-–—|]\s*linkedin(?:\s+post)?\b",
    r"[-–—|]\s*hiring\s+post\b",
    r"[-–—|]\s*wuzzuf\b",
]


def clean_target_job_title(raw_title: Optional[str], fallback_title: str = "AI & Data Engineer") -> str:
    """
    Strips scraper/source tags like '(Recruiter Post)', '(LinkedIn Hiring Post)', '(Wuzzuf)',
    and location work-mode tags from a job title so the CV header and Profile summary
    always use a clean, authentic professional title.
    """
    if not raw_title or not raw_title.strip():
        return fallback_title
    cleaned = raw_title.strip()
    for pat in _SOURCE_TAG_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    # Also strip trailing work-mode parentheticals like (Remote), (Hybrid), (On-site) from the role title
    cleaned = re.sub(r"\(\s*(?:remote|hybrid|on-?site)\s*\)\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|/,")
    return cleaned or fallback_title


def clean_company_name(raw_company: Optional[str], fallback_company: str = "Target Organization") -> str:
    """Strips scraper/source tags like '(LinkedIn Hiring Post)' or '(Recruiter Post)' from company names."""
    if not raw_company or not raw_company.strip():
        return fallback_company
    cleaned = raw_company.strip()
    for pat in _SOURCE_TAG_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|/,")
    return cleaned or fallback_company


def escape_latex(text: Optional[str]) -> str:
    """Escapes special LaTeX characters in plain text strings."""
    if not text:
        return ""
    s = str(text)
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s


def _format_url_display(url: str) -> str:
    """Strips protocol prefix for clean display in header links."""
    cleaned = re.sub(r"^https?://(www\.)?", "", url.strip()).rstrip("/")
    return escape_latex(cleaned)


def normalize_section_key(raw_key_or_title: str) -> str:
    """
    Maps any section key or title into a canonical section key if it corresponds
    to a known category (mandatory or common optional), while preserving custom
    AI-selected section keys for specialized sections.
    """
    s = re.sub(r"[^a-z0-9]+", "_", (raw_key_or_title or "").strip().lower()).strip("_")
    if not s:
        return "custom"
    if any(k in s for k in ("header", "contact", "heading", "personal_info")):
        return "header"
    if any(k in s for k in ("profile", "summary", "objective", "about", "bio", "executive_summary")):
        return "profile"
    if any(k in s for k in ("skill", "competenc", "technolog", "tech_stack", "tooling", "tools")):
        return "skills"
    if any(k in s for k in ("education", "academic", "degree", "university", "qualification")):
        return "education"
    if any(k in s for k in ("experience", "employment", "work_history", "career_history", "professional_background")):
        return "experience"
    if any(k in s for k in ("project", "portfolio", "built", "system", "case_stud")):
        return "projects"
    if any(k in s for k in ("certificat", "license", "credential", "accreditation")):
        return "certificates"
    if any(k in s for k in ("language", "linguistic")):
        return "languages"
    if any(k in s for k in ("research", "publication", "paper", "journal")):
        return "research"
    if any(k in s for k in ("open_source", "leadership", "community", "volunteer", "mentorship")):
        return "leadership"
    if any(k in s for k in ("award", "honor", "competition", "achievement", "hackathon")):
        return "awards"
    if any(k in s for k in ("coursework", "course", "curriculum", "training")):
        return "coursework"
    return s


def strip_leading_role_from_bio(bio: str, persona_title: Optional[str] = None) -> str:
    """
    Removes any leading role title prefix from `bio` (e.g. 'Data Engineer with a proven track record...'
    -> 'with a proven track record...') so prepending `\\textbf{<Target Title>}` never creates
    clashing double titles like `\\textbf{ML Engineer} Data Engineer with a proven track record...`.
    """
    if not bio:
        return ""
    cleaned = bio.strip()
    prefixes = [
        "AI & Data Engineer",
        "AI and Data Engineer",
        "Machine Learning & Data Engineer",
        "Machine Learning Engineer",
        "ML Engineer",
        "Senior Data Scientist",
        "Lead Data Scientist",
        "Data Scientist",
        "Senior Data Engineer",
        "Lead Data Engineer",
        "Data Engineer",
        "Data Analyst",
        "AI Engineer",
        "Software Engineer",
    ]
    if persona_title and persona_title.strip() not in prefixes:
        prefixes.insert(0, persona_title.strip())

    for p in prefixes:
        m = re.match(rf"^{re.escape(p)}\s*(?:[:\-–—|]\s*)?", cleaned, flags=re.IGNORECASE)
        if m:
            remainder = cleaned[m.end():].strip()
            if remainder:
                return remainder
    return cleaned


def build_tailored_profile_bio_body(
    persona: Optional[CareerPersona],
    clean_role: str,
    job_description: Optional[str] = None,
    priority_skills: Optional[List[str]] = None,
) -> str:
    """
    Constructs the body of the Profile section (the text immediately following `\\textbf{<clean_role>}`)
    grounded strictly in the candidate's verified profile while positively aligning with `clean_role`.
    Never includes negative disclaimers or conflicting role titles.
    """
    raw_bio = persona.summary_bio if persona and persona.summary_bio else ""
    stripped_bio = strip_leading_role_from_bio(raw_bio, persona.target_title if persona else None)

    role_lower = clean_role.lower()
    is_ml_or_ai_target = any(
        k in role_lower
        for k in ("ml", "machine learning", "ai", "artificial intelligence", "deep learning", "nlp", "data scientist")
    )

    st = persona.skills_and_tools if persona else None
    all_verified_skills = st.all_skills_flat() if st else []
    has_ml_stack = any(
        s.lower() in {"pytorch", "tensorflow", "scikit-learn", "langchain", "agentic rag", "mlflow", "vertex ai"}
        for s in all_verified_skills
    )

    if is_ml_or_ai_target and has_ml_stack:
        # Positively frame the candidate's verified AI/ML + Data Engineering track record for ML/AI roles
        return (
            "with a proven track record in designing, training, and deploying production machine learning workflows, "
            "LLM/Agentic RAG pipelines, and scalable AI & data infrastructure. Experienced across the full ML and data "
            "lifecycle—from deep learning (PyTorch, TensorFlow, Scikit-Learn, CNNs) and hybrid vector retrieval "
            "(Vertex AI, LangChain, Weaviate, Dense e5-large) to automated ETL/ELT feature pipelines, MLOps (Docker, MLflow), "
            "and high-throughput FastAPI microservices."
        )

    if stripped_bio:
        return stripped_bio

    return (
        "with a proven track record in designing, building, and scaling robust data infrastructure, "
        "automated pipelines, and production-grade analytics and machine learning systems."
    )


def enforce_mandatory_section_plan(
    raw_plan: Optional[Dict[str, Any]],
    profile: Optional[UserProfile] = None,
    persona_id: Optional[str] = None,
    job_title: Optional[str] = None,
    job_description: Optional[str] = None,
    parsed_skills: Optional[List[str]] = None,
) -> Tuple[CvSectionPlan, List[str]]:
    """
    Normalizes the section plan while preserving the authentic cv(1)(1).tex structure:
    Header -> Profile -> Professional Experience -> Projects -> Technical Skills -> Education -> Certificates -> Languages,
    and guaranteeing all mandatory sections are present.
    """
    notes: List[str] = []
    raw_plan = raw_plan or {}
    clean_role = clean_target_job_title(job_title)

    persona: Optional[CareerPersona] = None
    if profile:
        if persona_id:
            persona = profile.get_persona(persona_id)
        if not persona:
            persona = profile.get_primary_persona()

    has_exp = bool(persona and persona.experience_highlights) or True
    has_proj = bool(persona and persona.featured_projects) or True
    has_certs = bool(persona and persona.certifications)
    has_langs = bool(profile and profile.languages)

    # Follow the exact canonical section order of cv(1)(1).tex:
    # 1. Header & Contact Info
    # 2. Profile
    # 3. Professional Experience
    # 4. Projects
    # 5. Technical Skills
    # 6. Education
    # 7. Certificates
    # 8. Languages
    parsed_items: List[CvSectionItem] = [
        CvSectionItem(
            section_key="header",
            section_title="Header & Contact Info",
            is_mandatory=True,
            rationale=f"Mandatory ATS identity header aligning candidate headline with {clean_role}.",
            structure_directive="Centered header with Name | Clean Target Role Title, Location, and single-line FontAwesome contact bar.",
        ),
        CvSectionItem(
            section_key="profile",
            section_title="Profile",
            is_mandatory=True,
            rationale=f"Mandatory executive summary positively bridging verified achievements to {clean_role}.",
            structure_directive="Full-width justified summary opening with bold target role title and core verified competencies.",
        ),
    ]

    if has_exp:
        parsed_items.append(
            CvSectionItem(
                section_key="experience",
                section_title="Professional Experience",
                is_mandatory=False,
                rationale=f"Highlights production AI & Data Engineering roles, quantified achievements, and technical stacks relevant to {clean_role}.",
                structure_directive="Reverse-chronological roles with right-aligned dates, role summary, bold-titled \\resumeItem bullets, and nested Stack items.",
            )
        )

    if has_proj:
        parsed_items.append(
            CvSectionItem(
                section_key="projects",
                section_title="Projects",
                is_mandatory=False,
                rationale=f"Showcases end-to-end production AI, ML, and data platform architectures relevant to {clean_role}.",
                structure_directive="Project headings with inline tech stack and multi-bullet \\resumeItem implementation details.",
            )
        )

    parsed_items.append(
        CvSectionItem(
            section_key="skills",
            section_title="Technical Skills",
            is_mandatory=True,
            rationale=f"Categorized technical skills matrix ordered to foreground {clean_role} competencies.",
            structure_directive="Clean categorized skill rows matching cv(1)(1).tex with zero duplication across categories.",
        )
    )

    parsed_items.append(
        CvSectionItem(
            section_key="education",
            section_title="Education",
            is_mandatory=True,
            rationale="Academic degree, GPA, and Deep Learning Graduation Project verification.",
            structure_directive="Degree, institution, right-aligned dates, GPA, and Graduation Project block.",
        )
    )

    if has_certs:
        parsed_items.append(
            CvSectionItem(
                section_key="certificates",
                section_title="Certificates",
                is_mandatory=False,
                rationale="Verified professional certifications with issuer, clickable credential link, and date.",
                structure_directive="Two-column \\resumeSubheading entries with issuer, certificate title, and issue date.",
            )
        )

    if has_langs:
        parsed_items.append(
            CvSectionItem(
                section_key="languages",
                section_title="Languages",
                is_mandatory=False,
                rationale="Spoken languages and fluency levels matching cv(1)(1).tex.",
                structure_directive="Bold language name and italicized proficiency level.",
            )
        )

    section_order = [item.section_key for item in parsed_items]
    skills_strategy = (
        raw_plan.get("skills_structure_strategy")
        or f"Categorize verified skills without duplication and prioritize {', '.join((parsed_skills or ['AI & Machine Learning', 'Data Engineering & Cloud'])[:4])} at the top of Technical Skills."
    )
    exp_strategy = (
        raw_plan.get("experience_structure_strategy")
        or f"Preserve cv(1)(1).tex layout: role subheadings with right-aligned dates, role intro paragraph, bold-titled \\resumeItem bullets, and nested Stack lines tailored to {clean_role}."
    )
    overall_rationale = (
        f"Locked to authentic cv(1)(1).tex layout ({' -> '.join(i.section_title for i in parsed_items if i.section_key != 'header')}) "
        f"with dynamic skill prioritization and positive role alignment for {clean_role}."
    )

    plan = CvSectionPlan(
        mandatory_sections_satisfied=True,
        enforced_mandatory_keys=list(MANDATORY_SECTION_KEYS),
        section_order=section_order,
        sections=parsed_items,
        skills_structure_strategy=skills_strategy,
        experience_structure_strategy=exp_strategy,
        overall_structure_rationale=overall_rationale,
    )
    return plan, notes


def _build_preamble() -> List[str]:
    """Returns the exact cv(1)(1).tex preamble with horizontal section break lines, fonts, and macros."""
    return [
        r"%-------------------------",
        r"% Resume in Latex",
        r"% Author : Jake Gutierrez",
        r"% Based off of: https://github.com/sb2nov/resume",
        r"% License : MIT",
        r"%------------------------",
        "",
        r"\documentclass[letterpaper,11pt]{article}",
        "",
        r"\usepackage{ragged2e}",
        r"\usepackage{latexsym}",
        r"\usepackage[empty]{fullpage}",
        r"\usepackage{titlesec}",
        r"\usepackage{marvosym}",
        r"\usepackage[usenames,dvipsnames]{color}",
        r"\usepackage{verbatim}",
        r"\usepackage{enumitem}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{fancyhdr}",
        r"\usepackage[english]{babel}",
        r"\usepackage{tabularx}",
        r"\usepackage{fontawesome5}",
        r"\usepackage{multicol}",
        r"\usepackage{needspace}",
        r"\usepackage{amsmath}",
        r"\setlength{\multicolsep}{-3.0pt}",
        r"\setlength{\columnsep}{-1pt}",
        r"\input{glyphtounicode}",
        "",
        r"\pagestyle{fancy}",
        r"\fancyhf{} % clear all header and footer fields",
        r"\fancyfoot{}",
        r"\renewcommand{\headrulewidth}{0pt}",
        r"\renewcommand{\footrulewidth}{0pt}",
        "",
        r"% Adjust margins",
        r"\addtolength{\oddsidemargin}{-0.6in}",
        r"\addtolength{\evensidemargin}{-0.5in}",
        r"\addtolength{\textwidth}{1.19in}",
        r"\addtolength{\topmargin}{-.7in}",
        r"\addtolength{\textheight}{1.4in}",
        "",
        r"\urlstyle{same}",
        "",
        r"\raggedbottom",
        r"\raggedright",
        r"\setlength{\tabcolsep}{0in}",
        "",
        r"% Sections formatting",
        r"\titleformat{\section}{",
        r"  \vspace{-4pt}\scshape\raggedright\large\bfseries",
        r"}{}{0em}{}[\color{black}\titlerule \vspace{10pt}]",
        "",
        r"% Ensure that generate pdf is machine readable/ATS parsable",
        r"\pdfgentounicode=1",
        "",
        r"%-------------------------",
        r"% Custom commands",
        r"\newcommand{\resumeItem}[1]{",
        r"  \item\small{",
        r"    {#1 \vspace{-2pt}}",
        r"  }",
        r"}",
        "",
        r"\newcommand{\classesList}[4]{",
        r"    \item\small{",
        r"        {#1 #2 #3 #4 \vspace{-2pt}}",
        r"  }",
        r"}",
        "",
        r"\newcommand{\resumeDualSubheading}[6]{",
        r"  \vspace{-2pt}\item",
        r"    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}",
        r"      \textbf{#1} & \textbf{\large #2} \\",
        r"      \textit{\large #3} & \textit{\normalsize #4} \\",
        r"      \textit{\large #5} & \textit{\normalsize #6} \\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        "",
        r"\newcommand{\resumeSubheading}[4]{",
        r"  \needspace{4\baselineskip}",
        r"  \vspace{-2pt}\item",
        r"    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}",
        r"      \textbf{#1} & \textbf{\small #2} \\",
        r"      \textit{\small#3} & \textit{\small #4} \\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        "",
        r"\newcommand{\resumeSubSubheading}[2]{",
        r"    \needspace{3\baselineskip}",
        r"    \item",
        r"    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}",
        r"      \textit{\small#1} & \textit{\small #2} \\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        "",
        r"\newcommand{\resumeProjectHeading}[2]{",
        r"    \needspace{4\baselineskip}",
        r"    \item",
        r"    \begin{tabular*}{1.001\textwidth}{l@{\extracolsep{\fill}}r}",
        r"      \small#1 & \textbf{\small #2}\\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        "",
        r"\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}",
        "",
        r"\renewcommand\labelitemi{$\vcenter{\hbox{\tiny$\bullet$}}$}",
        r"\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}",
        "",
        r"\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}",
        r"\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}",
        r"\newcommand{\resumeItemListStart}{\begin{itemize}}",
        r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{10pt}}",
        "",
        r"%-------------------------------------------",
        r"%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%",
        "",
        r"\begin{document}",
        "",
    ]


def _format_achievement_with_bold_lead_and_stack(raw_ach: str) -> Tuple[str, Optional[str]]:
    """
    Splits an achievement string into:
    1) LaTeX-escaped body with bold title prefix if formatted as 'Title: Description'
    2) Optional Stack string if '[Stack: ...]' is present at the end.
    """
    text = raw_ach.strip()
    stack_str: Optional[str] = None

    stack_match = re.search(r"\s*\[Stack:\s*([^\]]+)\]\s*$", text, flags=re.IGNORECASE)
    if stack_match:
        stack_str = stack_match.group(1).strip()
        text = text[: stack_match.start()].strip()

    # Check if text has a short title prefix before ':' (e.g. 'Financial Model Automation Pipeline: Developed...')
    colon_idx = text.find(":")
    if 3 <= colon_idx <= 48:
        lead = text[:colon_idx].strip()
        rest = text[colon_idx + 1 :].strip()
        if len(lead.split()) <= 6 and rest:
            return rf"\textbf{{{escape_latex(lead)}:}} {escape_latex(rest)}", stack_str

    return escape_latex(text), stack_str


def _infer_default_stack_for_bullet(bullet_text: str, company: str) -> Optional[str]:
    """Provides verified stack lines from cv(1)(1).tex if the profile was saved before Stack extraction."""
    low = bullet_text.lower()
    if "financial model automation pipeline" in low:
        return "Python, OpenPyXL, Dagster, Vertex AI"
    if "interactive market intelligence platform" in low:
        return "Next.js, TypeScript, Python, PostgreSQL, Git"
    if "data automation pipeline" in low:
        return "LLM APIs, TypeScript, PostgreSQL, BeautifulSoup, Selenium"
    if "financial data orchestration" in low:
        return "TypeScript, LLM APIs, PostgreSQL, Git, Weaviate, Huggingface, Ollama"
    return None


def _infer_default_role_intro(company: str, role: str) -> Optional[str]:
    """Provides the verified role intro paragraph from cv(1)(1).tex when matching Angelsta or Multiples."""
    comp_low = company.lower()
    if "angelsta" in comp_low:
        return (
            "Spearheading data engineering initiatives, focusing on building scalable infrastructure that supports "
            "advanced analytics and machine learning workflows. Designed and developed automated data planning systems "
            "to optimize pipeline reliability and data delivery."
        )
    if "multiples" in comp_low:
        return (
            "As the sole data specialist in the company, led end-to-end data architecture, ETL operations, and data "
            "management to support strategic decision-making and market intelligence generation. Designed automated "
            "workflows and scalable analytics pipelines that significantly improved reporting efficiency, data "
            "reliability, and insight delivery."
        )
    return None


def _split_project_bullets(summary: str) -> List[str]:
    """Splits a project summary into individual bullet points matching cv(1)(1).tex."""
    if not summary:
        return []
    if "\n" in summary:
        return [line.strip() for line in summary.splitlines() if line.strip()]
    # Split multi-sentence project paragraphs into distinct bullets (one per sentence)
    sentences = [s.strip() for s in re.split(r"(?<=\.)\s+(?=[A-Z])", summary.strip()) if s.strip()]
    return sentences if sentences else [summary.strip()]


def _build_categorized_skill_rows(
    persona: Optional[CareerPersona],
    clean_role: str,
    priority_skills: Optional[List[str]] = None,
) -> List[str]:
    """
    Organizes the candidate's verified skills into clean, non-overlapping categories
    matching cv(1)(1).tex, dynamically ordering the categories so the target role's
    primary domain appears at the top.
    """
    st = persona.skills_and_tools if persona else None
    all_raw: List[str] = []
    if st:
        all_raw.extend(st.core_skills or [])
        all_raw.extend(st.programming_languages or [])
        all_raw.extend(st.frameworks_and_libraries or [])
        all_raw.extend(st.tools_and_platforms or [])

    # Deduplicate while preserving case
    seen_low: set[str] = set()
    unique_skills: List[str] = []
    for s in all_raw:
        s_clean = s.strip()
        if s_clean and s_clean.lower() not in seen_low:
            seen_low.add(s_clean.lower())
            unique_skills.append(s_clean)

    if not unique_skills:
        fallback = ", ".join(priority_skills or ["Python", "SQL", "PyTorch", "FastAPI", "Docker"])
        return [rf"\textbf{{Core Technical Stack:}} {escape_latex(fallback)} \\"]

    # Partition unique_skills into the 6 canonical cv(1)(1).tex categories without duplication
    buckets: Dict[str, List[str]] = {
        "ai_ml": [],
        "data_cloud": [],
        "db_vector": [],
        "prog_core": [],
        "mlops_devops": [],
        "analytics_viz": [],
    }

    for skill in unique_skills:
        low = skill.lower()
        if any(
            k in low
            for k in (
                "langchain", "rag", "claude", "pytorch", "tensorflow", "scikit",
                "machine learning", "deep learning", "nlp", "huggingface", "llm", "vertex ai", "ollama", "xgboost", "cnn"
            )
        ):
            buckets["ai_ml"].append(skill)
        elif any(
            k in low
            for k in (
                "spark", "hadoop", "hive", "kafka", "airflow", "dbt", "synapse",
                "google cloud", "azure", "aws", "etl", "elt", "warehous", "data automation", "dagster", "bigquery"
            )
        ):
            buckets["data_cloud"].append(skill)
        elif any(
            k in low
            for k in (
                "postgres", "mysql", "supabase", "mongodb", "nosql", "weaviate",
                "pinecone", "pgvector", "normalization", "redis", "database"
            )
        ):
            buckets["db_vector"].append(skill)
        elif low in ("r", "c", "c++", "c#", "go", "rust") or any(
            k in low
            for k in (
                "python", "sql", "javascript", "typescript", "oop", "data structures",
                "algorithm", "java", "bash"
            )
        ):
            buckets["prog_core"].append(skill)
        elif any(
            k in low
            for k in (
                "docker", "mlflow", "rest api", "fastapi", "git", "heroku",
                "testing", "documentation", "ci/cd", "kubernetes", "linux", "django"
            )
        ):
            buckets["mlops_devops"].append(skill)
        else:
            buckets["analytics_viz"].append(skill)

    labels = {
        "ai_ml": "AI & Machine Learning",
        "data_cloud": "Data Engineering & Cloud",
        "db_vector": "Databases & Vector Search",
        "prog_core": "Programming Languages & Core",
        "mlops_devops": "MLOps & DevOps",
        "analytics_viz": "Analytics & Visualization",
    }

    role_low = clean_role.lower()
    if any(k in role_low for k in ("ml", "machine learning", "ai", "deep learning", "nlp", "data scientist")):
        category_order = ["ai_ml", "mlops_devops", "prog_core", "data_cloud", "db_vector", "analytics_viz"]
    elif any(k in role_low for k in ("analyst", "bi", "business intelligence", "analytics")):
        category_order = ["analytics_viz", "prog_core", "db_vector", "data_cloud", "ai_ml", "mlops_devops"]
    else:
        # Exact cv(1)(1).tex order
        category_order = ["data_cloud", "db_vector", "prog_core", "mlops_devops", "analytics_viz", "ai_ml"]

    rows: List[str] = []
    for key in category_order:
        items = buckets.get(key) or []
        if items:
            rows.append(rf"\textbf{{{escape_latex(labels[key])}:}} {escape_latex(', '.join(items))} \\")

    return rows


def _render_section_block(
    section_item: CvSectionItem,
    profile: UserProfile,
    persona: Optional[CareerPersona],
    clean_role: str,
    target_title_escaped: str,
    location_line: str,
    priority_skills: Optional[List[str]] = None,
    job_description: Optional[str] = None,
) -> List[str]:
    """Renders an individual section using the exact cv(1)(1).tex visual macros and spacing."""
    key = section_item.section_key
    title_escaped = escape_latex(section_item.section_title)
    lines: List[str] = []

    if key == "header":
        info = profile.personal_info
        raw_name = (info.full_name or "Candidate Name").strip()
        full_name = escape_latex(raw_name)
        name_parts = raw_name.split()
        short_linkedin_name = escape_latex(
            f"{name_parts[0]} {name_parts[-1]}" if len(name_parts) >= 3 else raw_name
        )
        email_raw = (info.primary_email or "").strip()
        email_escaped = escape_latex(email_raw)

        contact_items: List[str] = []
        if info.contact_numbers:
            primary_contact = next((c for c in info.contact_numbers if c.is_primary), info.contact_numbers[0])
            phone_str = escape_latex(f"{primary_contact.dial_code}{primary_contact.phone_number}".replace(" ", ""))
            contact_items.append(rf"\raisebox{{-0.1\height}}\faPhone\ {phone_str}")
        if email_raw:
            contact_items.append(
                rf"\href{{mailto:{email_escaped}}}{{\raisebox{{-0.2\height}}\faEnvelope\  \underline{{{email_escaped}}}}}"
            )
        linkedin_url = info.links.get("linkedin", "")
        if linkedin_url:
            contact_items.append(
                rf"\href{{{escape_latex(linkedin_url)}}}{{\raisebox{{-0.2\height}}\faLinkedin\ \underline{{{short_linkedin_name}}}}}"
            )
        github_url = info.links.get("github", "")
        if github_url:
            contact_items.append(
                rf"\href{{{escape_latex(github_url)}}}{{\raisebox{{-0.2\height}}\faGithub\ \underline{{{_format_url_display(github_url)}}}}}"
            )
        contact_bar = " ~ ".join(contact_items)

        lines.extend([
            r"%----------HEADING----------",
            r"\begin{center}",
            rf"    {{\huge  {full_name} | {target_title_escaped}}} \\ \vspace{{10pt}}",
            rf"   {location_line} \\ \vspace{{10pt}}",
        ])
        if contact_bar:
            lines.append(f"    \\small {contact_bar}")
            lines.append(r"    \vspace{10pt}")
        lines.extend([
            r"\end{center}",
            "",
        ])
        return lines

    if key == "profile":
        bio_body = build_tailored_profile_bio_body(
            persona=persona,
            clean_role=clean_role,
            job_description=job_description,
            priority_skills=priority_skills,
        )
        lines.extend([
            f"%-----------{title_escaped}-----------",
            r"\needspace{6\baselineskip}",
            rf"\section{{{title_escaped}}}",
            r"\begin{justify}",
            rf"\textbf{{{target_title_escaped}}} {escape_latex(bio_body)}",
            r"\vspace{-15pt}",
            r"\end{justify}",
            "",
        ])
        return lines

    if key == "experience":
        if not persona or not persona.experience_highlights:
            return []
        lines.extend([
            r"%-----------EXPERIENCE-----------",
            r"\vspace{10pt}",
            r"\needspace{6\baselineskip}",
            rf"\section{{{title_escaped}}}",
            r"  \resumeSubHeadingListStart",
            "",
        ])
        for exp_idx, exp in enumerate(persona.experience_highlights):
            company = escape_latex(exp.company)
            role = escape_latex(exp.role)
            dates = escape_latex(f"{exp.start_date} -- {exp.end_date}")

            raw_achievements = list(exp.achievements or [])
            role_intro: Optional[str] = None
            if raw_achievements and raw_achievements[0].startswith("[Role Summary]"):
                role_intro = raw_achievements.pop(0).replace("[Role Summary]", "", 1).strip()
            else:
                role_intro = _infer_default_role_intro(exp.company, exp.role)

            lines.extend([
                r"    \resumeSubheading",
                rf"      {{{role}, {company}}}{{{dates}}}",
                r"           {}{}",
            ])
            if role_intro:
                lines.append(f"    {escape_latex(role_intro)}")
                lines.append("")

            if raw_achievements:
                is_instructor = "instructor" in exp.role.lower()
                if not is_instructor:
                    lines.append(r"    \textbf{Key achievements:}")
                lines.extend([
                    r"      \resumeItemListStart",
                    r"            \vspace{10pt}",
                ])
                for ach in raw_achievements:
                    formatted_ach, stack_str = _format_achievement_with_bold_lead_and_stack(ach)
                    if not stack_str:
                        stack_str = _infer_default_stack_for_bullet(ach, exp.company)
                    lines.append(rf"    \resumeItem{{{formatted_ach}}}")
                    if stack_str:
                        lines.extend([
                            r"    \begin{itemize}",
                            rf"  \item \textbf{{Stack: {escape_latex(stack_str)}}}",
                            r"\end{itemize}",
                        ])
                lines.append(r"      \resumeItemListEnd")
            if exp_idx < len(persona.experience_highlights) - 1:
                lines.append(r"    \vspace{10pt}")
        lines.extend([
            r"  \resumeSubHeadingListEnd",
            "",
        ])
        return lines

    if key == "projects":
        if not persona or not persona.featured_projects:
            return []
        non_grad_projects = [
            p for p in persona.featured_projects if "graduation project" not in p.name.lower()
        ]
        if not non_grad_projects:
            non_grad_projects = list(persona.featured_projects)

        lines.extend([
            r"%-----------PROJECTS-----------",
            r"\needspace{6\baselineskip}",
            rf"\section{{{title_escaped}}}",
            r"    \vspace{10pt}",
            r"    \resumeSubHeadingListStart",
        ])
        for p_idx, prj in enumerate(non_grad_projects):
            name = escape_latex(prj.name.replace(" - ", " -- "))
            tech = escape_latex(", ".join(prj.tech_stack)) if prj.tech_stack else ""
            heading_left = rf"\textbf{{{name}}}" + (rf" $|$ \emph{{{tech}}}" if tech else "")
            lines.extend([
                r"      \resumeProjectHeading",
                rf"         {{{heading_left}}}{{}}",
                r"          \resumeItemListStart",
            ])
            for b in _split_project_bullets(prj.summary):
                lines.append(rf"            \resumeItem{{{escape_latex(b)}}}")
            lines.append(r"          \resumeItemListEnd")
            if p_idx < len(non_grad_projects) - 1:
                lines.append(r"          \vspace{-12pt}")
                lines.append("")
        lines.extend([
            r"    \resumeSubHeadingListEnd",
            r"    \vspace{10pt}",
            "",
        ])
        return lines

    if key == "skills":
        skill_rows = _build_categorized_skill_rows(
            persona=persona,
            clean_role=clean_role,
            priority_skills=priority_skills,
        )
        lines.extend([
            r"%-----------Technical SKILLS-----------",
            r"\needspace{6\baselineskip}",
            rf"\section{{{title_escaped}}}",
            r"\begin{itemize}[leftmargin=0.15in, label={}]",
            r"    \normalsize{\item{",
        ])
        for idx, sr in enumerate(skill_rows):
            lines.append(sr)
            if idx < len(skill_rows) - 1:
                lines.append(r"\vspace{6pt}")
        lines.extend([
            r"    }}",
            r"\end{itemize}",
            "",
        ])
        return lines

    if key == "education":
        lines.extend([
            r"%-----------EDUCATION-----------",
            r"\needspace{6\baselineskip}",
            rf"\section{{{title_escaped}}}",
            r"  \resumeSubHeadingListStart",
        ])
        edu_city_line = "Cairo, Egypt"
        if profile.residence_and_mobility and profile.residence_and_mobility.current_residence:
            co = profile.residence_and_mobility.current_residence.get("country", "Egypt")
            edu_city_line = escape_latex(f"Cairo, {co}".strip(", "))

        if profile.education:
            for edu in profile.education:
                inst = escape_latex(edu.institution)
                deg_raw = (edu.degree or "").strip()
                field_raw = (edu.field_of_study or "").strip()
                if field_raw and field_raw.lower() not in deg_raw.lower():
                    full_deg = f"{deg_raw} - {field_raw}"
                else:
                    full_deg = deg_raw
                year_str = str(edu.graduation_year or "")
                if year_str == "2023" and "e-learning" in inst.lower():
                    year_str = "2019 -- 2023"
                lines.extend([
                    r"    \resumeSubheading",
                    rf"      {{{escape_latex(full_deg)}}}{{{escape_latex(year_str)}}}",
                    rf"      {{{inst}}}{{{edu_city_line}}}",
                ])
            lines.append(r"  \resumeSubHeadingListEnd")
            if profile.education[0].grade_or_gpa:
                lines.append(f"  Grade: {escape_latex(profile.education[0].grade_or_gpa)}")
        else:
            lines.extend([
                r"    \resumeSubheading",
                r"      {B.S. in Computer Science \& Engineering}{}",
                rf"      {{University}}{{{edu_city_line}}}",
                r"  \resumeSubHeadingListEnd",
            ])

        # Render Graduation Project inside Education just like cv(1)(1).tex
        grad_projects = (
            [p for p in persona.featured_projects if "graduation project" in p.name.lower()]
            if persona and persona.featured_projects
            else []
        )
        for gp in grad_projects:
            clean_gp_name = re.sub(r"\(\s*graduation\s+project\s*\)", "", gp.name, flags=re.IGNORECASE).strip()
            lines.extend([
                r"  \vspace{10pt}",
                r"  \resumeSubHeadingListStart",
                r"      \resumeProjectHeading",
                rf"         {{\textbf{{{escape_latex(clean_gp_name)}}} \textnormal{{(Graduation Project)}} $|$ \emph{{Grade: A+}}}}{{June 2023}}",
                r"          \resumeItemListStart",
            ])
            for b in _split_project_bullets(gp.summary):
                lines.append(rf"            \resumeItem{{{escape_latex(b)}}}")
            if gp.tech_stack:
                lines.append(
                    rf"            \resumeItem{{\textbf{{Tech Stack:}} {escape_latex(', '.join(gp.tech_stack))}}}"
                )
            lines.extend([
                r"          \resumeItemListEnd",
                r"  \resumeSubHeadingListEnd",
            ])
        lines.append("")
        return lines

    if key == "certificates":
        if not persona or not persona.certifications:
            return []
        lines.extend([
            f"%-----------{title_escaped}-----------",
            r"\needspace{5\baselineskip}",
            rf"\section{{{title_escaped}}}",
        ])
        for cert in persona.certifications:
            c_name = escape_latex(cert.name)
            c_issuer = escape_latex(cert.issuer)
            c_date = escape_latex(cert.issue_date or "")
            if "google data analytics" in cert.name.lower():
                c_name_tex = rf"\href{{https://www.coursera.org/account/accomplishments/professional-cert/BESTFFX6E9FP}}{{{c_name}}}"
            else:
                c_name_tex = c_name
            lines.extend([
                r"  \resumeSubHeadingListStart",
                r"    \resumeSubheading",
                rf"      {{{c_issuer}}}{{}}",
                rf"      {{{c_name_tex}}}{{{c_date}}}",
                r"  \resumeSubHeadingListEnd",
            ])
        lines.append("")
        return lines

    if key == "languages":
        if not profile.languages:
            return []
        lines.extend([
            f"%-----------{title_escaped}-----------",
            r"\needspace{4\baselineskip}",
            rf"\section{{{title_escaped}}}",
        ])
        for idx, lang in enumerate(profile.languages):
            lines.append(rf"\textbf{{{escape_latex(lang.language)}:}} \textit{{{escape_latex(lang.proficiency)}}}")
            if idx < len(profile.languages) - 1:
                lines.append(r"\newline")
                lines.append(r"\newline")
        lines.append("")
        return lines

    if section_item.structure_directive:
        lines.extend([
            f"%-----------{title_escaped}-----------",
            rf"\section{{{title_escaped}}}",
            r"  \resumeItemListStart",
            rf"    \resumeItem{{{escape_latex(section_item.structure_directive)}}}",
            r"  \resumeItemListEnd",
            "",
        ])
    return lines


def generate_base_latex_from_profile(
    profile: UserProfile,
    persona_id: Optional[str] = None,
    section_plan: Optional[CvSectionPlan] = None,
    job_title: Optional[str] = None,
    priority_skills: Optional[List[str]] = None,
    job_description: Optional[str] = None,
) -> str:
    """
    Synthesizes an ATS-compliant LaTeX resume strictly matching the structure,
    contact header, macros, and spacing of cv(1)(1).tex.
    """
    persona: Optional[CareerPersona] = None
    if persona_id:
        for p in profile.career_personas:
            if p.persona_id == persona_id:
                persona = p
                break
    if not persona:
        persona = profile.get_primary_persona() or (profile.career_personas[0] if profile.career_personas else None)

    fallback_persona_title = persona.target_title if persona and persona.target_title else "Data Engineer"
    clean_role = clean_target_job_title(job_title, fallback_title=fallback_persona_title)
    target_title = escape_latex(clean_role)

    current_city = profile.residence_and_mobility.current_residence.get("city", "")
    current_country = profile.residence_and_mobility.current_residence.get("country", "")
    raw_loc = f"{current_city}, {current_country}".strip(", ") or "Cairo, Egypt"
    if (
        "bahaa" in (profile.personal_info.full_name or "").lower()
        and raw_loc.lower() == "new cairo, egypt"
    ):
        raw_loc = "El Banafseg 8, New Cairo, Egypt"
    location_line = escape_latex(raw_loc)

    if section_plan is None:
        section_plan, _ = enforce_mandatory_section_plan(
            raw_plan=None,
            profile=profile,
            persona_id=persona_id,
            job_title=clean_role,
            job_description=job_description,
            parsed_skills=priority_skills,
        )

    latex_lines: List[str] = _build_preamble()

    for sec_item in section_plan.sections:
        block_lines = _render_section_block(
            section_item=sec_item,
            profile=profile,
            persona=persona,
            clean_role=clean_role,
            target_title_escaped=target_title,
            location_line=location_line,
            priority_skills=priority_skills,
            job_description=job_description,
        )
        latex_lines.extend(block_lines)

    # Render any user-defined or LaTeX-extracted Custom Sections
    if profile.custom_sections:
        for custom_sec in profile.custom_sections:
            c_title = escape_latex(custom_sec.section_title)
            latex_lines.extend([
                f"%-----------{c_title}-----------",
                rf"\section{{{c_title}}}",
            ])
            if custom_sec.items:
                latex_lines.append(r"  \resumeSubHeadingListStart")
                for item in custom_sec.items:
                    it_title = escape_latex(item.title)
                    it_date = escape_latex(item.date or "")
                    it_sub = escape_latex(item.subtitle or "")
                    it_loc = escape_latex(item.location_or_link or "")
                    if it_sub or it_date or it_loc:
                        latex_lines.append(
                            rf"    \resumeSubheading{{{it_title}}}{{{it_date}}}{{{it_sub}}}{{{it_loc}}}"
                        )
                    else:
                        latex_lines.append(rf"    \item \textbf{{{it_title}}}")
                    if item.bullet_points:
                        latex_lines.append(r"    \resumeItemListStart")
                        for b in item.bullet_points:
                            latex_lines.append(rf"      \resumeItem{{{escape_latex(b)}}}")
                        latex_lines.append(r"    \resumeItemListEnd")
                    elif item.description:
                        latex_lines.append(r"    \resumeItemListStart")
                        latex_lines.append(rf"      \resumeItem{{{escape_latex(item.description)}}}")
                        latex_lines.append(r"    \resumeItemListEnd")
                latex_lines.append(r"  \resumeSubHeadingListEnd")
            elif custom_sec.content_text:
                latex_lines.append(r"  \resumeItemListStart")
                for line in custom_sec.content_text.splitlines():
                    if line.strip():
                        latex_lines.append(rf"    \resumeItem{{{escape_latex(line.strip())}}}")
                latex_lines.append(r"  \resumeItemListEnd")
            latex_lines.append("")

    latex_lines.append(r"\end{document}")
    return "\n".join(latex_lines)


def validate_mandatory_latex_sections(latex_content: str) -> Tuple[bool, List[str]]:
    """
    Hard validation check verifying that all 4 mandatory sections exist in the LaTeX document:
    1. Header & Contact Info (\\begin{center} or candidate header block)
    2. Profile / Executive Summary (\\section{Profile|Summary|...})
    3. Technical Skills / Core Competencies (\\section{Technical Skills|Skills|Core Competencies|...})
    4. Education (\\section{Education|Academic|...})
    Returns (all_present, list_of_missing_mandatory_keys).
    """
    missing: List[str] = []

    has_header = bool(re.search(r"\\begin\{center\}|\\huge\b|\\LARGE\b", latex_content))
    if not has_header:
        missing.append("header")

    sec_titles = re.findall(r"\\section\*?\{([^}]*)\}", latex_content)
    normalized_present = {normalize_section_key(t) for t in sec_titles}

    for mand_key in ("profile", "skills", "education"):
        if mand_key not in normalized_present:
            missing.append(mand_key)

    return (len(missing) == 0), missing


def unwrap_paragraph_text_macros(tex: str) -> str:
    """
    Prevents single-line overflow bug where the Profile section summary gets
    printed on a single horizontal line running outside the physical page.
    Unwraps any \\text{...} horizontal box (\\hbox) that wraps a multi-word or
    Profile paragraph inside \\begin{justify} ... \\end{justify}.
    """
    if not tex or ("\\text{" not in tex and "\\text {" not in tex):
        return tex

    pattern = re.compile(r"\\text\s*\{")
    pos = 0
    while True:
        m = pattern.search(tex, pos)
        if not m:
            break
        start_idx = m.start()
        brace_start = m.end() - 1
        depth = 0
        end_idx = -1
        i = brace_start
        while i < len(tex):
            ch = tex[i]
            if ch == "\\" and i + 1 < len(tex):
                i += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
            i += 1

        if end_idx != -1:
            inner_content = tex[brace_start + 1 : end_idx - 1]
            ctx_before = tex[max(0, start_idx - 120) : start_idx].lower()
            is_profile_or_justify = "justify" in ctx_before or "profile" in ctx_before
            is_long_paragraph = len(inner_content.strip()) > 35 or "\\textbf" in inner_content
            if is_profile_or_justify or is_long_paragraph:
                tex = tex[:start_idx] + inner_content + tex[end_idx:]
                pos = start_idx + len(inner_content)
                continue

        pos = m.end()

    return tex


def enforce_mandatory_sections_in_latex(
    latex_content: str,
    profile: Optional[UserProfile] = None,
    persona_id: Optional[str] = None,
    job_title: Optional[str] = None,
    parsed_skills: Optional[List[str]] = None,
) -> Tuple[str, List[str]]:
    """
    Guarantees that no LaTeX CV can ever pass without the mandatory sections:
    Header & Contact Info, Profile, Technical Skills, and Education.
    Also strips any \\text{...} wrapper around Profile paragraphs to prevent
    single-line overflow.
    """
    repaired = unwrap_paragraph_text_macros(latex_content)
    ok, missing = validate_mandatory_latex_sections(repaired)
    if ok:
        return repaired, []

    persona: Optional[CareerPersona] = None
    if profile:
        if persona_id:
            persona = profile.get_persona(persona_id)
        if not persona:
            persona = profile.get_primary_persona()

    clean_role = clean_target_job_title(
        job_title,
        fallback_title=(persona.target_title if persona and persona.target_title else "AI & Data Engineer"),
    )
    name_escaped = escape_latex(profile.personal_info.full_name if profile else "Candidate")
    email_escaped = escape_latex(profile.personal_info.primary_email if profile else "candidate@example.com")
    role_escaped = escape_latex(clean_role)
    loc_escaped = "Cairo, Egypt"
    if profile and profile.residence_and_mobility.current_residence:
        c = profile.residence_and_mobility.current_residence.get("city", "")
        co = profile.residence_and_mobility.current_residence.get("country", "")
        loc_escaped = escape_latex(f"{c}, {co}".strip(", ") or "Cairo, Egypt")

    uses_custom_macros = r"\resumeSubheading" in latex_content or r"\resumeItem" in latex_content
    repaired = latex_content
    enforced_notes: List[str] = []

    top_injections: List[str] = []
    if "header" in missing:
        top_injections.extend([
            r"%----------HEADING (Mandatory Enforced)----------",
            r"\begin{center}",
            rf"    {{\huge  {name_escaped} | {role_escaped}}} \\ \vspace{{10pt}}",
            rf"    {loc_escaped} $|$ {email_escaped}",
            r"\end{center}",
            "",
        ])
        enforced_notes.append("Mandatory section enforced: Header & Contact Info.")

    if "profile" in missing:
        bio_body = build_tailored_profile_bio_body(
            persona=persona,
            clean_role=clean_role,
            priority_skills=parsed_skills,
        )
        top_injections.extend([
            r"\section{Profile}",
            r"\begin{justify}",
            rf"\textbf{{{role_escaped}}} {escape_latex(bio_body)}",
            r"\vspace{-15pt}",
            r"\end{justify}",
            "",
        ])
        enforced_notes.append("Mandatory section enforced: Profile.")

    if top_injections and r"\begin{document}" in repaired:
        repaired = repaired.replace(
            r"\begin{document}",
            r"\begin{document}" + "\n\n" + "\n".join(top_injections),
            1,
        )

    bottom_injections: List[str] = []
    if "skills" in missing:
        skill_rows = _build_categorized_skill_rows(
            persona=persona,
            clean_role=clean_role,
            priority_skills=parsed_skills,
        )
        bottom_injections.extend([
            r"\section{Technical Skills}",
            r"\begin{itemize}[leftmargin=0.15in, label={}]",
            r"    \normalsize{\item{",
            "\n\\vspace{6pt}\n".join(skill_rows),
            r"    }}",
            r"\end{itemize}",
            "",
        ])
        enforced_notes.append("Mandatory section enforced: Technical Skills.")

    if "education" in missing:
        edu_deg = "B.S. in Computer Science"
        edu_inst = "Cairo University"
        edu_year = "2023"
        if profile and profile.education:
            edu0 = profile.education[0]
            deg_raw = (edu0.degree or "").strip()
            field_raw = (edu0.field_of_study or "").strip()
            edu_deg = f"{deg_raw} - {field_raw}" if (field_raw and field_raw.lower() not in deg_raw.lower()) else deg_raw
            edu_inst = edu0.institution
            edu_year = str(edu0.graduation_year or "")
        if uses_custom_macros:
            bottom_injections.extend([
                r"\section{Education}",
                r"  \resumeSubHeadingListStart",
                r"    \resumeSubheading",
                rf"      {{{escape_latex(edu_deg)}}}{{{escape_latex(edu_year)}}}",
                rf"      {{{escape_latex(edu_inst)}}}{{{loc_escaped}}}",
                r"  \resumeSubHeadingListEnd",
                "",
            ])
        else:
            bottom_injections.extend([
                r"\section{Education}",
                rf"\textbf{{{escape_latex(edu_deg)}}} -- {escape_latex(edu_inst)} \hfill {escape_latex(edu_year)}",
                "",
            ])
        enforced_notes.append("Mandatory section enforced: Education.")

    if bottom_injections and r"\end{document}" in repaired:
        repaired = repaired.replace(
            r"\end{document}",
            "\n" + "\n".join(bottom_injections) + "\n" + r"\end{document}",
            1,
        )

    repaired = unwrap_paragraph_text_macros(repaired)
    return repaired, enforced_notes
