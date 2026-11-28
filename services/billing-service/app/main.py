from __future__ import annotations

import asyncio
import hashlib
import hmac
import io
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
import httpx
from botocore.client import Config as BotoConfig
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    EventEnvelope,
    InsufficientCreditsError,
    NotFoundError,
    OutboxEvent,
    OutboxRelay,
    ProcessedEvent,
    RedpandaConsumer,
    RedpandaProducer,
    RequestContext,
    ServiceSettings,
    audit_feature,
    create_service_app,
    require_internal_service,
    require_user,
)
from tailored_kit.telemetry_otel.setup import get_current_trace_context

from app.models import (
    CreditHoldDB,
    CreditLedgerEntryDB,
    CreditPackCatalogDB,
    CreditWalletDB,
    PaymentOrderDB,
    utc_now,
)

logger = logging.getLogger(__name__)


class BillingSettings(ServiceSettings):
    service_name: str = "billing-service"
    database_url: str = "postgresql+psycopg://billing_svc:tailored_billing_pass@postgres:5432/billing_db"
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "tailored_minio"
    minio_root_password: str = "tailored_minio_dev_pass"
    paymob_hmac_secret: str = "dev_paymob_hmac_secret"
    paymob_api_key: str = ""
    paymob_integration_id: int = 0
    stripe_webhook_secret: str = "dev_stripe_webhook_secret"
    stripe_api_key: str = ""
    checkout_redirect_base: str = "http://localhost/plans"


settings = BillingSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)

BILLING_TABLES = [
    CreditWalletDB.__table__,
    CreditLedgerEntryDB.__table__,
    CreditHoldDB.__table__,
    CreditPackCatalogDB.__table__,
    PaymentOrderDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]

DEFAULT_PACKS = [
    {
        "pack_id": "free",
        "name": "Free Starter",
        "subtitle": "Included at verification",
        "credits": 2,
        "apps_equiv": "1 complete application",
        "popular": False,
        "prices": {
            "EGP": {"amount": 0, "amount_minor": 0, "label": "0 EGP", "per_credit": "0 EGP"},
            "SAR": {"amount": 0, "amount_minor": 0, "label": "0 SAR", "per_credit": "0 SAR"},
            "AED": {"amount": 0, "amount_minor": 0, "label": "0 AED", "per_credit": "0 AED"},
            "USD": {"amount": 0, "amount_minor": 0, "label": "$0", "per_credit": "$0"},
        },
    },
    {
        "pack_id": "starter",
        "name": "Starter",
        "subtitle": "Quick apply pack",
        "credits": 5,
        "apps_equiv": "2–3 applications",
        "popular": False,
        "prices": {
            "EGP": {"amount": 49, "amount_minor": 4900, "label": "49 EGP", "per_credit": "9.8 EGP/cr"},
            "SAR": {"amount": 12, "amount_minor": 1200, "label": "12 SAR", "per_credit": "2.4 SAR/cr"},
            "AED": {"amount": 12, "amount_minor": 1200, "label": "12 AED", "per_credit": "2.4 AED/cr"},
            "USD": {"amount": 2.99, "amount_minor": 299, "label": "$2.99", "per_credit": "$0.60/cr"},
        },
    },
    {
        "pack_id": "hunter",
        "name": "Hunter",
        "subtitle": "Active daily search",
        "credits": 25,
        "apps_equiv": "12–15 applications",
        "popular": True,
        "prices": {
            "EGP": {"amount": 179, "amount_minor": 17900, "label": "179 EGP", "per_credit": "7.1 EGP/cr"},
            "SAR": {"amount": 35, "amount_minor": 3500, "label": "35 SAR", "per_credit": "1.4 SAR/cr"},
            "AED": {"amount": 34, "amount_minor": 3400, "label": "34 AED", "per_credit": "1.36 AED/cr"},
            "USD": {"amount": 8.99, "amount_minor": 899, "label": "$8.99", "per_credit": "$0.36/cr"},
        },
    },
    {
        "pack_id": "sprint",
        "name": "Sprint",
        "subtitle": "Full job switch",
        "credits": 70,
        "apps_equiv": "35–40 applications",
        "popular": False,
        "prices": {
            "EGP": {"amount": 399, "amount_minor": 39900, "label": "399 EGP", "per_credit": "5.7 EGP/cr"},
            "SAR": {"amount": 75, "amount_minor": 7500, "label": "75 SAR", "per_credit": "1.07 SAR/cr"},
            "AED": {"amount": 72, "amount_minor": 7200, "label": "72 AED", "per_credit": "1.03 AED/cr"},
            "USD": {"amount": 18.99, "amount_minor": 1899, "label": "$18.99", "per_credit": "$0.27/cr"},
        },
    },
]


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _enqueue_outbox(
    session: Session,
    *,
    event_type: str,
    user_id: str,
    feature_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type="billing",
            aggregate_id=user_id,
            topic="billing.events.v1",
            event_type=event_type,
            partition_key=user_id,
            payload_json=json.dumps(payload, default=str),
            headers_json=json.dumps(
                {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "feature_key": feature_key,
                    "actor": {"user_id": user_id},
                }
            ),
        )
    )


