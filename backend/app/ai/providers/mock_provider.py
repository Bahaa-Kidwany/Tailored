import json
import re
from typing import Optional, List, Dict, Any
from app.ai.providers.base import BaseLLMProvider
from app.ai.formatters.latex_template import (
    clean_target_job_title,
    clean_company_name,
)
from app.ai.formatters.latex_engine import _extract_balanced_macros


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock Provider preserving exact cv(1)(1).tex structure, positive role bridging, and self-critique."""

    def _extract_job_meta(self, user_text: str) -> tuple[str, str, List[str]]:
        title_match = re.search(r"(?:Target )?Job Title(?:\s*\(Clean\))?:\s*(.+)", user_text)
        company_match = re.search(r"(?:Target )?Company(?:\s*Name|\s*\(Clean\))?:\s*(.+)", user_text)
        skills_match = re.search(
            r"(?:Pre-Extracted Required Skills|Required Skills to Prioritize|Required Skills to Foreground|Required Skills|Target Skills):\s*(.+)",
            user_text,
        )

        raw_title = title_match.group(1).strip() if title_match else "AI & Data Engineer"
        raw_company = company_match.group(1).strip() if company_match else "Target Organization"
        job_title = clean_target_job_title(raw_title, fallback_title="AI & Data Engineer")
        company = clean_company_name(raw_company, fallback_company="Target Organization")

        if skills_match and skills_match.group(1).strip():
            skills = [s.strip() for s in skills_match.group(1).split(",") if s.strip()]
        else:
            skills = ["Python", "PyTorch", "TensorFlow", "FastAPI", "SQL", "Docker"]
        return job_title, company, skills

    def _build_mock_section_plan(self, job_title: str, company: str, skills: List[str]) -> Dict[str, Any]:
        sections: List[Dict[str, Any]] = [
            {
                "section_key": "header",
                "section_title": "Header & Contact Info",
                "is_mandatory": True,
                "rationale": f"Centered identity header aligning candidate headline with {job_title}.",
                "structure_directive": "Centered Name | Clean Target Role Title, Location, and single-line FontAwesome contact bar.",
            },
            {
                "section_key": "profile",
                "section_title": "Profile",
                "is_mandatory": True,
                "rationale": f"Full-width justified executive summary bridging verified AI, ML, and Data Engineering achievements to {job_title}.",
                "structure_directive": "3-4 line summary opening with bold target role title and core verified competencies.",
            },
            {
                "section_key": "experience",
                "section_title": "Professional Experience",
                "is_mandatory": False,
                "rationale": f"Demonstrates production AI & Data Engineering track record relevant to {job_title} at {company}.",
                "structure_directive": "Reverse-chronological roles with right-aligned dates, role summary, bold-titled \\resumeItem bullets, and nested Stack items.",
            },
            {
                "section_key": "projects",
                "section_title": "Projects",
                "is_mandatory": False,
                "rationale": f"Showcases end-to-end production AI, ML, and data platform architectures relevant to {company}.",
                "structure_directive": "Project headings with inline tech stack and multi-bullet \\resumeItem implementation details.",
            },
            {
                "section_key": "skills",
                "section_title": "Technical Skills",
                "is_mandatory": True,
                "rationale": f"Categorized technical skills matrix ordered to foreground {', '.join(skills[:4])}.",
                "structure_directive": "Clean categorized skill rows matching cv(1)(1).tex with zero duplication across categories.",
            },
            {
                "section_key": "education",
                "section_title": "Education",
                "is_mandatory": True,
                "rationale": "Academic degree, GPA, and Deep Learning Graduation Project verification.",
                "structure_directive": "Degree, institution, right-aligned dates, GPA, and Graduation Project block.",
            },
            {
                "section_key": "certificates",
                "section_title": "Certificates",
                "is_mandatory": False,
                "rationale": "Verified professional certifications with issuer, clickable credential link, and date.",
                "structure_directive": "Two-column \\resumeSubheading entries with issuer, certificate title, and issue date.",
            },
            {
                "section_key": "languages",
                "section_title": "Languages",
                "is_mandatory": False,
                "rationale": "Spoken languages and fluency levels matching cv(1)(1).tex.",
                "structure_directive": "Bold language name and italicized proficiency level.",
            },
        ]
        return {
            "sections": sections,
            "skills_structure_strategy": (
                f"Prioritize {', '.join(skills[:4])} in the top skill category, followed by programming languages, "
                "data engineering & cloud, databases & vector search, and analytics."
            ),
            "experience_structure_strategy": (
                f"Preserve cv(1)(1).tex layout: role subheadings with right-aligned dates, role intro paragraph, "
                f"bold-titled \\resumeItem bullets, and nested Stack lines tailored to {job_title}."
            ),
            "overall_structure_rationale": (
                f"Locked to authentic cv(1)(1).tex layout (Profile -> Professional Experience -> Projects -> "
                f"Technical Skills -> Education -> Certificates -> Languages) for {job_title} at {company}."
            ),
        }

    def _surgically_rewrite_bullet(self, bullet: str, idx: int, job_title: str, skills: List[str]) -> str:
        b = bullet.strip()
        primary_skill = skills[0] if skills else "Python"
        secondary_skill = skills[1] if len(skills) > 1 else "PyTorch"

        if "financial model automation pipeline" in b.lower():
            return (
                r"\textbf{Financial Model Automation Pipeline:} Engineered a production Python and Vertex AI pipeline "
                r"to dynamically synthesize complex financial models, automating feature extraction and structuring of "
                r"business assumptions to cut manual overhead and ensure high-integrity downstream analytics."
            )
        if "interactive market intelligence platform" in b.lower():
            return (
                r"\textbf{Interactive Market Intelligence Platform:} Architected an analytical platform and data "
                r"warehouse to ingest, model, and surface MENA investment trends, building automated backend reporting "
                r"pipelines that dynamically generate granular market intelligence."
            )
        if "financial data orchestration" in b.lower():
            return (
                r"\textbf{Financial Data Orchestration:} Built end-to-end data ingestion and vector retrieval pipelines "
                r"(Weaviate, Huggingface, Ollama) powering multi-step LLM reasoning systems and personalized analytics."
            )
        if "margin" in b.lower() or "pricing" in b.lower():
            return (
                f"Architected production {primary_skill} and {secondary_skill} dynamic route pricing regression "
                f"models that improved ride margins by 7.4\\% across high-concurrency regional fleets."
            )
        if "sentiment" in b.lower() or "reviews" in b.lower():
            return (
                f"Engineered and deployed low-latency NLP sentiment inference microservices ({primary_skill}, Docker) "
                f"processing 50k+ user reviews monthly with automated drift monitoring."
            )
        return b

    def generate(
        self,
        system_prompt: str,
        user_text: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.2,
    ) -> str:
        job_title, company, skills = self._extract_job_meta(user_text)

        # 1. Stage 1 Analysis prompt
        if "Schema:" in user_text and "fit_summary" in user_text:
            return json.dumps({
                "fit_summary": (
                    f"Strong verified candidate alignment for {job_title} at {company}. "
                    f"Verified AI & Data Engineer roles, {', '.join(skills[:4])}, and production ML/data pipelines directly map to target requirements."
                ),
                "target_keywords": skills[:6],
                "changes_to_make": [
                    f"Use clean target role title '{job_title}' in header and Profile without any scraper/source tags.",
                    f"Positively bridge verified AI/ML and Data Engineering achievements ({', '.join(skills[:3])}) in Profile and Experience.",
                    "Preserve exact cv(1)(1).tex section order, contact bar, role intros, bold bullet titles, and nested Stack items.",
                ],
                "evidence_to_preserve": [
                    "Verified AI & Data Engineer experience at Angelsta and Multiples, plus AMIT/DEPI instruction",
                    "Production AI/ML projects (JobFinder, Sanad Legal Hybrid Search, CNN Bell Peppers Graduation Project)",
                ],
                "risks": [],
            })

        # 2. Stage 1.5 AI Section & Structure Planning prompt
        if "skills_structure_strategy" in user_text and "Schema:" in user_text:
            return json.dumps(self._build_mock_section_plan(job_title, company, skills))

        # 3. Stage 4 Self-Critique prompt
        if "passed_all_checks" in user_text and "critique_checklist" in user_text:
            return json.dumps({
                "passed_all_checks": True,
                "overall_fit_assessment": (
                    f"Tailored CV for {job_title} at {company} strictly adheres to cv(1)(1).tex layout, "
                    f"strips all source tags, and positively frames verified {', '.join(skills[:3])} competencies with zero self-sabotage."
                ),
                "critique_checklist": [
                    {
                        "criterion": "Header & Source Tag Cleanliness",
                        "status": "PASS",
                        "reasoning": f"Header uses clean title '{job_title}' with zero '(Recruiter Post)' or scraper tags.",
                    },
                    {
                        "criterion": "Positive Role Fit & Zero Self-Sabotage",
                        "status": "PASS",
                        "reasoning": "Profile and experience bullets positively foreground verified AI, ML, and Data Engineering achievements without negative disclaimers.",
                    },
                    {
                        "criterion": "Layout, Contact Bar & Spacing Fidelity (cv(1)(1).tex)",
                        "status": "PASS",
                        "reasoning": "Single-line contact bar (Phone, Email, LinkedIn, GitHub), full-width justified paragraphs, and exact cv(1)(1).tex section order verified.",
                    },
                    {
                        "criterion": "Experience, Projects & Stack Integrity",
                        "status": "PASS",
                        "reasoning": "Role intro paragraphs, bold achievement lead-ins, nested Stack items, and Graduation Project under Education are intact.",
                    },
                    {
                        "criterion": "Technical Skills Categorization & Ordering",
                        "status": "PASS",
                        "reasoning": "Skills are grouped into non-overlapping categories with target domain skills prioritized at the top.",
                    },
                    {
                        "criterion": "Zero-Hallucination Grounding",
                        "status": "PASS",
                        "reasoning": "All employers, dates, degrees, and metrics match the verified base profile.",
                    },
                ],
                "flaws_detected": [],
                "corrections_applied": [],
                "corrected_latex": "",
            })

        # 4. Stage 3 Review prompt
        if "Generated CV LaTeX:" in user_text:
            return json.dumps({
                "notes": [
                    f"Header and Profile aligned to clean role title '{job_title}' (zero source tags).",
                    "Self-critique verified positive framing of AI/ML & Data Engineering achievements with zero negative disclaimers.",
                    "Exact cv(1)(1).tex layout, horizontal contact bar, role intros, nested Stack items, and full-width justification verified.",
                ],
                "warnings": [],
            })

        # 5. Cover Letter prompt
        if "cover letter" in system_prompt.lower() or "cover letter" in user_text.lower():
            return (
                "Dear Hiring Team,\n\n"
                f"I am writing to express my strong enthusiasm for the {job_title} role at {company}. "
                "With hands-on experience as an AI & Data Engineer building production machine learning workflows, "
                "LLM/Agentic RAG pipelines, and scalable data infrastructure, my background directly aligns with your requirements.\n\n"
                "Thank you for your consideration. I look forward to connecting soon.\n\n"
                "Sincerely,\nCandidate"
            )

        # 6. Stage 2 LaTeX Generation prompt
        base_match = re.search(
            r"(?:Base CV LaTeX[^\n]*|Existing CV LaTeX):\s*\n(.*?)(?:\n\nYour previous attempt|$)",
            user_text,
            re.DOTALL,
        )
        if base_match:
            base_latex = base_match.group(1).strip()
            tailored = base_latex

            # Safely rewrite the first 3 \resumeItem{...} blocks using balanced brace extraction
            macro_calls = _extract_balanced_macros(tailored, "resumeItem", 1)
            if macro_calls:
                for idx, (args, m_start, m_end) in reversed(list(enumerate(macro_calls[:3]))):
                    orig_inner = args[0]
                    new_inner = self._surgically_rewrite_bullet(orig_inner, idx, job_title, skills)
                    if new_inner != orig_inner:
                        tailored = tailored[:m_start] + rf"\resumeItem{{{new_inner}}}" + tailored[m_end:]
            return tailored

        return "% Tailored CV LaTeX\n\\documentclass{article}\n\\begin{document}\nHello World\n\\end{document}"
