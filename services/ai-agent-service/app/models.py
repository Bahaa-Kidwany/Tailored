from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class UserBehaviorProfileDB(SQLModel, table=True):
    __tablename__ = "user_behavior_profiles"

    user_id: str = Field(primary_key=True, max_length=64)
    dominant_locations_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    implicit_role_drift_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    writing_style_prefs_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    skill_gap_clicks_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    avg_proposal_accept_rate: float = Field(default=1.0)
    total_events_processed: int = Field(default=0)
    events_since_last_distill: int = Field(default=0)
    last_distilled_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=utc_now)


class BehavioralMemoryFactDB(SQLModel, table=True):
    __tablename__ = "behavioral_memory_facts"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    category: str = Field(max_length=32)  # writing_style | role_drift | location_drift | skill_gap | workflow_habit
    fact_text: str
    embedding: Any = Field(default=None, sa_column=Column(Vector(768), nullable=True))
    confidence: float = Field(default=0.8)
    source_event_ids_json: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    status: str = Field(default="active", index=True, max_length=24)  # active | dismissed_by_user
    created_at: datetime = Field(default_factory=utc_now)
    last_reinforced_at: datetime = Field(default_factory=utc_now)


class AgentThreadDB(SQLModel, table=True):
    __tablename__ = "agent_threads"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    surface: str = Field(default="cv", max_length=24)  # cv | cover_letter | workspace
    scope: str = Field(default="role", max_length=16)  # role | workspace
    doc_id: Optional[str] = Field(default=None, max_length=64)
    job_id: Optional[str] = Field(default=None, max_length=64)
    title: str = Field(default="Studio Coach Thread", max_length=200)
    active_checkpoint_id: Optional[str] = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentCheckpointDB(SQLModel, table=True):
    __tablename__ = "agent_checkpoints"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    thread_id: str = Field(foreign_key="agent_threads.id", index=True, max_length=64)
    parent_checkpoint_id: Optional[str] = Field(default=None, max_length=64)
    state_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    created_at: datetime = Field(default_factory=utc_now)


class AgentMessageDB(SQLModel, table=True):
    __tablename__ = "agent_messages"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    thread_id: str = Field(foreign_key="agent_threads.id", index=True, max_length=64)
    checkpoint_id: str = Field(index=True, max_length=64)
    role: str = Field(max_length=16)  # user | assistant
    content_text: str = Field(default="")
    thinking_summary: Optional[str] = Field(default=None)
    focused_anchor_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    resources_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    action_card_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    audit_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    langfuse_trace_id: Optional[str] = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)


class ProposalCardDB(SQLModel, table=True):
    __tablename__ = "proposal_cards"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    thread_id: str = Field(foreign_key="agent_threads.id", index=True, max_length=64)
    message_id: str = Field(foreign_key="agent_messages.id", index=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    doc_id: Optional[str] = Field(default=None, index=True, max_length=64)
    target_anchor_id: str = Field(default="profile", max_length=128)
    target_label: str = Field(default="Profile Summary", max_length=200)
    old_text: str = Field(default="")
    new_text: str = Field(default="")
    is_metric_question: bool = Field(default=False)
    status: str = Field(default="pending", index=True, max_length=24)  # pending | applied | skipped | undone
    refine_count: int = Field(default=0)
    resolved_at: Optional[datetime] = Field(default=None)


class ProactiveSuggestionDB(SQLModel, table=True):
    __tablename__ = "proactive_suggestions"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    rule_key: str = Field(max_length=64)
    title: str
    body: str
    cta_route: str = Field(default="/dashboard", max_length=128)
    payload_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    status: str = Field(default="emitted", index=True, max_length=24)  # emitted | clicked | dismissed | expired
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = Field(default=None)