def _seed_packs() -> None:
    with Session(engine) as session:
        for pk in DEFAULT_PACKS:
            if not session.get(CreditPackCatalogDB, pk["pack_id"]):
                session.add(
                    CreditPackCatalogDB(
                        pack_id=pk["pack_id"],
                        name=pk["name"],
                        subtitle=pk["subtitle"],
                        credits=pk["credits"],
                        apps_equiv=pk["apps_equiv"],
                        prices_json=json.dumps(pk["prices"]),
                        popular=pk["popular"],
                    )
                )
        session.commit()


def _get_or_create_wallet(session: Session, user_id: str) -> CreditWalletDB:
    wallet = session.get(CreditWalletDB, user_id)
    if not wallet:
        wallet = CreditWalletDB(user_id=user_id, available_credits=0, held_credits=0)
        session.add(wallet)
        session.flush()
    return wallet


def _grant_starter_credits(user_id: str, amount: int = 2) -> None:
    idem = f"starter_grant:{user_id}"
    with Session(engine) as session:
        if session.exec(select(CreditLedgerEntryDB).where(CreditLedgerEntryDB.idempotency_key == idem)).first():
            return
        wallet = _get_or_create_wallet(session, user_id)
        wallet.available_credits += amount
        wallet.version += 1
        wallet.updated_at = utc_now()
        session.add(wallet)
        session.add(
            CreditLedgerEntryDB(
                user_id=user_id,
                entry_type="starter_grant",
                delta=amount,
                balance_after=wallet.available_credits,
                job_target_label="Welcome Starter Allocation",
                idempotency_key=idem,
            )
        )
        session.commit()


def _commit_hold_tx(hold_id: str) -> Optional[Dict[str, Any]]:
    with Session(engine) as session:
        hold = session.get(CreditHoldDB, hold_id)
        if not hold or hold.status != "held":
            return None
        wallet = _get_or_create_wallet(session, hold.user_id)
        wallet.held_credits = max(0, wallet.held_credits - hold.amount)
        wallet.version += 1
        wallet.updated_at = utc_now()
        hold.status = "committed"
        hold.resolved_at = utc_now()
        session.add(wallet)
        session.add(hold)
        idem = f"commit:{hold.id}"
        if not session.exec(select(CreditLedgerEntryDB).where(CreditLedgerEntryDB.idempotency_key == idem)).first():
            session.add(
                CreditLedgerEntryDB(
                    user_id=hold.user_id,
                    entry_type="hold_committed",
                    delta=-hold.amount,
                    balance_after=wallet.available_credits,
                    hold_id=hold.id,
                    reference_doc_id=hold.doc_id,
                    job_target_label=f"Settled: {hold.reason} ({hold.doc_id})",
                    idempotency_key=idem,
                )
            )
        if wallet.available_credits <= wallet.low_balance_threshold:
            _enqueue_outbox(
                session,
                event_type="credits.low_balance",
                user_id=hold.user_id,
                feature_key="billing.credit.commit",
                payload={"user_id": hold.user_id, "available_credits": wallet.available_credits},
            )
        session.commit()
        return {"hold_id": hold.id, "status": "committed", "available_credits": wallet.available_credits}


