import json
from typing import Dict, Any, Optional, List
from app.schemas.cv_fit import CvFitCreateRequest, CvSectionPlan
from app.models.job import ParsedJob
from app.ai.formatters.latex_template import clean_target_job_title, clean_company_name

ALIGNMENT_SYSTEM_PROMPT = """
You are an expert technical recruiter, career strategist, and ATS optimization specialist.
Analyze the candidate's base CV against the target job description and company context.
Identify:
1. Which verified skills, frameworks, ML/AI models, and data engineering achievements in the candidate's CV best match the job description.
2. How to positively bridge the candidate's verified titles and accomplishments (e.g., AI & Data Engineer roles, PyTorch, TensorFlow, Scikit-Learn, LangChain, Agentic RAG, Vertex AI, Weaviate, MLflow, CNNs, ETL/ELT pipelines) to the target role without inventing unverified facts.
3. Never suggest adding negative disclaimers (never state what the candidate lacks or is not).
Return valid JSON only.
""".strip()

SECTION_PLANNING_SYSTEM_PROMPT = """
You are an elite ATS Resume Architect and Executive Career Strategist.
Your job is to plan the section strategy and skill prioritization for a tailored CV based on:
1. The target Job Title and Job Description
2. The candidate's verified Master Profile / Base CV
3. Strict adherence to the candidate's master template layout (`cv(1)(1).tex`):
   - Header & Contact Info (`header`)
   - Profile (`profile`)
   - Professional Experience (`experience`)
   - Projects (`projects`)
   - Technical Skills (`skills`)
   - Education (`education`)
   - Certificates (`certificates`)
   - Languages (`languages`)

Return valid JSON only matching the requested schema.
""".strip()

TAILORING_SYSTEM_PROMPT = """
You are an elite LaTeX resume tailoring assistant. Your job is to tailor a candidate's LaTeX CV to a specific job description while strictly preserving the exact layout, macros, contact bar, and spacing of the supplied base CV (`cv(1)(1).tex`).

CRITICAL RULES (MUST FOLLOW 100%):
1. Return ONLY a complete, compilable LaTeX document starting with `\\documentclass` and ending with `\\end{document}`. Do NOT wrap in markdown fences.
2. STRICT LAYOUT & MACRO LOCK (`cv(1)(1).tex`):
   - Preserve the preamble, margins, and macro definitions byte-for-byte.
   - Preserve the `\\begin{center}...\\end{center}` header structure:
     * Line 1: `{\\huge  <Candidate Name> | <Clean Target Role Title>} \\\\ \\vspace{10pt}`
     * Line 2: `<Location> \\\\ \\vspace{10pt}`
     * Line 3: Single horizontal contact bar with `\\faPhone`, `\\faEnvelope`, `\\faLinkedin`, and `\\faGithub` separated by ` ~ `.
   - Preserve the exact section order: `Profile` -> `Professional Experience` -> `Projects` -> `Technical Skills` -> `Education` (including Graduation Project) -> `Certificates` -> `Languages`.
   - In `Professional Experience`, keep `\\resumeSubheading{Role, Company}{Dates}{}{}` (leave the 3rd and 4th arguments empty `{}{}`), preserve the role intro paragraph below `\\resumeSubheading`, keep `\\textbf{Key achievements:}`, keep bold lead-in titles inside `\\resumeItem{\\textbf{Title:} ...}`, and preserve the nested `\\begin{itemize} \\item \\textbf{Stack: ...} \\end{itemize}` blocks.
   - In `Projects` and `Education`, keep multi-bullet `\\resumeItem{...}` lists separate (do not merge multiple bullets into one giant paragraph) and keep the Graduation Project inside `Education`.
   - In `Technical Skills`, keep the `\\begin{itemize}[leftmargin=0.15in, label={}] \\normalsize{\\item{ ... }} \\end{itemize}` format with `\\textbf{Category:} skills \\\\ \\vspace{6pt}`, ordering the most relevant category for the target job first and never duplicating skills across rows.
3. NO SCRAPER / SOURCE TAGS IN HEADER OR BODY:
   - NEVER include tags like `(Recruiter Post)`, `(LinkedIn Hiring Post)`, `(LinkedIn Post)`, `(Wuzzuf)`, or `(Hiring Post)` anywhere in the LaTeX document. Use only the clean professional role title (e.g. `ML Engineer`, `AI & Data Engineer`, `Senior Data Scientist`).
4. POSITIVE ROLE FIT & ZERO SELF-SABOTAGE:
   - NEVER write negative disclaimers, apologies, or disqualifying statements (e.g., NEVER write "although not an ML engineer", "while primarily a Data Engineer", "lacks experience in", or leave a clashing title like `\\textbf{ML Engineer} Data Engineer with...`).
   - Positively reframe the `Profile` paragraph and experience/project bullets to foreground the candidate's verified overlapping skills (e.g. for ML/AI roles, emphasize verified `AI & Data Engineer` experience, `PyTorch`, `TensorFlow`, `Scikit-Learn`, `LangChain`, `Agentic RAG`, `Vertex AI`, `Weaviate`, `MLflow`, `CNNs`, and production ML/data pipelines).
5. ZERO HALLUCINATION:
   - Do not invent employers, dates, degrees, certifications, or unverified tools.
   - Escape LaTeX special characters (`\\&`, `\\%`, `\\$`, `\\#`, `\\_`) properly in text.
""".strip()

