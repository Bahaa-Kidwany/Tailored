"""Run Alembic migrations across all 9 isolated Tailored PostgreSQL domain databases."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

DOMAIN_DBS = [
    "auth_db",
    "privacy_vault_db",
    "profile_db",
    "jobs_db",
    "documents_db",
    "pipeline_db",
    "billing_db",
    "ai_agent_db",
    "notifications_db",
]


def _host_reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def run_all() -> int:
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    if host in ("127.0.0.1", "localhost") and not _host_reachable(host, port):
        repo_root = str(Path(__file__).resolve().parents[2])
        subprocess.check_call(
            ["docker", "build", "-q", "-t", "tailored-migrations:latest", "-f", "infra/migrations/Dockerfile", "."],
            cwd=repo_root,
        )
        return subprocess.call(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                os.getenv("TAILORED_DATA_NET", "tailored_data_net"),
                "-e",
                "POSTGRES_HOST=postgres",
                "tailored-migrations:latest",
            ]
        )

    try:
        from alembic import command
        from alembic.config import Config
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "alembic>=1.13.0"])
        from alembic import command
        from alembic.config import Config

    user = os.getenv("POSTGRES_SUPERUSER", "tailored_admin")
    password = os.getenv("POSTGRES_SUPERPASS", "tailored_dev_superpass")
    ini_path = str(Path(__file__).resolve().parent / "alembic.ini")

    for db in DOMAIN_DBS:
        db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
        os.environ["ALEMBIC_DB_URL"] = db_url
        os.environ["ALEMBIC_DB_NAME"] = db
        cfg = Config(ini_path)
        cfg.set_main_option("script_location", str(Path(__file__).resolve().parent))
        cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(cfg, "head")
        print(f"[MIGRATE] {db} -> head (0001_initial_schema)")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
