"""Baseline multi-database schema migration tracking all 9 Tailored service DBs."""

from __future__ import annotations

import os
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    db_name = conn.engine.url.database or os.getenv("ALEMBIC_DB_NAME", "")
    if db_name == "ai_agent_db":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'behavioral_memory_facts') THEN
                    CREATE INDEX IF NOT EXISTS ix_behavioral_memory_embedding_hnsw
                    ON behavioral_memory_facts USING hnsw (embedding vector_cosine_ops);
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    conn = op.get_bind()
    db_name = conn.engine.url.database or os.getenv("ALEMBIC_DB_NAME", "")
    if db_name == "ai_agent_db":
        op.execute("DROP INDEX IF EXISTS ix_behavioral_memory_embedding_hnsw")