REVIEW_SYSTEM_PROMPT = """
You are a meticulous executive CV auditor. Review the tailored LaTeX CV against the base CV and job context.
Highlight the specific alignment improvements made and flag any factual or formatting warnings.
Return valid JSON only.
""".strip()

SELF_CRITIQUE_SYSTEM_PROMPT = """
You are a Principal Resume Quality Critic & LaTeX Verification Engine.
Before a tailored CV is handed to the candidate, you must perform a rigorous Self-Critique & Auto-Correction audit comparing the Draft Tailored LaTeX CV against:
1. The candidate's Base CV (`cv(1)(1).tex` layout standard)
2. The target Job Title and Job Description

Evaluate these 6 mandatory criteria:
1. Header & Source Tag Cleanliness: Must NOT contain `(Recruiter Post)`, `(LinkedIn Hiring Post)`, `(Wuzzuf)`, or any scraper metadata in the header or body.
2. Positive Role Fit & Zero Self-Sabotage: The Profile and bullets must positively position the candidate's verified skills (e.g. AI & Data Engineer roles, PyTorch, TensorFlow, Scikit-Learn, LangChain, Agentic RAG, Vertex AI, MLflow, CNNs, ETL/ELT pipelines) for the target role. It must NEVER contain self-sabotaging disclaimers ("not an ML engineer", "primarily a data engineer") or clashing double titles (`\\textbf{ML Engineer} Data Engineer...`).
3. Layout, Contacts & Spacing Fidelity (`cv(1)(1).tex`): All 4 contact items (Phone, Email, LinkedIn, GitHub) must be on the horizontal contact bar; section order must be `Profile` -> `Professional Experience` -> `Projects` -> `Technical Skills` -> `Education` -> `Certificates` -> `Languages`.
4. Experience, Projects & Stack Integrity: Experience entries must retain role intro summaries, bold bullet lead-ins (`\\textbf{Title:}`), and nested `\\item \\textbf{Stack: ...}` lines; Graduation Project must remain in `Education`.
5. Technical Skills Categorization & Ordering: Skills must be cleanly categorized without raw `\\item` leaks or duplicate skills across categories, with the most relevant category for the target role placed first.
6. Zero-Hallucination Grounding: Every employer, date, metric, degree, and certificate must match the candidate's verified profile.

Return valid JSON only matching the requested schema.
""".strip()


def _resolve_skills(payload: CvFitCreateRequest, parsed_job: Optional[ParsedJob]) -> List[str]:
    if payload.parsed_skills:
        return payload.parsed_skills
    if parsed_job and parsed_job.required_skills:
        return parsed_job.required_skills
    return []


def build_analysis_prompt(
    payload: CvFitCreateRequest,
    crawl_summary: Dict[str, Any],
    company_about_text: str = "",
    parsed_job: Optional[ParsedJob] = None,
) -> str:
    schema = {
        "fit_summary": "string",
        "target_keywords": ["string"],
        "changes_to_make": ["string"],
        "evidence_to_preserve": ["string"],
        "risks": ["string"],
    }
    clean_title = clean_target_job_title(payload.job_title)
    clean_comp = clean_company_name(payload.company_name)
    skills = _resolve_skills(payload, parsed_job)
    skills_str = ", ".join(skills) if skills else "Extract from Job Description"
    return (
        "Analyze how the candidate's base CV should be positively tailored to the target job.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Target Job Title: {clean_title}\n"
        f"Target Company: {clean_comp}\n"
        f"Pre-Extracted Required Skills: {skills_str}\n\n"
        f"Job Description:\n{payload.job_description_text or 'Not provided'}\n\n"
        f"Company Website Summary:\n{company_about_text or crawl_summary.get('summary_text') or 'No website summary available.'}\n\n"
        f"Candidate Additional Comments:\n{payload.user_comments or 'None'}\n\n"
        f"Base CV LaTeX:\n{payload.base_cv_latex}\n"
    )


