from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OutboxEvent(SQLModel, table=True):
    """Transactional outbox table present in every PostgreSQL domain database."""

    __tablename__ = "outbox_events"

    event_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, max_length=64)
    aggregate_type: str = Field(max_length=64)
    aggregate_id: str = Field(max_length=128)
    topic: str = Field(max_length=128)
    event_type: str = Field(max_length=128)
    partition_key: str = Field(max_length=128)
    payload_json: str = Field(default="{}", sa_column=Column("payload", Text().with_variant(JSONB(), "postgresql"), nullable=False))
    headers_json: str = Field(default="{}", sa_column=Column("headers", Text().with_variant(JSONB(), "postgresql"), nullable=False))
    published_at: Optional[datetime] = Field(default=None, index=True)
    retry_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class ProcessedEvent(SQLModel, table=True):
    """Consumer-side event deduplication table."""

    __tablename__ = "processed_events"

    event_id: str = Field(primary_key=True, max_length=64)
    consumer_group: str = Field(max_length=128)
    processed_at: datetime = Field(default_factory=utc_now)
