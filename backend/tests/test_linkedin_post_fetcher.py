import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest
from app.pipeline.url_job_fetcher import UrlJobFetcher
from app.models.job import RawJob, JobDB
from app.api.routes.jobs import format_job_response, extract_recruiter_email

def test_is_linkedin_post():
    fetcher = UrlJobFetcher()
    assert fetcher._is_linkedin_post("https://www.linkedin.com/posts/recruiter-name_we-are-hiring-activity-7123456789-abcd")
    assert fetcher._is_linkedin_post("https://www.linkedin.com/feed/update/urn:li:activity:7123456789012345678/")
    assert fetcher._is_linkedin_post("https://www.linkedin.com/feed/update/urn:li:share:7123456789012345678/")
    assert not fetcher._is_linkedin_post("https://www.linkedin.com/jobs/view/1234567890/")
    assert not fetcher._is_linkedin_post("https://wuzzuf.net/jobs/p/12345-python-engineer")

def test_extract_activity_id():
    fetcher = UrlJobFetcher()
    url1 = "https://www.linkedin.com/posts/recruiter-name_we-are-hiring-activity-7123456789012345678-abcd"
    assert fetcher._extract_activity_id(url1) == "7123456789012345678"

    url2 = "https://www.linkedin.com/feed/update/urn:li:activity:7198765432109876543/"
    assert fetcher._extract_activity_id(url2) == "7198765432109876543"

def test_is_valid_job_content():
    fetcher = UrlJobFetcher()
    # Authwall / sign-in stubs must be rejected
    stub1 = RawJob(
        source_type="linkedin_posts",
        source_id="1",
        title="Sign In | LinkedIn",
        company_name="LinkedIn",
        location="Cairo",
        raw_description="Join now to view this job",
        url="https://linkedin.com",
    )
    assert not fetcher._is_valid_job_content(stub1)

    stub2 = RawJob(
        source_type="linkedin_posts",
        source_id="2",
        title="Senior Python Developer",
        company_name="Tech",
        location="Cairo",
        raw_description="Sign in to view more content on LinkedIn and apply today",
        url="https://linkedin.com",
    )
    assert not fetcher._is_valid_job_content(stub2)

    # Real job post content must pass
    real_desc = (
        "We are hiring a Senior Python Engineer at TechCorp. Must have 4+ years experience with FastAPI, "
        "PostgreSQL, Docker, and Kubernetes. Please send your CV to hiring@techcorp.com"
    )
    valid_job = RawJob(
        source_type="linkedin_posts",
        source_id="3",
        title="Senior Python Engineer",
        company_name="TechCorp",
        location="Cairo, Egypt",
        raw_description=real_desc,
        url="https://linkedin.com/posts/techcorp-hiring",
    )
    assert fetcher._is_valid_job_content(valid_job)

def test_extract_email():
    text = "Interested candidates should send their resume to careers.egypt@example.com before Sunday."
    assert extract_recruiter_email(text) == "careers.egypt@example.com"

    text2 = "Contact me at recruiter+jobs@talent.co.uk or on LinkedIn."
    assert extract_recruiter_email(text2) == "recruiter+jobs@talent.co.uk"

    no_email = "Apply directly via the company portal link."
    assert extract_recruiter_email(no_email) is None

def test_format_job_response_source_detection():
    # 1. Recruiter post
    post_job = JobDB(
        id=1,
        source_type="linkedin_posts",
        source_id="post-123",
        title="Python Tech Lead",
        company_name="Innovate Ltd",
        location="Cairo, Egypt",
        raw_description="Send CV to hr@innovate.com",
        url="https://www.linkedin.com/posts/innovate_hiring-activity-71234",
    )
    formatted_post = format_job_response(post_job)
    assert formatted_post.source_type == "linkedin_posts"
    assert formatted_post.recruiter_email == "hr@innovate.com"

    # 2. LinkedIn Job listing
    linkedin_job = JobDB(
        id=2,
        source_type="linkedin",
        source_id="job-456",
        title="Backend Engineer",
        company_name="Global Tech",
        location="Giza, Egypt",
        raw_description="Apply online through LinkedIn",
        url="https://www.linkedin.com/jobs/view/456",
    )
    formatted_li = format_job_response(linkedin_job)
    assert formatted_li.source_type == "linkedin"
    assert formatted_li.recruiter_email is None

    # 3. Wuzzuf Job
    wuzzuf_job = JobDB(
        id=3,
        source_type="wuzzuf",
        source_id="wuzzuf-789",
        title="Full Stack Developer",
        company_name="Local Startup",
        location="Alexandria, Egypt",
        raw_description="Wuzzuf job details",
        url="https://wuzzuf.net/jobs/p/789",
    )
    formatted_wuzzuf = format_job_response(wuzzuf_job)
    assert formatted_wuzzuf.source_type == "wuzzuf"

    # 4. Web generic job (should NOT become wuzzuf!)
    web_job = JobDB(
        id=4,
        source_type="web",
        source_id="web-999",
        title="AI Engineer",
        company_name="Deep Mind Partners",
        location="Remote",
        raw_description="Reach out directly to jobs@deepmindpartners.ai",
        url="https://jobs.lever.co/deepmind/999",
    )
    formatted_web = format_job_response(web_job)
    assert formatted_web.source_type == "web"
    assert formatted_web.recruiter_email == "jobs@deepmindpartners.ai"

def test_ingest_job_from_description():
    from app.pipeline.job_search_service import JobSearchService

    service = JobSearchService()
    raw_text = (
        "We are hiring a Senior Machine Learning Engineer at FalconAI in Cairo, Egypt. "
        "Looking for someone skilled in Python, PyTorch, Docker, FastAPI, and PostgreSQL. "
        "Send your resume to talent@falconai.tech."
    )
    saved = service.ingest_job_from_description(raw_description=raw_text)
    assert saved is not None
    assert "Machine Learning" in saved.title
    assert "FalconAI" in saved.company_name or "Falconai" in saved.company_name
    assert saved.fit_score >= 80.0

    formatted = format_job_response(saved)
    assert formatted.source_type == "linkedin_posts" or formatted.source_type == "recruiter_post"
    assert formatted.recruiter_email == "talent@falconai.tech"
    assert "Python" in formatted.parsed_skills or "PyTorch" in formatted.parsed_skills

def test_extract_description_api_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "description": "TechCorp is looking for a Lead Python Developer with 4+ years in FastAPI and Docker. Apply to jobs@techcorp.io"
    }
    response = client.post("/api/v1/jobs/extract-description", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["title"] or "Developer" in data["title"]
    assert data["recruiter_email"] == "jobs@techcorp.io"
    assert data["source_type"] in ["recruiter_post", "linkedin_posts"]
    assert data["fit_score"] >= 80.0
