import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.core.database import init_db, engine
from app.models.job import JobDB
from app.models.pipeline import PipelineItemDB


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_jobs():
    init_db()
    with Session(engine) as session:
        # 1. Recruiter post (eligible)
        recruiter_job = JobDB(
            source_id="linkedin_post_test_99",
            title="Senior AI Infrastructure Engineer",
            company_name="DeepMind Ventures",
            location="Remote",
            url="https://www.linkedin.com/posts/recruiter_deepmind_activity_9999",
            raw_description=(
                "We are hiring a Senior AI Infrastructure Engineer at DeepMind Ventures! "
                "Reach out directly with your resume to recruiter@deepmindventures.com. "
                "Requirements: Python, PyTorch, Kubernetes, Distributed Training."
            ),
            fit_score=92.5,
        )
        session.add(recruiter_job)

        # 2. LinkedIn standard listing (ineligible)
        linkedin_job = JobDB(
            source_id="linkedin_job_test_101",
            title="Software Engineer",
            company_name="Enterprise Corp",
            location="Cairo, Egypt",
            url="https://www.linkedin.com/jobs/view/999111222",
            raw_description="Standard LinkedIn Job listing. Apply via LinkedIn Easy Apply.",
            fit_score=85.0,
        )
        session.add(linkedin_job)

        # 3. Wuzzuf standard listing (ineligible)
        wuzzuf_job = JobDB(
            source_id="wuzzuf_job_test_202",
            title="Backend Developer",
            company_name="Local Startup",
            location="Giza, Egypt",
            url="https://wuzzuf.net/jobs/p/12345-backend-developer",
            raw_description="Standard Wuzzuf Job listing. Apply through Wuzzuf.",
            fit_score=78.0,
        )
        session.add(wuzzuf_job)

        session.commit()
        session.refresh(recruiter_job)
        session.refresh(linkedin_job)
        session.refresh(wuzzuf_job)

        return {
            "recruiter_job": recruiter_job,
            "linkedin_job": linkedin_job,
            "wuzzuf_job": wuzzuf_job,
        }


def test_add_recruiter_post_to_pipeline(client, sample_jobs):
    """Eligible recruiter posts can be added to the pipeline."""
    job = sample_jobs["recruiter_job"]
    resp = client.post("/api/v1/pipeline", json={"job_id": job.id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["job_id"] == job.id
    assert data["status"] == "in_process"  # Because recruiter email was extracted
    assert data["recruiter_email"] == "recruiter@deepmindventures.com"
    assert data["job"]["title"] == "Senior AI Infrastructure Engineer"


def test_add_linkedin_standard_listing_to_pipeline(client, sample_jobs):
    """LinkedIn external portal job listings can also be tracked cleanly in Pipeline."""
    job = sample_jobs["linkedin_job"]
    resp = client.post("/api/v1/pipeline", json={"job_id": job.id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["job_id"] == job.id
    assert data["status"] == "saved"


def test_add_wuzzuf_standard_listing_to_pipeline(client, sample_jobs):
    """Wuzzuf external portal job listings can also be tracked cleanly in Pipeline."""
    job = sample_jobs["wuzzuf_job"]
    resp = client.post("/api/v1/pipeline", json={"job_id": job.id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["job_id"] == job.id
    assert data["status"] == "saved"


def test_list_and_filter_pipeline(client, sample_jobs):
    """Querying pipeline returns eligible items with search filtering."""
    resp = client.get("/api/v1/pipeline?q=deepmind")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert any(i["job"]["company_name"] == "DeepMind Ventures" for i in items)


def test_update_status_and_applied_at(client, sample_jobs):
    """Updating status to applied automatically records applied_at."""
    job = sample_jobs["recruiter_job"]
    list_resp = client.get(f"/api/v1/pipeline?q=deepmind")
    item_id = list_resp.json()[0]["id"]

    patch_resp = client.patch(f"/api/v1/pipeline/{item_id}", json={"status": "applied"})
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == "applied"
    assert updated["applied_at"] is not None


def test_get_outreach_package(client, sample_jobs):
    """Generates 1-click outreach URLs including Gmail and Mailto."""
    job = sample_jobs["recruiter_job"]
    list_resp = client.get(f"/api/v1/pipeline?q=deepmind")
    item_id = list_resp.json()[0]["id"]

    outreach_resp = client.get(f"/api/v1/pipeline/{item_id}/outreach")
    assert outreach_resp.status_code == 200
    data = outreach_resp.json()
    assert data["to_email"] == "recruiter@deepmindventures.com"
    assert "mail.google.com" in data["gmail_web_url"]
    assert "mailto:" in data["mailto_url"]
    assert "Senior AI Infrastructure Engineer" in data["subject"]


def test_pipeline_metrics(client, sample_jobs):
    """Returns accurate pipeline counters."""
    metrics_resp = client.get("/api/v1/pipeline/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total"] >= 1
    assert metrics["applied"] >= 1
    assert metrics["with_email"] >= 1


def test_batch_import(client, sample_jobs):
    """Batch import endpoint migrates client localStorage items into server DB."""
    job = sample_jobs["recruiter_job"]
    payload = {
        "items": [
            {
                "job_id": job.id,
                "status": "interview",
                "notes": "Recruiter replied on LinkedIn, scheduling phone screen.",
            }
        ]
    }
    resp = client.post("/api/v1/pipeline/batch-import", json=payload)
    assert resp.status_code == 200
    items = resp.json()
    match = next((i for i in items if i["job_id"] == job.id), None)
    assert match is not None
    assert match["status"] == "interview"
    assert match["notes"] == "Recruiter replied on LinkedIn, scheduling phone screen."

