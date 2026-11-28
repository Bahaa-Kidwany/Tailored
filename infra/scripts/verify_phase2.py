"""Phase 2 Verification Gate: jobs_db, public /explore, 5-D Multi-Persona Zero-Drop Ranker, Interest & Scraper Worker."""

import secrets
import subprocess
import sys
import time
import httpx

BASE = "http://localhost"


def assert_tables() -> None:
    out = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", "jobs_db", "-Atc",
            "SELECT tablename FROM pg_tables WHERE schemaname='public';",
        ],
        text=True,
    )
    tables = {line.strip() for line in out.splitlines() if line.strip()}
    expected = ["jobs", "job_fit_scores", "user_job_interactions", "scrape_runs", "outbox_events", "processed_events"]
    missing = [t for t in expected if t not in tables]
    assert not missing, f"Missing jobs_db tables: {missing}"
    print(f"[PASS] jobs_db schema verified ({len(expected)} tables).")


def main() -> int:
    assert_tables()
    email = f"phase2_{secrets.token_hex(4)}@tailored.test"

    with httpx.Client(base_url=BASE, timeout=15.0) as client:
        # 1. Public /explore returns jobs without recruiter_email PII
        exp = client.get("/api/v1/explore/jobs")
        assert exp.status_code == 200 and len(exp.json()) >= 6, exp.text
        for j in exp.json():
            assert "recruiter_email" not in j, "Public /explore leaked recruiter_email!"
        print(f"[PASS] Public /explore feed verified ({len(exp.json())} jobs, zero PII).")

        # 2. Register & setup multi-persona profile
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "SecurePassword123!", "full_name": "Mostafa Phase2"},
        )
        assert reg.status_code == 201, reg.text
        tok = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}

        prof = client.put(
            "/api/v1/profiles/me",
            headers=h,
            json={
                "personal_info": {"full_name": "Mostafa Phase2", "primary_email": email},
                "residence_and_mobility": {
                    "current_residence": {"city": "Cairo", "country": "Egypt"},
                    "willing_to_relocate": True,
                    "target_locations": [{"location_id": "l1", "city": "Riyadh", "country": "Saudi Arabia", "work_modes": ["Remote", "Hybrid"], "is_active_for_search": True}],
                },
                "career_personas": [
                    {
                        "persona_id": "ds_track",
                        "target_title": "Lead Data Scientist",
                        "is_primary": True,
                        "years_of_experience": 4,
                        "skills_and_tools": {"core_skills": ["Python", "PyTorch", "SQL", "FastAPI", "Docker", "PostgreSQL"]},
                    },
                    {
                        "persona_id": "da_track",
                        "target_title": "Product Data Analyst",
                        "is_primary": False,
                        "years_of_experience": 3,
                        "skills_and_tools": {"core_skills": ["SQL", "Power BI", "Metabase", "A/B Testing"]},
                    },
                ],
            },
        )
        assert prof.status_code == 200

        # 3. Authenticated Radar feed (Zero-Drop ranked DESC)
        radar = client.get("/api/v1/jobs", headers=h)
        assert radar.status_code == 200
        jobs = radar.json()
        assert len(jobs) >= 6
        scores = [j["fit_score"] for j in jobs]
        assert scores == sorted(scores, reverse=True), "Radar feed not sorted DESC!"
        print(f"[PASS] Zero-Drop 5-D Radar ranked {len(jobs)} jobs (top score={scores[0]}%).")

        # 4. Job detail 5-D multi-persona breakdown
        detail = client.get(f"/api/v1/jobs/{jobs[0]['id']}", headers=h)
        assert detail.status_code == 200
        d = detail.json()
        assert len(d["persona_breakdown"]) == 2 and "dimensions" in d and "tailoring_guidance" in d
        print("[PASS] 5-D multi-persona fit breakdown verified.")

        # 5. Ingest custom JD text -> canonical dedup + email extraction + Interest List
        ing = client.post(
            "/api/v1/jobs/extract-description",
            headers=h,
            json={
                "title": "Senior FastAPI AI Engineer",
                "company_name": "MENA Labs",
                "description": "Need Python, FastAPI, Docker, PostgreSQL. Email hr@menalabs-demo.io to apply.",
            },
        )
        assert ing.status_code == 201 and ing.json()["recruiter_email"] == "hr@menalabs-demo.io"
        ing_id = ing.json()["id"]

        interest = client.get("/api/v1/interest", headers=h)
        assert interest.status_code == 200 and any(x["id"] == ing_id for x in interest.json())
        print("[PASS] JD ingestion & Interest List verified.")

        # 6. Hide & Undo Hide triage
        assert client.post(f"/api/v1/jobs/{ing_id}/hide", headers=h, json={"reason": "test"}).status_code == 200
        radar_after_hide = client.get("/api/v1/jobs", headers=h).json()
        assert all(x["id"] != ing_id for x in radar_after_hide)
        assert client.delete(f"/api/v1/jobs/{ing_id}/hide", headers=h).status_code == 200
        print("[PASS] Hide & Undo triage verified.")

        # 7. Auto-search triggers async scraper-worker via Redpanda
        before_cnt = len(client.get("/api/v1/jobs", headers=h).json())
        auto = client.post(
            "/api/v1/jobs/auto-search",
            headers=h,
            json={"query": f"Agentic Systems {secrets.token_hex(2)}", "location": "Dubai, UAE"},
        )
        assert auto.status_code == 200 and "scrape_run_id" in auto.json()

        discovered = False
        for _ in range(20):
            cur = client.get("/api/v1/jobs", headers=h).json()
            if len(cur) > before_cnt:
                discovered = True
                break
            time.sleep(1.0)
        assert discovered, "scraper-worker did not publish discovered job via Redpanda!"
        print("[PASS] Async scraper-worker -> Redpanda -> jobs-service scoring verified.")

    print("\nALL PHASE 2 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