def _refund_hold_tx(hold_id: str, reason: str = "compile_failure") -> Optional[Dict[str, Any]]:
    with Session(engine) as session:
        hold = session.get(CreditHoldDB, hold_id)
        if not hold or hold.status != "held":
            return None
        wallet = _get_or_create_wallet(session, hold.user_id)
        wallet.held_credits = max(0, wallet.held_credits - hold.amount)
        wallet.available_credits += hold.amount
        wallet.version += 1
        wallet.updated_at = utc_now()
        hold.status = "refunded"
        hold.resolved_at = utc_now()
        session.add(wallet)
        session.add(hold)
        idem = f"refund:{hold.id}"
        if not session.exec(select(CreditLedgerEntryDB).where(CreditLedgerEntryDB.idempotency_key == idem)).first():
            session.add(
                CreditLedgerEntryDB(
                    user_id=hold.user_id,
                    entry_type="compile_refund",
                    delta=hold.amount,
                    balance_after=wallet.available_credits,
                    hold_id=hold.id,
                    reference_doc_id=hold.doc_id,
                    job_target_label=f"Automatic Failure Refund ({reason})",
                    idempotency_key=idem,
                )
            )
        _enqueue_outbox(
            session,
            event_type="credits.refunded",
            user_id=hold.user_id,
            feature_key="billing.credit.auto_refund",
            payload={
                "user_id": hold.user_id,
                "hold_id": hold.id,
                "doc_id": hold.doc_id,
                "amount": hold.amount,
                "reason": reason,
                "available_credits": wallet.available_credits,
            },
        )
        session.commit()
        return {"hold_id": hold.id, "status": "refunded", "available_credits": wallet.available_credits}


def _settle_payment_order(session: Session, order: PaymentOrderDB) -> Dict[str, Any]:
    if order.status == "paid":
        wallet = _get_or_create_wallet(session, order.user_id)
        return {"order_id": order.id, "status": "paid", "available_credits": wallet.available_credits}

    order.status = "paid"
    order.paid_at = utc_now()
    wallet = _get_or_create_wallet(session, order.user_id)
    wallet.available_credits += order.credits_to_grant
    wallet.version += 1
    wallet.updated_at = utc_now()
    session.add(order)
    session.add(wallet)

    idem = f"pack_purchase:{order.id}"
    session.add(
        CreditLedgerEntryDB(
            user_id=order.user_id,
            entry_type="pack_purchase",
            delta=order.credits_to_grant,
            balance_after=wallet.available_credits,
            payment_order_id=order.id,
            job_target_label=f"{order.pack_id.title()} Pack ({order.provider.title()} · {order.currency})",
            idempotency_key=idem,
        )
    )
    _enqueue_outbox(
        session,
        event_type="credits.pack.purchased",
        user_id=order.user_id,
        feature_key="billing.webhook.settle",
        payload={
            "user_id": order.user_id,
            "order_id": order.id,
            "pack_id": order.pack_id,
            "credits_granted": order.credits_to_grant,
            "available_credits": wallet.available_credits,
        },
    )
    session.commit()
    return {"order_id": order.id, "status": "paid", "available_credits": wallet.available_credits}


