"""Phase 5 Verification Gate: pipeline_db, notifications_db, Pipeline CRM + Outreach + Frozen Snapshot, Live SSE Notifications, GDPR .zip Export & Crypto-Shredding Erasure."""

import io
import json
import secrets
import subprocess
import sys
import threading
import time
import zipfile
import httpx

BASE = "http://localhost"


def assert_tables(db: str, expected: list[str]) -> None:
    out = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", db, "-Atc",
            "SELECT tablename FROM pg_tables WHERE schemaname='public';",
        ],
        text=True,
    )
    tables = {line.strip() for line in out.splitlines() if line.strip()}
    missing = [t for t in expected if t not in tables]
    assert not missing, f"Missing {db} tables: {missing}"
    print(f"[PASS] {db} schema verified ({len(expected)} tables).")


def main() -> int:
    assert_tables(
        "pipeline_db",
        ["pipeline_items", "interview_round_notes", "outreach_dispatches", "outbox_events", "processed_events"],
    )
    assert_tables(
        "notifications_db",
        ["notifications", "notification_rules", "email_dispatch_logs", "outbox_events", "processed_events"],
    )

    email = f"phase5_{secrets.token_hex(4)}@tailored.test"
    with httpx.Client(base_url=BASE, timeout=20.0) as client:
        # 1. Register & verify (+2 credits)
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "SecurePassword123!", "full_name": "Mostafa Phase5"},
        )
        assert reg.status_code == 201
        tok = reg.json()["access_token"]
        user_id = reg.json()["user"]["id"]
        otp = reg.json()["dev_otp"]
        h = {"Authorization": f"Bearer {tok}"}
        client.post("/api/v1/auth/verify-email", json={"email": email, "code": otp})

        # Wait for async user.verified starter credit grant (+2 credits)
        for _ in range(30):
            bal = client.get("/api/v1/credits/balance", headers=h)
            if bal.status_code == 200 and bal.json().get("available_credits", 0) >= 2:
                break
            time.sleep(0.5)
        else:
            raise AssertionError("Starter credits not granted after email verification within 15s")

        # 2. Tailor a CV so we have a document to freeze
        jobs = client.get("/api/v1/explore/jobs").json()
        job = next((j for j in jobs if "TechStart" in j["company_name"]), jobs[0])
        tailor = client.post("/api/v1/cv-fit", headers=h, json={"persona_id": "ds_track", "job_id": job["id"]})
        assert tailor.status_code == 202
        doc_id = tailor.json()["doc_id"]

        # 3. Listen to live Notifications SSE stream in background thread while dispatching pipeline item
        sse_lines: list[str] = []

        def read_sse():
            with httpx.Client(base_url=BASE, timeout=15.0) as sc:
                with sc.stream("GET", f"/api/v1/notifications/stream?token={tok}") as resp:
                    for line in resp.iter_lines():
                        sse_lines.append(line)
                        if '"followup"' in line:
                            break

        t = threading.Thread(target=read_sse, daemon=True)
        t.start()
        time.sleep(1.5)

        # 4. Pipeline Create -> Outreach Package -> Dispatch (freezes snapshot & emits pipeline.item.applied) -> Round Note
        pipe = client.post(
            "/api/v1/pipeline",
            headers=h,
            json={"job_id": job["id"], "tailored_cv_doc_id": doc_id, "notes": "Direct recruiter post"},
        )
        assert pipe.status_code == 201, pipe.text
        item_id = pipe.json()["id"]

        outreach = client.get(f"/api/v1/pipeline/{item_id}/outreach", headers=h)
        assert outreach.status_code == 200 and "mail.google.com" in outreach.json()["gmail_web_url"]

        disp = client.post(
            f"/api/v1/pipeline/{item_id}/dispatch",
            headers=h,
            json={"dispatch_channel": "gmail_web", "cv_doc_id": doc_id},
        )
        assert disp.status_code == 200 and disp.json()["status"] == "applied" and disp.json()["frozen_snapshot_id"]

        rnd = client.post(
            f"/api/v1/pipeline/{item_id}/rounds",
            headers=h,
            json={"round_title": "Technical Screen", "interviewer": "Sara Mansour", "notes": "Prepare RAG eval architecture."},
        )
        assert rnd.status_code == 201
        metrics = client.get("/api/v1/pipeline/metrics", headers=h).json()
        assert metrics["applied"] >= 1
        print("[PASS] Pipeline CRM, Outreach Package, Frozen Snapshot & Interview Rounds verified.")

        t.join(timeout=12.0)
        assert any("notification" in l for l in sse_lines), f"SSE notification not pushed: {sse_lines}"

        notifs = client.get("/api/v1/notifications", headers=h).json()
        assert len(notifs) >= 1
        nid = notifs[0]["id"]
        assert client.patch(f"/api/v1/notifications/{nid}/snooze", headers=h, json={"hours": 48}).status_code == 200
        assert client.post("/api/v1/notifications/mark-all-read", headers=h).status_code == 200
        print("[PASS] Live Notifications SSE push, snooze, and mark-all-read verified.")

        # 5. GDPR .zip Export verification
        exp = client.post("/api/v1/account/export", headers=h)
        assert exp.status_code == 200, exp.text
        dl = client.get(exp.json()["download_url"], headers=h)
        assert dl.status_code == 200
        with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
            names = zf.namelist()
            assert "master_profile.json" in names and "documents_manifest.json" in names
        print(f"[PASS] GDPR .zip archive export verified ({len(names)} files).")

        # 6. Send telemetry event before erasure, then execute GDPR Crypto-Shredding Erasure!
        client.post(
            "/api/v1/telemetry/events",
            headers=h,
            json={"events": [{"feature_key": "pipeline.item.create", "event_name": "ui.pipeline.created", "route": "/pipeline"}]},
        )
        time.sleep(2.0)

        er = client.request("DELETE", "/api/v1/account", headers=h, json={"confirm": "DELETE", "password": "SecurePassword123!"})
        assert er.status_code == 202 and er.json()["crypto_shredded"] is True

        # Verify session is immediately dead (401)
        assert client.get("/api/v1/profiles/me", headers=h).status_code == 401

        # Verify privacy_vault_db pseudonym mapping was shredded!
        vault_cnt = subprocess.check_output(
            [
                "docker", "exec", "tailored-postgres",
                "psql", "-U", "tailored_admin", "-d", "privacy_vault_db", "-Atc",
                f"SELECT COUNT(*) FROM identity_pseudonyms WHERE user_id='{user_id}';",
            ],
            text=True,
        ).strip()
        assert vault_cnt == "0", f"privacy_vault_db mapping still present: {vault_cnt}"
        print("[PASS] GDPR Crypto-Shredding & session termination verified.")

    print("\nALL PHASE 5 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
