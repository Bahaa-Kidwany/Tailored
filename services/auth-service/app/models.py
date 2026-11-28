from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, LargeBinary, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    email: str = Field(index=True, unique=True, max_length=320)
    full_name: str = Field(default="", max_length=200)
    password_hash: Optional[str] = Field(default=None)
    email_verified: bool = Field(default=False)
    status: str = Field(default="active", max_length=24)  # active | locked | erasing
    role: str = Field(default="user", max_length=24)  # user | admin
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OAuthIdentityDB(SQLModel, table=True):
    __tablename__ = "oauth_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_uid"),)

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=64)
    provider: str = Field(max_length=24)  # google | linkedin
    provider_user_id: str = Field(max_length=255)
    provider_email: str = Field(default="", max_length=320)
    linked_at: datetime = Field(default_factory=utc_now)


class UserSessionDB(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=64)
    refresh_token_hash: str = Field(index=True, max_length=128)
    token_family: str = Field(default_factory=new_uuid, max_length=64)
    device_label: str = Field(default="Web Browser", max_length=200)
    ip_prefix: str = Field(default="127.0.0.1", max_length=64)
    geo_city: str = Field(default="Cairo, Egypt", max_length=96)
    last_active_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: Optional[datetime] = Field(default=None)


class OtpVerificationDB(SQLModel, table=True):
    __tablename__ = "otp_verifications"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=64)
    purpose: str = Field(index=True, max_length=32)  # verify_email | reset_pw | change_email
    target_email: str = Field(max_length=320)
    code_hash: str = Field(max_length=128)
    attempts: int = Field(default=0)
    expires_at: datetime
    consumed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class TotpMfaDB(SQLModel, table=True):
    __tablename__ = "totp_mfa"

    user_id: str = Field(foreign_key="users.id", primary_key=True, max_length=64)
    encrypted_secret: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    enabled: bool = Field(default=False)
    recovery_codes_hashes: str = Field(
        default="[]",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    enabled_at: Optional[datetime] = Field(default=None)


class WorkspacePreferenceDB(SQLModel, table=True):
    __tablename__ = "workspace_preferences"

    user_id: str = Field(foreign_key="users.id", primary_key=True, max_length=64)
    default_home_route: str = Field(default="/dashboard", max_length=48)
    list_density: str = Field(default="cozy", max_length=16)
    default_studio_intensity: str = Field(default="Surgical", max_length=24)
    preferred_currency: str = Field(default="EGP", max_length=8)
    chat_side: str = Field(default="right", max_length=8)
    collapsed_rail: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=utc_now)


class PrivacyConsentDB(SQLModel, table=True):
    __tablename__ = "privacy_consents"

    user_id: str = Field(foreign_key="users.id", primary_key=True, max_length=64)
    analytics_micro_signals: bool = Field(default=True)
    ai_passive_learning: bool = Field(default=True)
    proactive_nudges: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=utc_now)


class FeatureFlagDB(SQLModel, table=True):
    __tablename__ = "feature_flags"

    key: str = Field(primary_key=True, max_length=96)
    enabled: bool = Field(default=True)
    rollout_percent: int = Field(default=100)
    rules_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    description: str = Field(default="")
    updated_at: datetime = Field(default_factory=utc_now)


class FeatureFlagOverrideDB(SQLModel, table=True):
    __tablename__ = "feature_flag_overrides"

    flag_key: str = Field(foreign_key="feature_flags.key", primary_key=True, max_length=96)
    user_id: str = Field(primary_key=True, max_length=64)
    enabled: bool = Field(default=True)


# Isolated Privacy Vault Database Table (bound to privacy_vault_db engine only)
class IdentityPseudonymDB(SQLModel, table=True):
    __tablename__ = "identity_pseudonyms"

    user_id: str = Field(primary_key=True, max_length=64)
    analytics_anon_id: str = Field(unique=True, index=True, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)