def _build_invoice_pdf(order: PaymentOrderDB) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 730, "TAILORED — CREDIT PACK RECEIPT")
    c.setFont("Helvetica", 11)
    c.drawString(60, 695, f"Invoice / Order ID: {order.id}")
    c.drawString(60, 675, f"Pack: {order.pack_id.title()} ({order.credits_to_grant} Credits)")
    c.drawString(60, 655, f"Provider / Method: {order.provider.upper()} · {order.payment_method}")
    c.drawString(60, 635, f"Amount: {order.amount_minor / 100:.2f} {order.currency}")
    c.drawString(60, 615, f"Status: {order.status.upper()}")
    c.drawString(60, 595, f"Issued At (UTC): {order.created_at.isoformat()}")
    c.drawString(60, 560, "Credits never expire. Zero recurring subscription charges.")
    c.save()
    return buf.getvalue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine, tables=BILLING_TABLES)
    _seed_packs()

    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable (%s)", exc)
    app.state.redpanda_producer = producer

    relay = OutboxRelay(
        session_factory=lambda: Session(engine),
        producer=producer,
        service_name=settings.service_name,
    )
    await relay.start()

    async def on_event(env: EventEnvelope) -> None:
        if env.event_type == "user.verified":
            uid = env.payload.get("user_id") or env.actor.user_id
            if uid:
                _grant_starter_credits(uid, int(env.payload.get("starter_credits", 2)))
        elif env.event_type == "latex.compile.succeeded":
            hid = env.payload.get("credit_hold_id")
            if hid:
                _commit_hold_tx(hid)
        elif env.event_type in ("latex.compile.failed", "cv.tailor.failed"):
            hid = env.payload.get("credit_hold_id")
            if hid:
                _refund_hold_tx(hid, reason=env.payload.get("error_message") or env.event_type)
        elif env.event_type == "user.erasure.requested":
            uid = env.payload.get("user_id") or env.actor.user_id
            if uid:
                with Session(engine) as session:
                    entries = session.exec(select(CreditLedgerEntryDB).where(CreditLedgerEntryDB.user_id == uid)).all()
                    for e in entries:
                        e.job_target_label = "Redacted (GDPR Erasure)"
                        session.add(e)
                    session.commit()

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["identity.lifecycle.v1", "documents.events.v1"],
        group_id="billing-saga-cg",
        handler=on_event,
        dlq_producer=producer,
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("Consumer delayed (%s)", exc)

    stop_evt = asyncio.Event()

    async def _expired_holds_reaper() -> None:
        while not stop_evt.is_set():
            try:
                now = utc_now()
                with Session(engine) as session:
                    expired_ids = [
                        h.id
                        for h in session.exec(
                            select(CreditHoldDB).where(
                                CreditHoldDB.status == "held",
                                CreditHoldDB.expires_at <= now,
                            )
                        ).all()
                    ]
                for hid in expired_ids:
                    _refund_hold_tx(hid, reason="hold_expired")
            except Exception as exc:
                logger.warning("Expired hold reaper error: %s", exc)
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                pass

    reaper_task = asyncio.create_task(_expired_holds_reaper())

    try:
        yield
    finally:
        stop_evt.set()
        reaper_task.cancel()
        try:
            await reaper_task
        except asyncio.CancelledError:
            pass
        await consumer.stop()
        await relay.stop()
        await producer.stop()


app = create_service_app(
    settings,
    title="Tailored Billing & Credits Service",
    lifespan=lifespan,
)


# --- Schemas ---

class CheckoutRequest(BaseModel):
    pack_id: str
    currency: str = "EGP"
    payment_method: str = "card"  # card | meeza | wallet | fawry | apple_pay


class CreditHoldRequest(BaseModel):
    user_id: str
    amount: int = 1
    reason: str = "cv_tailor"
    doc_id: str
    idempotency_key: str


class CreditHoldResolveRequest(BaseModel):
    hold_id: str
    reason: str = "completed"


# --- Endpoints ---