def build_section_planning_prompt(
    payload: CvFitCreateRequest,
    crawl_summary: Dict[str, Any],
    analysis: Dict[str, Any],
    company_about_text: str = "",
    parsed_job: Optional[ParsedJob] = None,
) -> str:
    schema = {
        "sections": [
            {
                "section_key": "header | profile | experience | projects | skills | education | certificates | languages",
                "section_title": "Display title for the section in LaTeX",
                "is_mandatory": True,
                "rationale": "Why this section is included and how it supports the target role",
                "structure_directive": "How items inside this section should be structured and prioritized",
            }
        ],
        "skills_structure_strategy": "How skills inside Technical Skills should be grouped and ordered for this specific JD",
        "experience_structure_strategy": "How experience roles and achievement bullets should be structured for this JD",
        "overall_structure_rationale": "Executive summary of why this CV structure maximizes ATS and recruiter conversion",
    }
    clean_title = clean_target_job_title(payload.job_title)
    clean_comp = clean_company_name(payload.company_name)
    skills = _resolve_skills(payload, parsed_job) or analysis.get("target_keywords") or []
    skills_str = ", ".join(skills) if skills else "Extract from Job Description"
    return (
        "Decide the optimal CV section & skill prioritization strategy for this candidate and target role.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Target Job Title: {clean_title}\n"
        f"Target Company: {clean_comp}\n"
        f"Required Skills to Prioritize: {skills_str}\n\n"
        f"Stage-1 Alignment Analysis:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        f"Job Description:\n{payload.job_description_text or 'Not provided'}\n\n"
        f"Candidate Base CV LaTeX:\n{payload.base_cv_latex}\n"
    )


def build_generation_prompt(
    payload: CvFitCreateRequest,
    crawl_summary: Dict[str, Any],
    analysis: Dict[str, Any],
    company_about_text: str = "",
    parsed_job: Optional[ParsedJob] = None,
    section_plan: Optional[CvSectionPlan] = None,
) -> str:
    clean_title = clean_target_job_title(payload.job_title)
    clean_comp = clean_company_name(payload.company_name)
    skills = _resolve_skills(payload, parsed_job) or analysis.get("target_keywords") or []
    skills_str = ", ".join(skills) if skills else "See analysis"
    plan_dict = section_plan.model_dump() if section_plan else {}
    plan_json = json.dumps(plan_dict, ensure_ascii=False, indent=2)
    return (
        "Rewrite the candidate's LaTeX CV so it is strongly and positively tailored to the target job while locking the exact `cv(1)(1).tex` visual layout, contact bar, and spacing.\n\n"
        "STRICT REQUIREMENTS:\n"
        "1. Lock the preamble, `\\begin{center}...\\end{center}` header, and `\\end{document}` structure.\n"
        f"2. In the header (`{{\\huge Name | Role}}`) and `\\section{{Profile}}`, use the clean role title `{clean_title}` — NEVER include `(Recruiter Post)` or any source tag, and NEVER leave a clashing title like `ML Engineer Data Engineer with...`.\n"
        "3. Positively bridge the candidate's verified achievements (AI & Data Engineer roles at Angelsta & Multiples, PyTorch, TensorFlow, Scikit-Learn, LangChain, Agentic RAG, Vertex AI, Weaviate, MLflow, CNNs, ETL/ELT pipelines) to match the job description. NEVER include negative disclaimers or state what the candidate is not.\n"
        "4. Preserve role intro paragraphs, `\\textbf{Key achievements:}`, bold achievement lead-ins (`\\textbf{Title:}`), and nested `\\begin{itemize} \\item \\textbf{Stack: ...} \\end{itemize}` blocks in `Professional Experience`.\n"
        "5. Keep `Projects` bullets separate, keep the Graduation Project inside `Education`, and keep `Certificates` and `Languages` complete.\n\n"
        f"Target Job Title (Clean): {clean_title}\n"
        f"Target Company (Clean): {clean_comp}\n"
        f"Required Skills to Foreground: {skills_str}\n\n"
        f"Tailoring Plan:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        f"AI Section & Structure Plan:\n{plan_json}\n\n"
        f"Job Description:\n{payload.job_description_text or 'Not provided'}\n\n"
        f"Company Website Summary:\n{company_about_text or crawl_summary.get('summary_text') or 'No website summary available.'}\n\n"
        f"Candidate Additional Comments:\n{payload.user_comments or 'None'}\n\n"
        f"Base CV LaTeX (Already formatted in `cv(1)(1).tex` layout):\n{payload.base_cv_latex}\n"
    )


