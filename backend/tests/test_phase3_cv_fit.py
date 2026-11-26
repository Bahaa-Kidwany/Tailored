import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.models.job import UserProfile
from app.scrapers.mock_scrapers import LinkedInMockSource, WuzzufMockSource
from app.ai.extractor.llm_extractor import JobExtractor
from app.evaluator.engine import JobEvaluator
from app.evaluator.metrics import SkillMatchMetric, ExperienceMetric, LocationMetric
from app.pipeline.job_discovery_pipeline import run_discovery_pipeline
from app.schemas.cv_fit import CvFitCreateRequest, CoverLetterCreateRequest
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.tailor.cv_fit_service import CvFitService
from app.ai.cover_letter.cover_letter_service import CoverLetterService

BASE_LATEX_SAMPLE = r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=1in}

\begin{document}

\section*{Professional Experience}
\textbf{Senior Software Engineer} -- TechCorp \hfill 2021--Present
\begin{itemize}
    \item Built data extraction pipelines and optimized SQL queries.
    \item Mentored junior engineers on backend development.
\end{itemize}

\section*{Education}
\textbf{B.S. in Computer Science} -- Cairo University \hfill 2017--2021

\end{document}
""".strip()

def run_tests():
    print("--- [TEST 1] Initializing Database ---")
    init_db()
    print("Database initialized successfully.")

    print("\n--- [TEST 2] Discovery Pipeline (Phase 2 -> DB Storage) ---")
    profile = UserProfile(
        target_titles=["Data Scientist", "Data Analyst"],
        core_skills=["Python", "SQL", "Pandas"],
        years_of_experience=2,
        preferred_location_type="Remote"
    )
    sources = [LinkedInMockSource(), WuzzufMockSource()]
    extractor = JobExtractor()
    evaluator = JobEvaluator(
        metrics=[
            SkillMatchMetric(weight=4.0),
            ExperienceMetric(weight=2.0),
            LocationMetric(weight=2.0)
        ],
        passing_threshold=65.0
    )
    saved_jobs = run_discovery_pipeline(sources, profile, extractor, evaluator)
    assert len(saved_jobs) > 0, "Expected at least 1 job saved from discovery pipeline."
    target_job = saved_jobs[0]
    print(f"[PASS] Discovery pipeline saved {len(saved_jobs)} jobs. Selected Target Job ID: {target_job.id} ({target_job.title})")

    print("\n--- [TEST 3] CV Fit Service via Saved Job ID (Phase 3 Integration) ---")
    mock_llm = MockLLMProvider()
    cv_service = CvFitService(llm_provider=mock_llm)

    payload = CvFitCreateRequest(
        job_id=target_job.id,
        base_cv_latex=BASE_LATEX_SAMPLE,
        user_comments="Focus on production ML and backend reliability."
    )

    result = cv_service.create_cv_fit(payload)
    print(f"CV Fit Created! Doc ID: {result.doc_id}")
    print(f"Target Role: {result.job_title} at {result.company_name}")
    print(f"Tailoring applied: {result.tailoring_applied}")
    print(f"Compile status: {result.compile_status}")
    print(f"Notes logged: {len(result.notes)}")

    assert result.doc_id is not None
    assert result.tailoring_applied is True
    assert result.job_title == target_job.title
    assert result.company_name == target_job.company_name
    assert result.section_plan is not None
    assert result.section_plan.mandatory_sections_satisfied is True
    for mand in ("header", "profile", "skills", "education"):
        assert mand in result.section_plan.section_order, f"Mandatory section '{mand}' missing from section_plan!"
    from app.ai.formatters.latex_template import validate_mandatory_latex_sections
    mand_ok, missing_mand = validate_mandatory_latex_sections(result.tailored_latex_content or "")
    assert mand_ok, f"Mandatory sections missing from final LaTeX: {missing_mand}"
    print(f"[PASS] CV Fit generation linked to JobDB verified. Planned sections: {result.section_plan.section_order}")

    print("\n--- [TEST 4] Cover Letter Generation via Job ID ---")
    cl_service = CoverLetterService(llm_provider=mock_llm)
    cl_req = CoverLetterCreateRequest(
        job_id=target_job.id,
        base_cv_text="5 years experience in Python, FastAPI, distributed data pipelines and ML.",
    )
    cl_res = cl_service.generate_cover_letter(cl_req)
    print(f"Cover letter created! ID: {cl_res.doc_id}")
    print(f"Subject: {cl_res.subject_line}")
    print(f"Target: {cl_res.job_title} at {cl_res.company_name}")
    assert cl_res.doc_id is not None
    assert cl_res.company_name == target_job.company_name
    print("[PASS] Cover letter generation linked to JobDB verified.")

    print("\n--- [TEST 5] FastAPI Endpoints Verification ---")
    client = TestClient(app)
    
    # 5.1 Health check
    r_health = client.get("/health")
    assert r_health.status_code == 200

    # 5.2 List jobs
    r_jobs = client.get("/api/v1/jobs")
    assert r_jobs.status_code == 200
    jobs_data = r_jobs.json()
    assert len(jobs_data) >= len(saved_jobs)
    print(f"[PASS] /api/v1/jobs returned {len(jobs_data)} jobs.")

    # 5.3 List CV Fits
    r_cvs = client.get("/api/v1/cv-fit")
    assert r_cvs.status_code == 200
    cv_list = r_cvs.json()
    assert len(cv_list) > 0
    print(f"[PASS] /api/v1/cv-fit returned {len(cv_list)} tailored CVs.")

    # 5.4 List Cover Letters
    r_cls = client.get("/api/v1/cover-letter")
    assert r_cls.status_code == 200
    cl_list = r_cls.json()
    assert len(cl_list) > 0
    print(f"[PASS] /api/v1/cover-letter returned {len(cl_list)} cover letters.")

    # 5.5 Verify LaTeX escaping, profile synthesis, bullet diffs, and PDF/TeX download
    from app.ai.formatters.latex_template import escape_latex, generate_base_latex_from_profile
    from app.ai.formatters.latex_engine import is_complete_latex_document
    import json

    escaped = escape_latex("R&D 100% $50k #1 user_name {test}")
    assert r"\&" in escaped and r"\%" in escaped and r"\$" in escaped and r"\#" in escaped and r"\_" in escaped

    sample_path = Path(__file__).resolve().parent / "fixtures" / "sample_user_profile.json"
    sample_profile_dict = json.loads(sample_path.read_text(encoding="utf-8"))
    r_prof = client.post("/api/v1/profiles", json=sample_profile_dict)
    assert r_prof.status_code in (200, 201)
    created_prof_id = r_prof.json()["id"]

    # Tailor CV without supplying base_cv_latex (synthesized from profile_id)
    r_tailor = client.post("/api/v1/cv-fit", json={
        "profile_id": created_prof_id,
        "persona_id": "data_scientist_track",
        "job_id": target_job.id,
        "job_title": target_job.title,
        "company_name": target_job.company_name,
        "job_description_text": target_job.raw_description,
        "fit_score": 94.2,
        "parsed_skills": ["Python", "FastAPI", "SQL", "Docker"],
    })
    assert r_tailor.status_code == 200
    tailored_data = r_tailor.json()
    assert tailored_data["profile_id"] == created_prof_id
    assert is_complete_latex_document(tailored_data["tailored_latex_content"])
    assert len(tailored_data["bullet_diffs"]) > 0
    assert tailored_data.get("section_plan") is not None
    assert tailored_data["section_plan"]["mandatory_sections_satisfied"] is True
    for mand in ("header", "profile", "skills", "education"):
        assert mand in tailored_data["section_plan"]["section_order"]
    mand_ok_api, missing_api = validate_mandatory_latex_sections(tailored_data["tailored_latex_content"])
    assert mand_ok_api, f"API tailored CV missing mandatory sections: {missing_api}"
    print(f"[PASS] Synthesized CV Fit from profile_id={created_prof_id} with {len(tailored_data['bullet_diffs'])} surgical bullet diffs and dynamic section order: {tailored_data['section_plan']['section_order']}.")

    # Check profile tailored-cvs endpoint
    r_prof_cvs = client.get(f"/api/v1/profiles/{created_prof_id}/tailored-cvs")
    assert r_prof_cvs.status_code == 200
    assert any(d["doc_id"] == tailored_data["doc_id"] for d in r_prof_cvs.json())

    # Check PDF and TeX artifact downloads
    doc_id = tailored_data["doc_id"]
    r_dl_tex = client.get(f"/api/v1/cv-fit/{doc_id}/download/tex")
    assert r_dl_tex.status_code == 200
    assert r"\documentclass" in r_dl_tex.text

    r_dl_pdf = client.get(f"/api/v1/cv-fit/{doc_id}/download/pdf")
    assert r_dl_pdf.status_code == 200
    assert r_dl_pdf.content.startswith(b"%PDF-")
    print("[PASS] Both .tex and .pdf downloads verified.")

    print("\n============================================================")
    print("ALL TESTS PASSED! PIPELINE & CV FIT ARE CLEAN AND ALIGNED! ")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
