"""Comprehensive Full-System Verification & Benchmark Gate for Tailored.

Covers:
1. Container & Service Health Matrix (Traefik + 9 domain microservices + workers + observability)
2. Database Schema & Storage Audit across all 10 Postgres DBs (+ pgvector), ClickHouse, Redpanda topics, and MinIO buckets
3. Authentication & Security Matrix (401 ForwardAuth, JWKS, OTP, 2FA TOTP, OAuth sole-login unlink guard, Refresh + Redis revocation)
4. Cross-Service End-to-End User Workflow (Profile -> Jobs -> Billing -> Documents + LaTeX -> AI Coach + Telemetry + Ambient Memory -> Pipeline + Notifications -> Trace Audit -> GDPR Export & Crypto-Shredding Erasure)
5. 50-Concurrent-Request Performance Benchmark through Traefik Gateway (0% 5xx, P95 < 1500ms)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import hmac
import io
import json
import math
import secrets
import subprocess
import sys
import time
import zipfile
import httpx
import pyotp

BASE = "http://127.0.0.1"

EXPECTED_PG_TABLES = {
    "auth_db": [
        "users",
        "oauth_identities",
        "user_sessions",
        "otp_verifications",
        "totp_mfa",
        "workspace_preferences",
        "privacy_consents",
        "feature_flags",
        "feature_flag_overrides",
        "outbox_events",
        "processed_events",
    ],
    "privacy_vault_db": ["identity_pseudonyms"],
    "profile_db": [
        "master_profiles",
        "contact_numbers",
        "target_locations",
        "career_personas",
        "education_records",
        "spoken_languages",
        "base_cv_templates",
        "outbox_events",
        "processed_events",
    ],
    "jobs_db": [
        "jobs",
        "job_fit_scores",
        "user_job_interactions",
        "scrape_runs",
        "outbox_events",
        "processed_events",
    ],
    "documents_db": [
        "generated_documents",
        "document_versions",
        "frozen_application_snapshots",
        "gdpr_export_jobs",
        "outbox_events",
        "processed_events",
    ],
    "pipeline_db": [
        "pipeline_items",
        "interview_round_notes",
        "outreach_dispatches",
        "outbox_events",
        "processed_events",
    ],
    "billing_db": [
        "credit_wallets",
        "credit_ledger_entries",
        "credit_holds",
        "credit_packs_catalog",
        "payment_orders",
        "outbox_events",
        "processed_events",
    ],
    "ai_agent_db": [
        "user_behavior_profiles",
        "behavioral_memory_facts",
        "agent_threads",
        "agent_checkpoints",
        "agent_messages",
        "proposal_cards",
        "proactive_suggestions",
        "outbox_events",
        "processed_events",
    ],
    "notifications_db": [
        "notifications",
        "notification_rules",
        "email_dispatch_logs",
        "outbox_events",
        "processed_events",
    ],
}

EXPECTED_TOPICS = [
    "identity.lifecycle.v1",
    "profile.events.v1",
    "jobs.commands.v1",
    "jobs.events.v1",
    "documents.commands.v1",
    "documents.events.v1",
    "pipeline.events.v1",
    "billing.events.v1",
    "telemetry.interactions.v1",
    "ai.events.v1",
    "audit.trail.v1",
]

EXPECTED_BUCKETS = ["cv-artifacts", "user-uploads", "invoices", "gdpr-exports"]


def parse_sse_events(raw_text: str) -> list[dict]:
    events = []
    cur_ev = None
    for line in raw_text.splitlines():
        if line.startswith("event:"):
            cur_ev = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and cur_ev:
            events.append({"event": cur_ev, "data": json.loads(line.split(":", 1)[1].strip())})
            cur_ev = None
    return events


def check_infrastructure_and_databases() -> None:
    print("\n--- 1. Container & Service Health Matrix ---")
    ps_out = subprocess.check_output(
        ["docker", "ps", "--filter", "name=tailored-", "--format", "{{.Names}}|{{.Status}}"],
        text=True,
    )
    containers = {}
    for line in ps_out.splitlines():
        if "|" in line:
            name, st = line.split("|", 1)
            containers[name.strip()] = st.strip()

    required_containers = [
        "tailored-traefik",
        "tailored-postgres",
        "tailored-redis",
        "tailored-redpanda",
        "tailored-clickhouse",
        "tailored-minio",
        "tailored-auth",
        "tailored-profile",
        "tailored-jobs",
        "tailored-documents",
        "tailored-pipeline",
        "tailored-billing",
        "tailored-ai-agent",
        "tailored-notifications",
        "tailored-telemetry-audit",
        "tailored-scraper-worker",
        "tailored-latex-worker",
    ]
    missing = [c for c in required_containers if c not in containers]
    assert not missing, f"Missing Tailored containers: {missing}"
    unhealthy = [c for c in required_containers if "unhealthy" in containers[c].lower() or "exited" in containers[c].lower()]
    assert not unhealthy, f"Unhealthy Tailored containers: {unhealthy}"
    print(f"[PASS] All {len(required_containers)} Tailored containers running & healthy.")

    with httpx.Client(timeout=10.0) as client:
        for port in range(8001, 8010):
            r = client.get(f"http://127.0.0.1:{port}/health")
            assert r.status_code == 200, f"Port {port} /health failed: {r.status_code}"
            m = client.get(f"http://127.0.0.1:{port}/metrics")
            assert m.status_code == 200 and "tailored_http_requests_total" in m.text, (
                f"Port {port} /metrics invalid ({m.status_code})"
            )
    print("[PASS] All 9 Tailored HTTP microservices returned 200 on /health & Prometheus /metrics (8001..8009).")

    pdflatex_bin = subprocess.check_output(
        ["docker", "exec", "tailored-latex-worker", "which", "pdflatex"],
        text=True,
    ).strip()
    assert pdflatex_bin == "/usr/bin/pdflatex", f"Unexpected pdflatex path: {pdflatex_bin}"
    egress_probe = subprocess.run(
        [
            "docker", "exec", "tailored-latex-worker",
            "python", "-c", "import urllib.request; urllib.request.urlopen('https://1.1.1.1', timeout=2)",
        ],
        capture_output=True,
        text=True,
    )
    assert egress_probe.returncode != 0, "tailored-latex-worker must have outbound internet blocked!"
    print("[PASS] Offline /usr/bin/pdflatex verified inside egress-blocked sandbox_net.")

    print("\n--- 2. PostgreSQL (10 DBs + pgvector), ClickHouse, Redpanda & MinIO Audit ---")
    total_pg_tables = 0
    for db, expected in EXPECTED_PG_TABLES.items():
        out = subprocess.check_output(
            [
                "docker", "exec", "tailored-postgres",
                "psql", "-U", "tailored_admin", "-d", db, "-Atc",
                "SELECT tablename FROM pg_tables WHERE schemaname='public';",
            ],
            text=True,
        )
        found = {x.strip() for x in out.splitlines() if x.strip()}
        missing_tbls = [t for t in expected if t not in found]
        assert not missing_tbls, f"{db} missing tables: {missing_tbls}"
        alembic_ver = subprocess.check_output(
            [
                "docker", "exec", "tailored-postgres",
                "psql", "-U", "tailored_admin", "-d", db, "-Atc",
                "SELECT version_num FROM alembic_version LIMIT 1;",
            ],
            text=True,
        ).strip()
        assert alembic_ver == "0001_initial_schema", f"{db} unexpected alembic_version: {alembic_ver!r}"
        total_pg_tables += len(expected)

    db_list = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", "postgres", "-Atc",
            "SELECT datname FROM pg_database WHERE datistemplate = false;",
        ],
        text=True,
    )
    all_dbs = {x.strip() for x in db_list.splitlines() if x.strip()}
    for db in list(EXPECTED_PG_TABLES.keys()) + ["langfuse_db"]:
        assert db in all_dbs, f"Missing Postgres database: {db}"

    vec_ext = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", "ai_agent_db", "-Atc",
            "SELECT extname FROM pg_extension WHERE extname='vector';",
        ],
        text=True,
    ).strip()
    assert vec_ext == "vector", "pgvector extension missing on ai_agent_db"
    ai_indexes = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", "ai_agent_db", "-Atc",
            "SELECT indexname FROM pg_indexes WHERE tablename='behavioral_memory_facts';",
        ],
        text=True,
    )
    assert "ix_behavioral_memory_embedding_hnsw" in ai_indexes, "Missing pgvector HNSW index on ai_agent_db"
    print(f"[PASS] All 10 PostgreSQL DBs verified ({total_pg_tables} domain tables + 9x Alembic 0001 + langfuse_db + pgvector HNSW).")

    ch_tables = subprocess.check_output(
        [
            "docker", "exec", "tailored-clickhouse",
            "clickhouse-client", "--user", "tailored_ch", "--password", "tailored_ch_dev_pass",
            "-q", "SELECT database || '.' || name FROM system.tables WHERE database IN ('tailored_audit','tailored_analytics') FORMAT TabSeparated;",
        ],
        text=True,
    )
    ch_set = {x.strip() for x in ch_tables.splitlines() if x.strip()}
    assert "tailored_audit.feature_audit_logs" in ch_set
    assert "tailored_analytics.user_behavior_events" in ch_set
    print("[PASS] ClickHouse analytical & audit schemas verified.")

    rpk_out = subprocess.check_output(
        ["docker", "exec", "tailored-redpanda", "rpk", "topic", "list", "--brokers", "redpanda:9092"],
        text=True,
    )
    for topic in EXPECTED_TOPICS:
        assert topic in rpk_out, f"Missing Redpanda topic: {topic}"
    print(f"[PASS] All {len(EXPECTED_TOPICS)} Redpanda domain topics verified.")

    minio_out = subprocess.check_output(
        [
            "docker", "run", "--rm", "--network", "tailored_data_net",
            "--entrypoint", "/bin/sh", "minio/minio:latest", "-c",
            "mc alias set t http://minio:9000 tailored_minio tailored_minio_dev_pass >/dev/null && mc ls t/",
        ],
        text=True,
    )
    for bkt in EXPECTED_BUCKETS:
        assert bkt in minio_out, f"Missing MinIO bucket: {bkt}"
    print(f"[PASS] All {len(EXPECTED_BUCKETS)} MinIO buckets verified.")


def _get_bootstrap_admin_headers(client: httpx.Client) -> dict[str, str]:
    admin_email = "admin@tailored.test"
    admin_pwd = "AdminVerifyPass123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": admin_pwd, "full_name": "Tailored Admin"},
    )
    if reg.status_code == 201:
        return {"Authorization": f"Bearer {reg.json()['access_token']}"}
    login = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_pwd})
    if login.status_code == 200:
        return {"Authorization": f"Bearer {login.json()['access_token']}"}
    forgot = client.post("/api/v1/auth/forgot-password", json={"email": admin_email})
    assert forgot.status_code == 200 and forgot.json().get("dev_otp"), f"Cannot recover bootstrap admin: {forgot.text}"
    otp = forgot.json()["dev_otp"]
    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"email": admin_email, "code": otp, "new_password": admin_pwd},
    )
    assert reset.status_code == 200
    login2 = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_pwd})
    assert login2.status_code == 200, login2.text
    return {"Authorization": f"Bearer {login2.json()['access_token']}"}


def check_auth_and_security_matrix() -> dict[str, str]:
    print("\n--- 3. Auth, Login, 2FA TOTP, OAuth Unlink Guard, Admin RBAC & Security Headers ---")
    with httpx.Client(base_url=BASE, timeout=15.0) as client:
        gw_probe = client.get("/api/v1/explore/jobs")
        assert gw_probe.headers.get("x-content-type-options") == "nosniff", (
            f"Missing Traefik security header X-Content-Type-Options: {gw_probe.headers}"
        )

        for path in [
            "/api/v1/profiles/me",
            "/api/v1/jobs",
            "/api/v1/credits/balance",
            "/api/v1/cv-fit",
            "/api/v1/agent/threads",
            "/api/v1/pipeline",
            "/api/v1/notifications",
        ]:
            r = client.get(path)
            assert r.status_code == 401, f"Protected path {path} returned {r.status_code} instead of 401"

        jwks = client.get("/.well-known/jwks.json")
        assert jwks.status_code == 200 and len(jwks.json().get("keys", [])) >= 1
        print("[PASS] Traefik ForwardAuth blocks 7/7 protected prefixes with 401 & JWKS active.")

        # OAuth sole-login protection check
        oauth_email = f"full_oauth_{secrets.token_hex(4)}@tailored.test"
        o_reg = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={"provider_user_id": f"gid_{secrets.token_hex(4)}", "email": oauth_email, "full_name": "OAuth Full"},
        )
        assert o_reg.status_code == 200
        o_tok = o_reg.json()["access_token"]
        assert client.delete("/api/v1/account/oauth/google", headers={"Authorization": f"Bearer {o_tok}"}).status_code == 400
        assert (
            client.post(
                "/api/v1/account/change-password",
                headers={"Authorization": f"Bearer {o_tok}"},
                json={"new_password": "BackupPassword123!"},
            ).status_code
            == 200
        )
        assert client.delete("/api/v1/account/oauth/google", headers={"Authorization": f"Bearer {o_tok}"}).status_code == 200
        print("[PASS] OAuth sole-login unlink protection & recovery password verified.")

        # Password + 2FA TOTP + Refresh Rotation + Logout Immediate Redis Revocation
        sec_email = f"full_sec_{secrets.token_hex(4)}@tailored.test"
        pwd = "StrongPassword123!"
        reg = client.post("/api/v1/auth/register", json={"email": sec_email, "password": pwd, "full_name": "Sec User"})
        assert reg.status_code == 201
        tok1 = reg.json()["access_token"]
        rt1 = reg.json()["refresh_token"]
        assert client.post("/api/v1/auth/login", json={"email": sec_email, "password": "BadPassword!"}).status_code == 401

        setup = client.post("/api/v1/account/2fa/setup", headers={"Authorization": f"Bearer {tok1}"})
        secret = setup.json()["secret"]
        totp = pyotp.TOTP(secret).now()
        assert client.post("/api/v1/account/2fa/enable", headers={"Authorization": f"Bearer {tok1}"}, json={"code": totp}).status_code == 200
        assert client.post("/api/v1/auth/login", json={"email": sec_email, "password": pwd}).status_code == 401
        login_ok = client.post("/api/v1/auth/login", json={"email": sec_email, "password": pwd, "totp_code": pyotp.TOTP(secret).now()})
        assert login_ok.status_code == 200
        tok2 = login_ok.json()["access_token"]

        ref = client.post("/api/v1/auth/refresh", json={"refresh_token": rt1})
        assert ref.status_code == 200
        tok3 = ref.json()["access_token"]
        assert client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {tok3}"}).status_code == 200
        assert client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {tok3}"}).status_code == 401
        assert client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {tok2}"}).status_code == 200
        print("[PASS] Password auth, 2FA TOTP, Refresh rotation & immediate Redis session revocation verified.")

        # Admin RBAC + Traefik Security Headers verification (401 unauth / 403 user / 200 admin)
        admin_headers = _get_bootstrap_admin_headers(client)
        user_headers = {"Authorization": f"Bearer {tok2}"}
        flag_payload = {"enabled": True, "rollout_percent": 100, "description": "RBAC verification flag"}
        assert client.put("/api/v1/admin/flags/verify_rbac_flag", json=flag_payload).status_code == 401
        assert client.put("/api/v1/admin/flags/verify_rbac_flag", headers=user_headers, json=flag_payload).status_code == 403
        assert client.put("/api/v1/admin/flags/verify_rbac_flag", headers=admin_headers, json=flag_payload).status_code == 200

        dummy_trace = "0" * 32
        assert client.get(f"/api/v1/admin/audit/traces/{dummy_trace}").status_code == 401
        assert client.get(f"/api/v1/admin/audit/traces/{dummy_trace}", headers=user_headers).status_code == 403
        assert client.get(f"/api/v1/admin/audit/traces/{dummy_trace}", headers=admin_headers).status_code == 200
        print("[PASS] Admin RBAC (401/403/200) on /admin/flags & /admin/audit + security headers verified.")
        return admin_headers


def check_full_e2e_workflow_and_benchmark(admin_headers: dict[str, str]) -> None:
    print("\n--- 4. Full End-to-End Cross-Service Workflow + Telemetry/Trace + GDPR ---")
    email = f"full_e2e_{secrets.token_hex(4)}@tailored.test"
    pwd = "E2EPassword123!"
    trace_id_hex = secrets.token_hex(16)
    span_id_hex = secrets.token_hex(8)
    traceparent = f"00-{trace_id_hex}-{span_id_hex}-01"

    with httpx.Client(base_url=BASE, timeout=25.0) as client:
        # 1. Register + Verify Email
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Mostafa E2E"})
        assert reg.status_code == 201
        tok = reg.json()["access_token"]
        user_id = reg.json()["user"]["id"]
        otp = reg.json()["dev_otp"]
        h = {"Authorization": f"Bearer {tok}"}

        assert client.post("/api/v1/auth/verify-email", json={"email": email, "code": otp}).status_code == 200

        # 2. Master Profile + Persona
        prof = client.put(
            "/api/v1/profiles/me",
            headers={**h, "traceparent": traceparent},
            json={
                "personal_info": {"full_name": "Mostafa E2E", "primary_email": email},
                "residence_and_mobility": {
                    "current_residence": {"city": "Cairo", "country": "Egypt"},
                    "willing_to_relocate": True,
                    "target_locations": [{"location_id": "loc_1", "city": "Riyadh", "country": "Saudi Arabia", "work_modes": ["Hybrid", "Remote"]}],
                },
                "career_personas": [
                    {
                        "persona_id": "ds_track",
                        "target_title": "Lead Data Scientist",
                        "is_primary": True,
                        "years_of_experience": 4,
                        "skills_and_tools": {"core_skills": ["Python", "PyTorch", "FastAPI", "Docker", "SQL", "PostgreSQL"]},
                        "experience_highlights": [
                            {"company": "Swvl", "role": "Data Scientist", "achievements": ["Built route pricing APIs in Python"]}
                        ],
                    }
                ],
            },
        )
        assert prof.status_code == 200

        # 3. Explore + Ranked Jobs + Interest
        explore = client.get("/api/v1/explore/jobs")
        assert explore.status_code == 200 and len(explore.json()) >= 6
        ranked = client.get("/api/v1/jobs", headers=h)
        assert ranked.status_code == 200 and len(ranked.json()) >= 6
        target_job = ranked.json()[0]
        assert client.post(f"/api/v1/interest/{target_job['id']}", headers=h).status_code == 200

        # 4. Billing: wait starter +2 credits + packs + checkout webhook
        packs = client.get("/api/v1/credits/packs?currency=EGP")
        assert packs.status_code == 200 and len(packs.json()) >= 3
        starter_ok = False
        for _ in range(20):
            if client.get("/api/v1/credits/balance", headers=h).json()["available_credits"] == 2:
                starter_ok = True
                break
            time.sleep(0.8)
        assert starter_ok

        # 5. CV Fit Hold -> latex-worker -> MinIO PDF -> Commit
        tailor = client.post(
            "/api/v1/cv-fit",
            headers={**h, "traceparent": traceparent},
            json={"persona_id": "ds_track", "job_id": target_job["id"], "job_title": target_job["title"], "company_name": target_job["company_name"]},
        )
        assert tailor.status_code == 202
        doc_id = tailor.json()["doc_id"]
        compiled = False
        for _ in range(30):
            d = client.get(f"/api/v1/cv-fit/{doc_id}", headers=h).json()
            if d["status"] == "completed" and d["compile_status"] == "ok":
                compiled = True
                break
            time.sleep(0.8)
        assert compiled
        pdf = client.get(f"/api/v1/cv-fit/{doc_id}/download/pdf", headers=h)
        assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"

        # 6. Telemetry -> Ambient Memory + Proactive Suggestion -> Coach SSE Thread
        batch = [
            {
                "feature_key": "radar.job.dwell",
                "event_name": "ui.job.dwelled",
                "route": "/radar",
                "persona_track": "MLOps Platform Engineer",
                "duration_ms": 38000,
                "properties": {"job_country": "Saudi Arabia", "normalized_role": "MLOps Platform Engineer", "idx": i},
            }
            for i in range(6)
        ]
        assert client.post("/api/v1/telemetry/events", headers=h, json={"events": batch}).status_code == 202
        mem_ok = False
        for _ in range(20):
            mem = client.get("/api/v1/agent/memory", headers=h).json()
            if mem.get("memory_facts") and mem.get("proactive_suggestions"):
                mem_ok = True
                break
            time.sleep(0.8)
        assert mem_ok

        th = client.post("/api/v1/agent/threads", headers=h, json={"surface": "cv", "job_id": target_job["id"], "doc_id": doc_id})
        assert th.status_code == 201
        stream_r = client.post(
            f"/api/v1/agent/threads/{th.json()['id']}/messages:stream",
            headers=h,
            json={"prompt": "Add metrics to Swvl routing", "mode": "Surgical", "job_id": target_job["id"], "doc_id": doc_id},
        )
        assert stream_r.status_code == 200
        assert any(e["event"] == "proposal_card" for e in parse_sse_events(stream_r.text))

        # 7. Pipeline CRM -> Outreach -> Dispatch Frozen Snapshot -> Round Note -> Notification
        pipe = client.post("/api/v1/pipeline", headers=h, json={"job_id": target_job["id"], "tailored_cv_doc_id": doc_id})
        assert pipe.status_code == 201
        item_id = pipe.json()["id"]
        disp = client.post(f"/api/v1/pipeline/{item_id}/dispatch", headers=h, json={"dispatch_channel": "gmail_web", "cv_doc_id": doc_id})
        assert disp.status_code == 200 and disp.json()["frozen_snapshot_id"]
        assert client.post(f"/api/v1/pipeline/{item_id}/rounds", headers=h, json={"round_title": "System Design", "interviewer": "Lead Arch", "notes": "Discuss scalability"}).status_code == 201

        notif_ok = False
        for _ in range(15):
            ns = client.get("/api/v1/notifications", headers=h).json()
            if len(ns) >= 1:
                notif_ok = True
                break
            time.sleep(0.6)
        assert notif_ok

        # 8. Audit Trace Correlation across ClickHouse (Admin RBAC protected)
        audit_ok = False
        for _ in range(15):
            ar = client.get(f"/api/v1/admin/audit/traces/{trace_id_hex}", headers=admin_headers)
            if ar.status_code == 200 and ar.json()["count"] >= 2:
                audit_ok = True
                break
            time.sleep(0.8)
        assert audit_ok, "Distributed W3C traceparent did not appear across services in ClickHouse"
        print("[PASS] Full E2E cross-service journey & distributed ClickHouse audit correlation verified.")

        print("\n--- 5. Performance Benchmark: 50 Concurrent Connections via Traefik ---")
        targets = [
            ("GET", "/api/v1/explore/jobs", False),
            ("GET", "/api/v1/jobs", True),
            ("GET", "/api/v1/profiles/me", True),
            ("GET", "/api/v1/credits/balance", True),
            ("GET", "/api/v1/pipeline", True),
        ]
        total_requests = 150
        per_route_latencies: dict[str, list[float]] = {u: [] for _, u, _ in targets}
        latencies_ms: list[float] = []
        server_errors = 0
        auth_headers = {"Authorization": f"Bearer {tok}"}

        with httpx.Client(
            base_url=BASE,
            limits=httpx.Limits(max_connections=60, max_keepalive_connections=60),
            timeout=15.0,
        ) as bench_client:
            bench_client.get("/api/v1/explore/jobs")

            def run_one(idx: int) -> tuple[str, int, float]:
                _method, url, needs_auth = targets[idx % len(targets)]
                t0 = time.perf_counter()
                resp = bench_client.get(url, headers=auth_headers if needs_auth else None)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return url, resp.status_code, elapsed_ms

            t_bench_start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=50) as pool:
                futs = [pool.submit(run_one, i) for i in range(total_requests)]
                for fut in as_completed(futs):
                    url, code, ms = fut.result()
                    latencies_ms.append(ms)
                    per_route_latencies[url].append(ms)
                    if code >= 400:
                        server_errors += 1
            bench_wall_s = time.perf_counter() - t_bench_start

        latencies_ms.sort()
        p50 = latencies_ms[int(0.50 * len(latencies_ms))]
        p95 = latencies_ms[min(len(latencies_ms) - 1, math.ceil(0.95 * len(latencies_ms)) - 1)]
        p99 = latencies_ms[min(len(latencies_ms) - 1, math.ceil(0.99 * len(latencies_ms)) - 1)]
        max_ms = latencies_ms[-1]
        rps = total_requests / bench_wall_s

        print(
            f"[BENCHMARK] concurrency=50 total={total_requests} errors={server_errors} "
            f"RPS={rps:.1f}/s P50={p50:.1f}ms P95={p95:.1f}ms P99={p99:.1f}ms MAX={max_ms:.1f}ms"
        )
        for _m, url, _a in targets:
            ul = sorted(per_route_latencies[url])
            rp50 = ul[len(ul) // 2]
            rp95 = ul[min(len(ul) - 1, math.ceil(0.95 * len(ul)) - 1)]
            print(f"  {url}: P50={rp50:.1f}ms P95={rp95:.1f}ms MAX={ul[-1]:.1f}ms")
        assert server_errors == 0, f"Benchmark had {server_errors} error responses!"
        assert p95 < 1500.0, f"Benchmark P95 too high: {p95:.1f}ms"
        print("[PASS] 50-concurrent-request benchmark passed (0% errors, P95 < 1500ms).")

        # 9. Final GDPR .zip Export + Crypto-Shredding Cleanup
        exp = client.post("/api/v1/account/export", headers=h)
        assert exp.status_code == 200
        dl = client.get(exp.json()["download_url"], headers=h)
        with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
            assert "master_profile.json" in zf.namelist()

        er = client.request("DELETE", "/api/v1/account", headers=h, json={"confirm": "DELETE", "password": pwd})
        assert er.status_code == 202 and er.json()["crypto_shredded"] is True
        assert client.get("/api/v1/profiles/me", headers=h).status_code == 401
        shred_cnt = subprocess.check_output(
            [
                "docker", "exec", "tailored-postgres",
                "psql", "-U", "tailored_admin", "-d", "privacy_vault_db", "-Atc",
                f"SELECT COUNT(*) FROM identity_pseudonyms WHERE user_id='{user_id}';",
            ],
            text=True,
        ).strip()
        assert shred_cnt == "0"
        print("[PASS] GDPR .zip archive + crypto-shredding erasure cleanup verified.")


def main() -> int:
    check_infrastructure_and_databases()
    admin_headers = check_auth_and_security_matrix()
    check_full_e2e_workflow_and_benchmark(admin_headers)
    print("\nALL FULL-SYSTEM VERIFICATION & PERFORMANCE GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
