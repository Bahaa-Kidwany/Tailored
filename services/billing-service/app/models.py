from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class CreditWalletDB(SQLModel, table=True):
    __tablename__ = "credit_wallets"
    __table_args__ = (
        CheckConstraint("available_credits >= 0", name="ck_wallet_avail_nonneg"),
        CheckConstraint("held_credits >= 0", name="ck_wallet_held_nonneg"),
    )

    user_id: str = Field(primary_key=True, max_length=64)
    available_credits: int = Field(default=0)
    held_credits: int = Field(default=0)
    low_balance_threshold: int = Field(default=2)
    version: int = Field(default=1)
    updated_at: datetime = Field(default_factory=utc_now)


class CreditLedgerEntryDB(SQLModel, table=True):
    __tablename__ = "credit_ledger_entries"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    entry_type: str = Field(max_length=32)  # starter_grant | pack_purchase | hold_created | hold_committed | compile_refund
    delta: int
    balance_after: int
    hold_id: Optional[str] = Field(default=None, max_length=64)
    reference_doc_id: Optional[str] = Field(default=None, max_length=64)
    job_target_label: str = Field(default="")
    payment_order_id: Optional[str] = Field(default=None, max_length=64)
    idempotency_key: str = Field(unique=True, max_length=128)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class CreditHoldDB(SQLModel, table=True):
    __tablename__ = "credit_holds"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    amount: int
    reason: str = Field(max_length=64)
    doc_id: str = Field(max_length=64)
    status: str = Field(default="held", index=True, max_length=24)  # held | committed | refunded | expired
    idempotency_key: str = Field(unique=True, max_length=128)
    expires_at: datetime
    resolved_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class CreditPackCatalogDB(SQLModel, table=True):
    __tablename__ = "credit_packs_catalog"

    pack_id: str = Field(primary_key=True, max_length=32)
    name: str = Field(max_length=64)
    subtitle: str = Field(default="", max_length=128)
    credits: int
    apps_equiv: str = Field(default="", max_length=64)
    prices_json: str = Field(
        default="{}",
        sa_column=Column(Text().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    popular: bool = Field(default=False)
    active: bool = Field(default=True)


class PaymentOrderDB(SQLModel, table=True):
    __tablename__ = "payment_orders"
    __table_args__ = (UniqueConstraint("provider", "provider_order_id", name="uq_provider_order"),)

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=64)
    user_id: str = Field(index=True, max_length=64)
    pack_id: str = Field(max_length=32)
    provider: str = Field(max_length=24)  # paymob | stripe
    payment_method: str = Field(max_length=32)  # card | meeza | wallet | fawry | apple_pay
    currency: str = Field(max_length=8)
    amount_minor: int
    credits_to_grant: int
    status: str = Field(default="pending", max_length=24)  # pending | paid | failed | expired
    provider_order_id: str = Field(max_length=128)
    fawry_ref_code: Optional[str] = Field(default=None, max_length=64)
    invoice_object_key: Optional[str] = Field(default=None)
    idempotency_key: str = Field(unique=True, max_length=128)
    created_at: datetime = Field(default_factory=utc_now)
    paid_at: Optional[datetime] = Field(default=None)
