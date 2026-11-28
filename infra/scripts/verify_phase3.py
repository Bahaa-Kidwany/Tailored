"""Phase 3 Verification Gate: billing_db, documents_db, Starter Credits, Paymob Webhook, CV Tailor Hold->Compile->Commit, 0cr Unlock, Chaos Auto-Refund, and Sandbox Net Isolation."""

import hashlib
import hmac
import json
import secrets
import subprocess
import sys
import time
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


def check_latex_sandbox_isolation() -> None:
    # Verify latex-worker is on sandbox_net (internal) and has NO internet egress
    res = subprocess.run(
        [
            "docker", "exec", "tailored-latex-worker",
            "python", "-c",
            "import urllib.request; urllib.request.urlopen('https://1.1.1.1', timeout=3)",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0, "SECURITY FAIL: latex-worker reached external network!"
    print("[PASS] latex-worker sandbox_net egress isolation verified (outbound blocked).")


def main() -> int:
    assert_tables(
        "billing_db",
        ["credit_wallets", "credit_ledger_entries", "credit_holds", "credit_packs_catalog", "payment_orders", "outbox_events", "processed_events"],
    )
    assert_tables(
        "documents_db",
        ["generated_documents", "document_versions", "frozen_application_snapshots", "gdpr_export_jobs", "outbox_events", "processed_events"],
    )
    check_latex_sandbox_isolation()

    email = f"phase3_{secrets.token_hex(4)}@tailored.test"
    with httpx.Client(base_url=BASE, timeout=20.0) as client:
        # 1. Register + Verify Email -> +2 Starter Credits via Redpanda Outbox
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "SecurePassword123!", "full_name": "Mostafa Phase3"},
        )
        assert reg.status_code == 201, reg.text
        tok = reg.json()["access_token"]
        otp = reg.json()["dev_otp"]
        h = {"Authorization": f"Bearer {tok}"}

        ver = client.post("/api/v1/auth/verify-email", json={"email": email, "code": otp})
        assert ver.status_code == 200

        granted = False
        for _ in range(20):
            bal = client.get("/api/v1/credits/balance", headers=h).json()
            if bal["available_credits"] == 2:
                granted = True
                break
            time.sleep(1.0)
        assert granted, f"Starter +2 credits never granted: {bal}"
        print("[PASS] Starter +2 credits granted on user.verified.")

        # 2. Paymob Checkout + Signed HMAC Webhook -> +5 Starter Pack Credits (Total = 7)
        chk = client.post(
            "/api/v1/credits/checkout",
            headers=h,
            json={"pack_id": "starter", "currency": "EGP", "payment_method": "meeza"},
        )
        assert chk.status_code == 201, chk.text
        order = chk.json()
        wh_payload = json.dumps({"provider_order_id": order["provider_order_id"], "success": True}).encode("utf-8")
        sig = hmac.new(b"dev_paymob_hmac_secret", wh_payload, hashlib.sha512).hexdigest()
        wh = client.post(
            "/api/v1/webhooks/paymob",
            content=wh_payload,
            headers={"Content-Type": "application/json", "X-Paymob-Hmac": sig},
        )
        assert wh.status_code == 200 and wh.json()["available_credits"] == 7, wh.text

        inv = client.get(f"/api/v1/credits/invoices/{order['id']}/pdf", headers=h)
        assert inv.status_code == 200 and inv.content[:4] == b"%PDF"
        print("[PASS] Paymob HMAC webhook & PDF invoice verified (balance=7 cr).")

        # 3. CV Tailor Saga: Hold 1 cr -> latex-worker compiles PDF -> MinIO -> Commit (balance=6 cr)
        jobs = client.get("/api/v1/explore/jobs").json()
        target_job = jobs[0]
        tailor = client.post(
            "/api/v1/cv-fit",
            headers=h,
            json={
                "persona_id": "ds_track",
                "job_id": target_job["id"],
                "job_title": target_job["title"],
                "company_name": target_job["company_name"],
            },
        )
        assert tailor.status_code == 202, tailor.text
        doc_id = tailor.json()["doc_id"]

        compiled = False
        for _ in range(30):
            d = client.get(f"/api/v1/cv-fit/{doc_id}", headers=h).json()
            if d["status"] == "completed" and d["compile_status"] == "ok":
                compiled = True
                break
            time.sleep(1.0)
        assert compiled, f"CV compilation did not complete cleanly: {d}"

        pdf_resp = client.get(f"/api/v1/cv-fit/{doc_id}/download/pdf", headers=h)
        assert pdf_resp.status_code == 200 and pdf_resp.content[:4] == b"%PDF"

        settled = False
        for _ in range(15):
            bal_after = client.get("/api/v1/credits/balance", headers=h).json()
            if bal_after["available_credits"] == 6 and bal_after["held_credits"] == 0:
                settled = True
                break
            time.sleep(1.0)
        assert settled, f"Hold was not committed cleanly: {bal_after}"
        print("[PASS] Credit Hold -> latex-worker PDF -> MinIO -> Commit verified (balance=6 cr).")

        # 4. Already-Unlocked 0-credit protection
        reopen = client.post(
            "/api/v1/cv-fit",
            headers=h,
            json={"persona_id": "ds_track", "job_id": target_job["id"]},
        )
        assert reopen.status_code == 202 and reopen.json().get("already_unlocked") is True
        assert client.get("/api/v1/credits/balance", headers=h).json()["available_credits"] == 6
        print("[PASS] Already-unlocked 0-credit protection verified.")

        # 5. Chaos Test: Compile failure triggers automatic +1 cr refund in ledger!
        chaos = client.post(
            "/api/v1/cv-fit",
            headers=h,
            json={
                "persona_id": "chaos_track",
                "job_id": jobs[1]["id"],
                "user_comments": "Trigger \\FAIL_COMPILE_TEST",
            },
        )
        assert chaos.status_code == 202, chaos.text
        chaos_doc_id = chaos.json()["doc_id"]

        refunded = False
        for _ in range(25):
            bal_c = client.get("/api/v1/credits/balance", headers=h).json()
            ledger = client.get("/api/v1/credits/ledger", headers=h).json()
            if bal_c["available_credits"] == 6 and bal_c["held_credits"] == 0 and any(
                x["action"] == "compile_refund" and x["doc_id"] == chaos_doc_id for x in ledger
            ):
                refunded = True
                break
            time.sleep(1.0)
        assert refunded, f"Auto-refund failed! balance={bal_c}, ledger={ledger}"
        print("[PASS] Chaos compile failure triggered automatic +1 cr refund & ledger entry.")

        # 6. Cover Letter 1 cr draft & download
        cl = client.post(
            "/api/v1/cover-letter",
            headers=h,
            json={"job_id": target_job["id"], "job_title": target_job["title"], "company_name": target_job["company_name"]},
        )
        assert cl.status_code == 201
        assert client.get("/api/v1/credits/balance", headers=h).json()["available_credits"] == 5
        print("[PASS] Cover letter generation & credit settlement verified (balance=5 cr).")

    print("\nALL PHASE 3 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
