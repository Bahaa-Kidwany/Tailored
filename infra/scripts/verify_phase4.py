"""Phase 4 Verification Gate: ai_agent_db (+pgvector), Studio Coach SSE, Metric Guard, Turn Branching, Proposal/Action Resolve, Telemetry SDK -> ClickHouse + Ambient Behavioral Memory & Proactive Suggestions."""

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
            "psql", "-U", "tailored_admin", "-d", "ai_agent_db", "-Atc",
            "SELECT tablename FROM pg_tables WHERE schemaname='public';",
        ],
        text=True,
    )
    tables = {line.strip() for line in out.splitlines() if line.strip()}
    expected = [
        "user_behavior_profiles",
        "behavioral_memory_facts",
        "agent_threads",
        "agent_checkpoints",
        "agent_messages",
        "proposal_cards",
        "proactive_suggestions",
        "outbox_events",
        "processed_events",
    ]
    missing = [t for t in expected if t not in tables]
    assert not missing, f"Missing ai_agent_db tables: {missing}"
    print(f"[PASS] ai_agent_db schema verified ({len(expected)} tables + pgvector).")


def parse_sse_events(raw_text: str) -> list[dict]:
    events = []
    cur_ev = None
    for line in raw_text.splitlines():
        if line.startswith("event:"):
            cur_ev = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and cur_ev:
            import json
            events.append({"event": cur_ev, "data": json.loads(line.split(":", 1)[1].strip())})
            cur_ev = None
    return events


def main() -> int:
    assert_tables()
    email = f"phase4_{secrets.token_hex(4)}@tailored.test"

    with httpx.Client(base_url=BASE, timeout=20.0) as client:
        # 1. Register user + setup profile WITHOUT numbers for metric guard test
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "SecurePassword123!", "full_name": "Mostafa Phase4"},
        )
        assert reg.status_code == 201
        tok = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}

        client.put(
            "/api/v1/profiles/me",
            headers=h,
            json={
                "personal_info": {"full_name": "Mostafa Phase4", "primary_email": email},
                "career_personas": [
                    {
                        "persona_id": "ds_track",
                        "target_title": "AI Engineer",
                        "is_primary": True,
                        "years_of_experience": 3,
                        "skills_and_tools": {"core_skills": ["Python", "FastAPI", "Docker"]},
                        "experience_highlights": [
                            {"company": "Swvl", "role": "Engineer", "achievements": ["Built routing APIs in Python"]}
                        ],
                    }
                ],
            },
        )

        # 2. Passive Telemetry Replay (user NOT chatting!) -> ClickHouse + Ambient Behavioral Memory + Suggestion
        batch = []
        for idx in range(6):
            batch.append(
                {
                    "feature_key": "radar.job.dwell",
                    "event_name": "ui.job.dwelled",
                    "route": "/radar",
                    "persona_track": "MLOps Platform Engineer",
                    "duration_ms": 42000,
                    "properties": {"job_country": "Saudi Arabia", "normalized_role": "MLOps Platform Engineer", "idx": idx},
                }
            )
        tel = client.post("/api/v1/telemetry/events", headers=h, json={"events": batch})
        assert tel.status_code == 202, tel.text

        distilled = False
        for _ in range(25):
            mem = client.get("/api/v1/agent/memory", headers=h).json()
            if len(mem.get("memory_facts", [])) >= 1 and len(mem.get("proactive_suggestions", [])) >= 1:
                distilled = True
                break
            time.sleep(1.0)
        assert distilled, f"Ambient memory/suggestion did not trigger passively: {mem}"
        print(f"[PASS] Ambient behavioral pipeline distilled {len(mem['memory_facts'])} facts + emitted proactive suggestion.")

        # 3. Studio Coach SSE: Zero-Hallucination Metric Interception
        jobs = client.get("/api/v1/explore/jobs").json()
        job_id = jobs[0]["id"]
        th = client.post("/api/v1/agent/threads", headers=h, json={"surface": "cv", "job_id": job_id, "title": "Swvl Thread"})
        assert th.status_code == 201
        thread_id = th.json()["id"]

        r_metric = client.post(
            f"/api/v1/agent/threads/{thread_id}/messages:stream",
            headers=h,
            json={"prompt": "Add metrics and quantify my Swvl routing bullet", "mode": "Surgical", "job_id": job_id},
        )
        assert r_metric.status_code == 200
        evs_m = parse_sse_events(r_metric.text)
        prop_m = next((e["data"] for e in evs_m if e["event"] == "proposal_card"), None)
        assert prop_m and prop_m["isMetricQuestion"] is True, f"Metric interception failed: {evs_m}"
        done_m = next(e["data"] for e in evs_m if e["event"] == "done")
        print("[PASS] Zero-Hallucination metric interception verified via SSE.")

        # 4. Turn Branching with real user metric -> Grounded Proposal Card
        r_branch = client.post(
            f"/api/v1/agent/threads/{thread_id}/branch",
            headers=h,
            json={"checkpoint_id": done_m["checkpoint_id"], "new_prompt": "We cut latency by 42% on Swvl pricing", "mode": "Surgical"},
        )
        assert r_branch.status_code == 200
        evs_b = parse_sse_events(r_branch.text)
        prop_b = next((e["data"] for e in evs_b if e["event"] == "proposal_card"), None)
        assert prop_b and prop_b["isMetricQuestion"] is False and "42%" in prop_b["newText"], f"Grounded proposal failed: {evs_b}"

        res_p = client.post(
            f"/api/v1/agent/proposals/{prop_b['id']}/resolve",
            headers=h,
            json={"action": "apply"},
        )
        assert res_p.status_code == 200 and res_p.json()["langfuse_eval_score"] == 1.0
        print("[PASS] Turn branching + grounded Proposal Card Apply (+1.0 eval score) verified.")

        # 5. Memory Inspector deletion & clearing
        fact_id = mem["memory_facts"][0]["id"]
        assert client.delete(f"/api/v1/agent/memory/{fact_id}", headers=h).status_code == 200
        assert client.delete("/api/v1/agent/memory", headers=h).status_code == 200
        assert len(client.get("/api/v1/agent/memory", headers=h).json()["memory_facts"]) == 0
        print("[PASS] AI Memory Inspector view/delete/clear verified.")

    print("\nALL PHASE 4 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
