from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class NotificationDB(SQLModel, table=True):
    __tablename__ = "notifications"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    category: str = Field(max_length=24)  # match | followup | document | credit | ai_insight
    title: str
    subtitle: str = Field(default="")
    job_id: Optional[str] = Field(default=None, max_length=64)
    pipeline_id: Optional[str] = Field(default=None, max_length=64)
    action_label: str = Field(default="Open", max_length=64)
    target_path: str = Field(default="/dashboard")
    dedup_key: Optional[str] = Field(default=None, index=True, max_length=128)
    read_at: Optional[datetime] = Field(default=None)
    archived_at: Optional[datetime] = Field(default=None)
    snoozed_until: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class NotificationRuleDB(SQLModel, table=True):
    __tablename__ = "notification_rules"

    user_id: str = Field(primary_key=True, max_length=64)
    min_match_alert_score: int = Field(default=85)
    digest_cadence: str = Field(default="daily_9am", max_length=24)
    followup_reminders: bool = Field(default=True)
    low_credit_alerts: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=utc_now)


class EmailDispatchLogDB(SQLModel, table=True):
    __tablename__ = "email_dispatch_logs"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    template_key: str = Field(max_length=64)
    provider_msg_id: str = Field(default="", max_length=128)
    status: str = Field(default="queued", max_length=24)
    sent_at: datetime = Field(default_factory=utc_now)