def build_self_critique_prompt(
    payload: CvFitCreateRequest,
    draft_cv: str,
    parsed_job: Optional[ParsedJob] = None,
) -> str:
    schema = {
        "passed_all_checks": True,
        "overall_fit_assessment": "Concise 2-sentence executive reasoning on why the tailored CV strongly fits the role and adheres to cv(1)(1).tex",
        "critique_checklist": [
            {
                "criterion": "Header & Source Tag Cleanliness",
                "status": "PASS | FIXED",
                "reasoning": "Verification that header and profile use a clean role title with zero scraper/source tags",
            },
            {
                "criterion": "Positive Role Fit & Zero Self-Sabotage",
                "status": "PASS | FIXED",
                "reasoning": "Verification that verified AI/ML/Data skills are positively framed with zero negative disclaimers",
            },
            {
                "criterion": "Layout, Contact Bar & Spacing Fidelity (cv(1)(1).tex)",
                "status": "PASS | FIXED",
                "reasoning": "Verification that all 4 contacts, justified paragraphs, right-aligned dates, and section order match cv(1)(1).tex",
            },
            {
                "criterion": "Experience, Projects & Stack Integrity",
                "status": "PASS | FIXED",
                "reasoning": "Verification that role intros, bold bullet titles, nested Stack lines, and Graduation Project are intact",
            },
            {
                "criterion": "Technical Skills Categorization & Ordering",
                "status": "PASS | FIXED",
                "reasoning": "Verification that skill categories have zero duplication and prioritize target JD technologies first",
            },
            {
                "criterion": "Zero-Hallucination Grounding",
                "status": "PASS | FIXED",
                "reasoning": "Verification that all employers, dates, degrees, and metrics match the base profile",
            },
        ],
        "flaws_detected": ["List any flaws found in draft_cv, or empty list if none"],
        "corrections_applied": ["List specific improvements/fixes applied during self-critique"],
        "corrected_latex": "Empty string if draft_cv passed all checks; otherwise the complete corrected LaTeX document",
    }
    clean_title = clean_target_job_title(payload.job_title)
    clean_comp = clean_company_name(payload.company_name)
    skills = _resolve_skills(payload, parsed_job)
    skills_str = ", ".join(skills) if skills else "Extract from Job Description"
    return (
        "Critique the Draft Tailored LaTeX CV against the Base CV and Target Job Description before handing it to the user.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Target Job Title: {clean_title}\n"
        f"Target Company: {clean_comp}\n"
        f"Target Skills: {skills_str}\n\n"
        f"Job Description:\n{payload.job_description_text or 'Not provided'}\n\n"
        f"Base CV LaTeX:\n{payload.base_cv_latex}\n\n"
        f"Draft Tailored CV LaTeX:\n{draft_cv}\n"
    )


def build_review_prompt(
    payload: CvFitCreateRequest,
    generated_cv: str,
    section_plan: Optional[CvSectionPlan] = None,
) -> str:
    schema = {
        "notes": ["string"],
        "warnings": ["string"],
    }
    clean_title = clean_target_job_title(payload.job_title)
    clean_comp = clean_company_name(payload.company_name)
    return (
        "Review the generated CV against the base CV and job context.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Job Title: {clean_title}\n"
        f"Company: {clean_comp}\n"
        f"Job Description:\n{payload.job_description_text or 'Not provided'}\n\n"
        f"Base CV LaTeX:\n{payload.base_cv_latex}\n\n"
        f"Generated CV LaTeX:\n{generated_cv}\n"
    )