@app.get("/api/v1/credits/balance")
async def get_balance(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        wallet = _get_or_create_wallet(session, ctx.user_id)
        session.commit()
        return {
            "user_id": wallet.user_id,
            "available_credits": wallet.available_credits,
            "held_credits": wallet.held_credits,
            "low_balance_threshold": wallet.low_balance_threshold,
            "version": wallet.version,
        }


@app.get("/api/v1/credits/packs")
async def list_packs(currency: str = Query(default="EGP")) -> List[Dict[str, Any]]:
    curr = currency.upper()
    if curr not in ("EGP", "SAR", "AED", "USD"):
        curr = "EGP"
    with Session(engine) as session:
        packs = session.exec(select(CreditPackCatalogDB).where(CreditPackCatalogDB.active == True)).all()  # noqa: E712
        out = []
        for p in packs:
            prices = json.loads(p.prices_json or "{}")
            out.append(
                {
                    "pack_id": p.pack_id,
                    "name": p.name,
                    "subtitle": p.subtitle,
                    "credits": p.credits,
                    "apps_equiv": p.apps_equiv,
                    "popular": p.popular,
                    "currency": curr,
                    "price": prices.get(curr, prices.get("USD")),
                    "prices": prices,
                }
            )
        return out


@app.get("/api/v1/credits/ledger")
async def get_ledger(ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(CreditLedgerEntryDB)
            .where(CreditLedgerEntryDB.user_id == ctx.user_id)
            .order_by(CreditLedgerEntryDB.created_at.desc())
        ).all()
        return [
            {
                "id": r.id,
                "date": r.created_at.strftime("%b %d"),
                "created_at": r.created_at.isoformat(),
                "action": r.entry_type,
                "job_target": r.job_target_label,
                "delta": r.delta,
                "balance_after": r.balance_after,
                "doc_id": r.reference_doc_id,
                "order_id": r.payment_order_id,
            }
            for r in rows
        ]


@app.post("/api/v1/credits/checkout", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="billing.checkout.create", resource_type="payment_order", action="create")
async def create_checkout(
    payload: CheckoutRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    curr = payload.currency.upper()
    idem = idempotency_key or f"chk_{ctx.user_id}_{uuid4().hex[:12]}"
    with Session(engine) as session:
        existing = session.exec(select(PaymentOrderDB).where(PaymentOrderDB.idempotency_key == idem)).first()
        if existing:
            return existing.model_dump()

        pack = session.get(CreditPackCatalogDB, payload.pack_id)
        if not pack or pack.credits <= 0 or pack.pack_id == "free":
            raise NotFoundError("Purchasable credit pack not found.")
        prices = json.loads(pack.prices_json or "{}")
        price_info = prices.get(curr) or prices.get("USD")
        provider = "paymob" if curr == "EGP" else "stripe"
        provider_order_id = f"{provider}_ord_{uuid4().hex[:12]}"
        fawry_ref = f"99{uuid4().int % 10**8:08d}" if payload.payment_method == "fawry" else None

        order = PaymentOrderDB(
            user_id=ctx.user_id,
            pack_id=pack.pack_id,
            provider=provider,
            payment_method=payload.payment_method,
            currency=curr,
            amount_minor=int(price_info.get("amount_minor", 0)),
            credits_to_grant=pack.credits,
            status="pending",
            provider_order_id=provider_order_id,
            fawry_ref_code=fawry_ref,
            idempotency_key=idem,
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        checkout_url = f"https://checkout.tailored.app/{provider}/{order.provider_order_id}"
        if provider == "paymob" and settings.paymob_api_key:
            try:
                async with httpx.AsyncClient(timeout=8.0) as hc:
                    auth_r = await hc.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": settings.paymob_api_key})
                    auth_r.raise_for_status()
                    pm_tok = auth_r.json()["token"]
                    ord_r = await hc.post(
                        "https://accept.paymob.com/api/ecommerce/orders",
                        json={"auth_token": pm_tok, "delivery_needed": "false", "amount_cents": str(order.amount_minor), "currency": order.currency, "merchant_order_id": order.provider_order_id, "items": []},
                    )
                    ord_r.raise_for_status()
                    pm_oid = ord_r.json()["id"]
                    if settings.paymob_integration_id:
                        pk_r = await hc.post(
                            "https://accept.paymob.com/api/acceptance/payment_keys",
                            json={"auth_token": pm_tok, "amount_cents": str(order.amount_minor), "expiration": 3600, "order_id": pm_oid, "currency": order.currency, "integration_id": settings.paymob_integration_id, "billing_data": {"email": f"{ctx.user_id}@tailored.app", "first_name": "Tailored", "last_name": "User", "phone_number": "NA", "city": "Cairo", "country": "EG"}},
                        )
                        pk_r.raise_for_status()
                        checkout_url = f"https://accept.paymob.com/api/acceptance/iframes/default?payment_token={pk_r.json()['token']}"
            except Exception as exc:
                logger.warning("Paymob live session fallback to sandbox URL: %s", exc)
        elif provider == "stripe" and settings.stripe_api_key:
            try:
                async with httpx.AsyncClient(timeout=8.0) as hc:
                    sr = await hc.post(
                        "https://api.stripe.com/v1/checkout/sessions",
                        headers={"Authorization": f"Bearer {settings.stripe_api_key}"},
                        data={
                            "mode": "payment",
                            "success_url": f"{settings.checkout_redirect_base}?paid=1",
                            "cancel_url": f"{settings.checkout_redirect_base}?cancelled=1",
                            "line_items[0][price_data][currency]": order.currency.lower(),
                            "line_items[0][price_data][unit_amount]": str(order.amount_minor),
                            "line_items[0][price_data][product_data][name]": f"Tailored {pack.name} ({pack.credits} credits)",
                            "line_items[0][quantity]": "1",
                            "client_reference_id": order.provider_order_id,
                        },
                    )
                    sr.raise_for_status()
                    checkout_url = sr.json().get("url") or checkout_url
            except Exception as exc:
                logger.warning("Stripe live session fallback to sandbox URL: %s", exc)
        res = order.model_dump()
        res["created_at"] = order.created_at.isoformat()
        res["checkout_url"] = checkout_url
        return res


@app.get("/api/v1/credits/orders/{order_id}")
async def get_order(order_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        order = session.get(PaymentOrderDB, order_id)
        if not order or order.user_id != ctx.user_id:
            raise NotFoundError("Payment order not found.")
        return order.model_dump()


@app.get("/api/v1/credits/invoices/{order_id}/pdf")
async def download_invoice_pdf(order_id: str, ctx: RequestContext = Depends(require_user)) -> Response:
    with Session(engine) as session:
        order = session.get(PaymentOrderDB, order_id)
        if not order or order.user_id != ctx.user_id:
            raise NotFoundError("Invoice order not found.")
        pdf_bytes = _build_invoice_pdf(order)
        try:
            key = f"receipts/{ctx.user_id}/{order.id}.pdf"
            _s3_client().put_object(Bucket="invoices", Key=key, Body=pdf_bytes, ContentType="application/pdf")
            order.invoice_object_key = key
            session.add(order)
            session.commit()
        except Exception as exc:
            logger.warning("MinIO invoice store failed (%s)", exc)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Tailored_Receipt_{order_id}.pdf"'},
    )


@app.post("/api/v1/webhooks/paymob")
@audit_feature(feature_key="billing.webhook.settle", resource_type="payment_order", action="paymob_webhook")
async def paymob_webhook(
    request: Request,
    x_paymob_hmac: Optional[str] = Header(default=None, alias="X-Paymob-Hmac"),
) -> Dict[str, Any]:
    raw_body = await request.body()
    if x_paymob_hmac:
        expected = hmac.new(
            settings.paymob_hmac_secret.encode("utf-8"), raw_body, hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(expected, x_paymob_hmac):
            raise HTTPException(status_code=401, detail="Invalid Paymob HMAC signature")
    elif settings.environment != "development":
        raise HTTPException(status_code=401, detail="Missing Paymob HMAC signature")

    data = json.loads(raw_body.decode("utf-8"))
    provider_order_id = data.get("provider_order_id") or data.get("order", {}).get("id")
    success = bool(data.get("success", True))
    with Session(engine) as session:
        order = session.exec(
            select(PaymentOrderDB).where(
                PaymentOrderDB.provider == "paymob",
                PaymentOrderDB.provider_order_id == str(provider_order_id),
            )
        ).first()
        if not order:
            raise NotFoundError("Paymob order not found.")
        if not success:
            order.status = "failed"
            session.add(order)
            session.commit()
            return {"order_id": order.id, "status": "failed"}
        return _settle_payment_order(session, order)


@app.post("/api/v1/webhooks/stripe")
@audit_feature(feature_key="billing.webhook.settle", resource_type="payment_order", action="stripe_webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(default=None, alias="Stripe-Signature"),
) -> Dict[str, Any]:
    raw_body = await request.body()
    if stripe_signature:
        expected = hmac.new(
            settings.stripe_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, stripe_signature.replace("v1=", "")):
            raise HTTPException(status_code=401, detail="Invalid Stripe signature")
    elif settings.environment != "development":
        raise HTTPException(status_code=401, detail="Missing Stripe signature")

    data = json.loads(raw_body.decode("utf-8"))
    provider_order_id = data.get("provider_order_id") or data.get("data", {}).get("object", {}).get("id")
    with Session(engine) as session:
        order = session.exec(
            select(PaymentOrderDB).where(
                PaymentOrderDB.provider == "stripe",
                PaymentOrderDB.provider_order_id == str(provider_order_id),
            )
        ).first()
        if not order:
            raise NotFoundError("Stripe order not found.")
        return _settle_payment_order(session, order)


# --- Internal Saga Endpoints ---

@app.post("/internal/credits/hold", status_code=status.HTTP_201_CREATED)
async def internal_create_hold(
    payload: CreditHoldRequest,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    with Session(engine) as session:
        existing = session.exec(
            select(CreditHoldDB).where(CreditHoldDB.idempotency_key == payload.idempotency_key)
        ).first()
        if existing:
            return {"hold_id": existing.id, "status": existing.status, "amount": existing.amount}

        wallet = _get_or_create_wallet(session, payload.user_id)
        if wallet.available_credits < payload.amount:
            raise InsufficientCreditsError(
                f"This action requires {payload.amount} credit(s), but your available balance is {wallet.available_credits}.",
                metadata={
                    "required_credits": payload.amount,
                    "available_credits": wallet.available_credits,
                    "resume_action": payload.reason,
                },
            )

        wallet.available_credits -= payload.amount
        wallet.held_credits += payload.amount
        wallet.version += 1
        wallet.updated_at = utc_now()
        hold = CreditHoldDB(
            user_id=payload.user_id,
            amount=payload.amount,
            reason=payload.reason,
            doc_id=payload.doc_id,
            status="held",
            idempotency_key=payload.idempotency_key,
            expires_at=utc_now() + timedelta(minutes=15),
        )
        session.add(wallet)
        session.add(hold)
        session.flush()
        session.add(
            CreditLedgerEntryDB(
                user_id=payload.user_id,
                entry_type="hold_created",
                delta=0,
                balance_after=wallet.available_credits,
                hold_id=hold.id,
                reference_doc_id=payload.doc_id,
                job_target_label=f"Credit Hold: {payload.reason} ({payload.doc_id})",
                idempotency_key=f"hold_led:{hold.id}",
            )
        )
        session.commit()
        return {"hold_id": hold.id, "status": "held", "available_credits": wallet.available_credits}


@app.post("/internal/credits/commit")
async def internal_commit_hold(
    payload: CreditHoldResolveRequest,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    res = _commit_hold_tx(payload.hold_id)
    if not res:
        return {"hold_id": payload.hold_id, "status": "already_resolved"}
    return res


@app.post("/internal/credits/release")
async def internal_release_hold(
    payload: CreditHoldResolveRequest,
    _: RequestContext = Depends(require_internal_service),
) -> Dict[str, Any]:
    res = _refund_hold_tx(payload.hold_id, reason=payload.reason)
    if not res:
        return {"hold_id": payload.hold_id, "status": "already_resolved"}
    return res
