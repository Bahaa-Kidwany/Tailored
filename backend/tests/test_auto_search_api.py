import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

client = TestClient(app)

def test_job_search_and_scraping_lifecycle():
    init_db()

    # 1. Trigger auto-search
    payload = {
        "profile_id": 1,
        "query": "Data Scientist",
        "location": "Cairo",
        "min_score": 60.0
    }
    res = client.post("/api/v1/jobs/auto-search", json=payload)
    assert res.status_code == 200, f"Auto search failed: {res.text}"
    jobs = res.json()
    assert len(jobs) > 0, "Expected at least 1 discovered job"

    top_job = jobs[0]
    print(f"Top discovered job: {top_job['title']} @ {top_job['company_name']} (Score: {top_job['fit_score']}%)")
    assert "fit_score" in top_job
    assert "is_high_match" in top_job
    assert "parsed_skills" in top_job
    assert "url" in top_job

    # 2. Test GET /api/v1/jobs with filters
    list_res = client.get("/api/v1/jobs?min_score=80.0")
    assert list_res.status_code == 200
    high_match_jobs = list_res.json()
    for j in high_match_jobs:
        assert j["fit_score"] >= 80.0
    print(f"Verified {len(high_match_jobs)} jobs with score >= 80%")

    # 3. Test GET /api/v1/jobs/{job_id}
    job_id = top_job["id"]
    detail_res = client.get(f"/api/v1/jobs/{job_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == job_id
    assert len(detail["raw_description"]) > 20
    print(f"Successfully retrieved detail for job ID: {job_id}")

if __name__ == "__main__":
    test_job_search_and_scraping_lifecycle()
    print("Auto-search and Job Radar API tests passed successfully!")
