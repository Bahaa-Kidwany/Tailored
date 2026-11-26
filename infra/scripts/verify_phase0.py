"""Phase 0 End-to-End Verification Gate for Tailored Infrastructure & Observability Spine."""

import os
import secrets
import subprocess
import sys
import time
import httpx


EXPECTED_DBS = [
    "auth_db",
    "privacy_vault_db",
    "profile_db",
    "jobs_db",
    "documents_db",
    "pipeline_db",
    "billing_db",
    "ai_agent_db",
    "notifications_db",
    "langfuse_db",
]

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


def run_cmd(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout


def check_postgres() -> None:
    out = run_cmd([
        "docker", "exec", "tailored-postgres",
        "psql", "-U", "tailored_admin", "-d", "postgres", "-Atc",
        "SELECT datname FROM pg_database WHERE datistemplate = false;",
    ])
    dbs = {line.strip() for line in out.splitlines() if line.strip()}
    missing = [db for db in EXPECTED_DBS if db not in dbs]
    assert not missing, f"Missing Postgres DBs: {missing}"

    ext = run_cmd([
        "docker", "exec", "tailored-postgres",
        "psql", "-U", "tailored_admin", "-d", "ai_agent_db", "-Atc",
        "SELECT extname FROM pg_extension WHERE extname='vector';",
    ]).strip()
    assert ext == "vector", f"pgvector extension missing on ai_agent_db (got {ext!r})"
    print("[PASS] PostgreSQL: all 10 logical DBs + pgvector on ai_agent_db verified.")


def check_redpanda() -> None:
    out = run_cmd(["docker", "exec", "tailored-redpanda", "rpk", "topic", "list", "--brokers", "redpanda:9092"])
    missing = [t for t in EXPECTED_TOPICS if t not in out or f"{t}.dlq" not in out]
    assert not missing, f"Missing Redpanda topics/DLQs: {missing}"
    print("[PASS] Redpanda: all 11 topics + 11 DLQs verified.")


def check_clickhouse() -> None:
    out = run_cmd([
        "docker", "exec", "tailored-clickhouse",
        "clickhouse-client", "--user", "tailored_ch", "--password", "tailored_ch_dev_pass",
        "-q", "SELECT database || '.' || name FROM system.tables WHERE database IN ('tailored_analytics', 'tailored_audit');",
    ])
    tables = {line.strip() for line in out.splitlines() if line.strip()}
    for required in [
        "tailored_analytics.user_behavior_events",
        "tailored_analytics.mv_feature_daily_usage",
        "tailored_analytics.mv_ai_proposal_quality",
        "tailored_audit.feature_audit_logs",
    ]:
        assert required in tables, f"Missing ClickHouse table/view: {required}"
    print("[PASS] ClickHouse: analytics, MVs, and audit tables verified.")


def check_minio() -> None:
    out = run_cmd([
        "docker", "exec", "tailored-minio",
        "sh", "-c", "ls /data",
    ])
    for bucket in EXPECTED_BUCKETS:
        assert bucket in out, f"Missing MinIO bucket: {bucket}"
    print("[PASS] MinIO: all 4 S3 buckets verified.")


def check_e2e_trace_and_audit() -> None:
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    traceparent = f"00-{trace_id}-{span_id}-01"

    with httpx.Client(timeout=10.0) as client:
        # 1. Fire request through Traefik Gateway -> telemetry-audit-service
        probe = client.post(
            "http://localhost/internal/phase0/probe",
            headers={
                "traceparent": traceparent,
                "X-Feature-Key": "system.phase0.probe",
                "X-User-Id": "phase0-verifier",
            },
        )
        assert probe.status_code == 200, f"Probe failed: {probe.status_code} {probe.text}"
        body = probe.json()
        assert body["trace_id"] == trace_id, f"Trace ID mismatch: {body}"
        assert probe.headers.get("X-Trace-Id") == trace_id
        print(f"[PASS] Traefik -> telemetry-audit-service probe succeeded (trace_id={trace_id}).")

        # 2. Poll ClickHouse audit query via Traefik
        found_audit = False
        for _ in range(25):
            r = client.get(f"http://localhost/api/v1/admin/audit/traces/{trace_id}")
            if r.status_code == 200 and r.json().get("count", 0) >= 1:
                rec = r.json()["records"][0]
                assert rec["feature_key"] == "system.phase0.probe"
                assert rec["outcome"] == "success"
                found_audit = True
                break
            time.sleep(1.0)
        assert found_audit, f"ClickHouse audit record not found for trace_id={trace_id}"
        print("[PASS] ClickHouse Audit: trace_id & feature_key persisted via Redpanda.")

        # 3. Poll Grafana Tempo for distributed trace spans
        found_tempo = False
        for _ in range(30):
            tr = client.get(f"http://localhost:3200/api/traces/{trace_id}")
            if tr.status_code == 200 and tr.text.strip():
                found_tempo = True
                break
            time.sleep(1.0)
        assert found_tempo, f"Grafana Tempo trace not found for trace_id={trace_id}"
        print("[PASS] Grafana Tempo: distributed OTLP trace verified.")

        # 4. Verify Grafana & Langfuse health endpoints
        grafana_port = os.getenv("GRAFANA_HOST_PORT", "3002")
        gf = client.get(f"http://localhost:{grafana_port}/api/health")
        assert gf.status_code == 200, f"Grafana unhealthy: {gf.status_code}"
        lf = client.get("http://localhost:3001/api/public/health")
        assert lf.status_code == 200, f"Langfuse unhealthy: {lf.status_code}"
        print("[PASS] Grafana & Self-Hosted Langfuse health endpoints verified.")


def main() -> int:
    check_postgres()
    check_redpanda()
    check_clickhouse()
    check_minio()
    check_e2e_trace_and_audit()
    print("\nALL PHASE 0 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
