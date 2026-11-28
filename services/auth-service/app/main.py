from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import secrets
import smtplib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import pyotp
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, delete
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    ActorContext,
    ConflictError,
    EventEnvelope,
    ForbiddenError,
    InternalHttpClient,
    NotFoundError,
    OutboxEvent,
    OutboxRelay,
    ProcessedEvent,
    RedpandaProducer,
    RequestContext,
    ServiceSettings,
    UnauthorizedError,
    audit_feature,
    create_service_app,
    require_admin,
    require_user,
)
from tailored_kit.auth.jwks_client import sign_identity_headers
from tailored_kit.telemetry_otel.setup import get_current_trace_context

from app.models import (
    FeatureFlagDB,
    FeatureFlagOverrideDB,
    IdentityPseudonymDB,
    OAuthIdentityDB,
    OtpVerificationDB,
    PrivacyConsentDB,
    TotpMfaDB,
    UserDB,
    UserSessionDB,
    WorkspacePreferenceDB,
    utc_now,
)
from app.security import (
    RsaKeyManager,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    hash_token,
    verify_password,
)

logger = logging.getLogger(__name__)


class AuthSettings(ServiceSettings):
    service_name: str = "auth-service"
    database_url: str = "postgresql+psycopg://auth_svc:tailored_auth_pass@postgres:5432/auth_db"
    privacy_vault_database_url: str = (
        "postgresql+psycopg://privacy_vault_svc:tailored_vault_pass@postgres:5432/privacy_vault_db"
    )
    documents_service_url: str = "http://documents-service:8004"
    rsa_key_dir: str = "/data/auth_keys"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    admin_bootstrap_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "noreply@tailored.app"
    google_client_id: str = ""
    google_client_secret: str = ""
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    oauth_redirect_base_url: str = "http://localhost"


settings = AuthSettings()


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        logger.debug("SMTP_HOST unset; skipping email delivery to %s (%s)", to_email, subject)
        return
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            if settings.smtp_port in (587, 2525):
                smtp.starttls()
            if settings.smtp_user and settings.smtp_pass:
                smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
    except Exception as exc:
        logger.warning("SMTP email delivery failed for %s: %s", to_email, exc)


async def _send_email_async(to_email: str, subject: str, body: str) -> None:
    await asyncio.to_thread(_send_email_sync, to_email, subject, body)

auth_engine = create_engine(settings.database_url, pool_pre_ping=True)
vault_engine = create_engine(settings.privacy_vault_database_url, pool_pre_ping=True)
key_manager = RsaKeyManager(settings.rsa_key_dir)

AUTH_TABLES = [
    UserDB.__table__,
    OAuthIdentityDB.__table__,
    UserSessionDB.__table__,
    OtpVerificationDB.__table__,
    TotpMfaDB.__table__,
    WorkspacePreferenceDB.__table__,
    PrivacyConsentDB.__table__,
    FeatureFlagDB.__table__,
    FeatureFlagOverrideDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]

DEFAULT_FLAGS = [
    ("ai.ambient.proactive_nudges", True, 100, "Calm proactive AI suggestions from passive behavior"),
    ("ai.studio.metric_guard", True, 100, "Zero-hallucination quantitative claim interception"),
    ("billing.paymob", True, 100, "Egypt Paymob card/wallet/Fawry checkout"),
    ("billing.stripe", True, 100, "GCC & Global Stripe card/Apple Pay checkout"),
    ("jobs.public_explore", True, 100, "Public unauthenticated /explore radar preview"),
    ("jobs.screenshot_ocr", True, 100, "Job description screenshot upload extraction"),
]


def _enqueue_outbox(
    session: Session,
    *,
    aggregate_type: str,
    aggregate_id: str,
    topic: str,
    event_type: str,
    user_id: str,
    anon_id: Optional[str],
    feature_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            topic=topic,
            event_type=event_type,
            partition_key=user_id,
            payload_json=json.dumps(payload, default=str),
            headers_json=json.dumps(
                {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "feature_key": feature_key,
                    "actor": {"user_id": user_id, "analytics_anon_id": anon_id},
                }
            ),
        )
    )


async def _sync_flags_to_redis(redis_client: aioredis.Redis) -> Dict[str, Any]:
    catalog: Dict[str, Any] = {}
    with Session(auth_engine) as session:
        flags = session.exec(select(FeatureFlagDB)).all()
        overrides = session.exec(select(FeatureFlagOverrideDB)).all()
        ov_by_flag: Dict[str, Dict[str, bool]] = {}
        for ov in overrides:
            ov_by_flag.setdefault(ov.flag_key, {})[ov.user_id] = ov.enabled
        for fl in flags:
            catalog[fl.key] = {
                "enabled": fl.enabled,
                "rollout_percent": fl.rollout_percent,
                "overrides": ov_by_flag.get(fl.key, {}),
                "description": fl.description,
            }
    await redis_client.set("ff:catalog", json.dumps(catalog))
    return catalog


def _init_databases() -> None:
    SQLModel.metadata.create_all(auth_engine, tables=AUTH_TABLES)
    SQLModel.metadata.create_all(vault_engine, tables=[IdentityPseudonymDB.__table__])
    with Session(auth_engine) as session:
        for key, enabled, pct, desc in DEFAULT_FLAGS:
            if not session.get(FeatureFlagDB, key):
                session.add(
                    FeatureFlagDB(
                        key=key,
                        enabled=enabled,
                        rollout_percent=pct,
                        description=desc,
                    )
                )
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_databases()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable on startup (%s)", exc)
    app.state.redpanda_producer = producer

    relay = OutboxRelay(
        session_factory=lambda: Session(auth_engine),
        producer=producer,
        service_name=settings.service_name,
    )
    await relay.start()
    await _sync_flags_to_redis(redis_client)

    app.state.internal_http = InternalHttpClient(
        caller_service=settings.service_name,
        hmac_secret=settings.internal_hmac_secret,
        timeout_seconds=5.0,
    )

    try:
        yield
    finally:
        await app.state.internal_http.close()
        await relay.stop()
        await producer.stop()
        await redis_client.aclose()


app = create_service_app(
    settings,
    title="Tailored Auth & Identity Service",
    lifespan=lifespan,
)


# --- Schemas ---

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str = ""
    device_label: Optional[str] = "Web Browser"


class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None
    device_label: Optional[str] = "Web Browser"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyOtpRequest(BaseModel):
    email: str
    code: str


class ResendOtpRequest(BaseModel):
    email: str
    purpose: str = "verify_email"


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str = Field(min_length=6)


class OAuthCallbackRequest(BaseModel):
    provider_user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: str = ""
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    device_label: Optional[str] = "OAuth Web"


class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=6)


class ChangeEmailRequest(BaseModel):
    new_email: str
    otp_code: Optional[str] = None


class TotpVerifyRequest(BaseModel):
    code: str


class PreferencesPatchRequest(BaseModel):
    default_home_route: Optional[str] = None
    list_density: Optional[str] = None
    default_studio_intensity: Optional[str] = None
    preferred_currency: Optional[str] = None
    chat_side: Optional[str] = None
    collapsed_rail: Optional[bool] = None


class PrivacyPatchRequest(BaseModel):
    analytics_micro_signals: Optional[bool] = None
    ai_passive_learning: Optional[bool] = None
    proactive_nudges: Optional[bool] = None


class FeatureFlagPutRequest(BaseModel):
    enabled: bool = True
    rollout_percent: int = Field(default=100, ge=0, le=100)
    description: str = ""


class DeleteAccountRequest(BaseModel):
    confirm: str
    password: Optional[str] = None


# --- Helpers ---

def _get_or_create_pseudonym(user_id: str) -> str:
    with Session(vault_engine) as v_sess:
        row = v_sess.get(IdentityPseudonymDB, user_id)
        if row:
            return row.analytics_anon_id
        anon_id = str(uuid4())
        v_sess.add(IdentityPseudonymDB(user_id=user_id, analytics_anon_id=anon_id))
        v_sess.commit()
        return anon_id


def _create_otp(session: Session, user_id: str, email: str, purpose: str) -> str:
    code = f"{secrets.randbelow(900000) + 100000}"
    session.add(
        OtpVerificationDB(
            user_id=user_id,
            purpose=purpose,
            target_email=email.lower().strip(),
            code_hash=hash_token(code),
            expires_at=utc_now() + timedelta(minutes=15),
        )
    )
    return code


def _issue_session_tokens(
    session: Session,
    *,
    user: UserDB,
    anon_id: str,
    device_label: str,
    ip_prefix: str,
) -> Dict[str, Any]:
    refresh_raw = f"rt_{secrets.token_urlsafe(36)}"
    sess = UserSessionDB(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_raw),
        device_label=device_label or "Web Browser",
        ip_prefix=ip_prefix or "127.0.0.1",
        expires_at=utc_now() + timedelta(days=settings.refresh_token_ttl_days),
    )
    session.add(sess)
    session.flush()

    access_token, expires_in = key_manager.issue_access_token(
        user_id=user.id,
        session_id=sess.id,
        analytics_anon_id=anon_id,
        email=user.email,
        role=user.role,
        email_verified=user.email_verified,
        ttl_minutes=settings.access_token_ttl_minutes,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_raw,
        "token_type": "bearer",
        "expires_in": expires_in,
        "session_id": sess.id,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "email_verified": user.email_verified,
            "role": user.role,
        },
    }


async def _cache_user_privacy_and_anon(
    redis_client: aioredis.Redis,
    user_id: str,
    anon_id: str,
    consent_dict: Dict[str, bool],
) -> None:
    await redis_client.setex(f"anon_map:{user_id}", 86400, anon_id)
    await redis_client.setex(
        f"consent:{user_id}",
        86400,
        json.dumps(consent_dict),
    )


# --- Public & Gateway Internal Routes ---

@app.get("/.well-known/jwks.json")
async def jwks() -> Dict[str, Any]:
    return key_manager.jwks()


@app.get("/internal/verify")
async def forward_auth_verify(request: Request, response: Response) -> Dict[str, Any]:
    """Traefik ForwardAuth endpoint validating Bearer RS256 JWT + Redis session revocation."""
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif request.query_params.get("token"):
        token = request.query_params["token"].strip()
    elif request.headers.get("X-Forwarded-Uri"):
        from urllib.parse import parse_qs, urlparse

        parsed_uri = urlparse(request.headers["X-Forwarded-Uri"])
        qs_tokens = parse_qs(parsed_uri.query).get("token")
        if qs_tokens:
            token = qs_tokens[0].strip()

    if not token:
        raise UnauthorizedError("Missing Bearer access token.")

    try:
        claims = key_manager.decode_access_token(token)
    except Exception as exc:
        raise UnauthorizedError(f"Invalid or expired token: {exc}")

    sid = str(claims.get("sid") or "")
    if sid and await request.app.state.redis.get(f"session:revoked:{sid}"):
        raise UnauthorizedError("Session has been revoked.")

    signed = sign_identity_headers(
        secret=settings.internal_hmac_secret,
        user_id=str(claims["sub"]),
        session_id=sid,
        analytics_anon_id=str(claims.get("anon_id") or ""),
        role=str(claims.get("role") or "user"),
    )
    for k, v in signed.items():
        response.headers[k] = v
    return {"valid": True, "user_id": claims["sub"], "session_id": sid}


# --- Auth Flows ---

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
@audit_feature(feature_key="auth.register", resource_type="user", action="register")
async def register(payload: RegisterRequest, request: Request) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    with Session(auth_engine) as session:
        existing = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if existing:
            raise ConflictError("An account with this email already exists.")

        assigned_role = (
            "admin"
            if settings.admin_bootstrap_email and email == settings.admin_bootstrap_email.lower().strip()
            else "user"
        )
        user = UserDB(
            email=email,
            full_name=payload.full_name.strip() or email.split("@")[0],
            password_hash=hash_password(payload.password),
            email_verified=False,
            role=assigned_role,
        )
        session.add(user)
        session.flush()

        prefs = WorkspacePreferenceDB(user_id=user.id)
        consent = PrivacyConsentDB(user_id=user.id)
        session.add(prefs)
        session.add(consent)

        otp_code = _create_otp(session, user.id, email, "verify_email")
        anon_id = _get_or_create_pseudonym(user.id)
        ip_prefix = request.client.host if request.client else "127.0.0.1"
        tokens = _issue_session_tokens(
            session,
            user=user,
            anon_id=anon_id,
            device_label=payload.device_label or "Web Browser",
            ip_prefix=ip_prefix,
        )
        _enqueue_outbox(
            session,
            aggregate_type="user",
            aggregate_id=user.id,
            topic="identity.lifecycle.v1",
            event_type="user.registered",
            user_id=user.id,
            anon_id=anon_id,
            feature_key="auth.register",
            payload={"user_id": user.id, "email": email, "full_name": user.full_name},
        )
        uid = user.id
        consent_dict = {
            "analytics_micro_signals": consent.analytics_micro_signals,
            "ai_passive_learning": consent.ai_passive_learning,
            "proactive_nudges": consent.proactive_nudges,
        }
        session.commit()

    await _cache_user_privacy_and_anon(request.app.state.redis, uid, anon_id, consent_dict)
    await _send_email_async(
        email,
        "Verify your Tailored account",
        f"Your 6-digit verification code is: {otp_code}\n\nExpires in 15 minutes.",
    )
    if settings.environment == "development":
        tokens["dev_otp"] = otp_code
    return tokens


@app.post("/api/v1/auth/login")
@audit_feature(feature_key="auth.login.password", resource_type="session", action="login")
async def login(payload: LoginRequest, request: Request) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    with Session(auth_engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if user.status != "active":
            raise ForbiddenError("Account is not active.")

        mfa = session.get(TotpMfaDB, user.id)
        if mfa and mfa.enabled:
            if not payload.totp_code:
                raise UnauthorizedError(
                    "Two-factor authentication code is required.",
                    metadata={"requires_2fa": True},
                )
            secret = decrypt_secret(mfa.encrypted_secret, settings.internal_hmac_secret)
            totp = pyotp.TOTP(secret)
            valid_totp = totp.verify(payload.totp_code.strip(), valid_window=1)
            if not valid_totp:
                # Check single-use recovery code
                hashes = json.loads(mfa.recovery_codes_hashes or "[]")
                code_h = hash_token(payload.totp_code.strip())
                if code_h in hashes:
                    hashes.remove(code_h)
                    mfa.recovery_codes_hashes = json.dumps(hashes)
                    session.add(mfa)
                else:
                    raise UnauthorizedError("Invalid 2FA verification code.")

        anon_id = _get_or_create_pseudonym(user.id)
        consent = session.get(PrivacyConsentDB, user.id) or PrivacyConsentDB(user_id=user.id)
        ip_prefix = request.client.host if request.client else "127.0.0.1"
        tokens = _issue_session_tokens(
            session,
            user=user,
            anon_id=anon_id,
            device_label=payload.device_label or "Web Browser",
            ip_prefix=ip_prefix,
        )
        uid = user.id
        consent_dict = {
            "analytics_micro_signals": consent.analytics_micro_signals,
            "ai_passive_learning": consent.ai_passive_learning,
            "proactive_nudges": consent.proactive_nudges,
        }
        session.commit()

    await _cache_user_privacy_and_anon(request.app.state.redis, uid, anon_id, consent_dict)
    return tokens


@app.post("/api/v1/auth/refresh")
async def refresh_token(payload: RefreshRequest, request: Request) -> Dict[str, Any]:
    token_hash = hash_token(payload.refresh_token)
    with Session(auth_engine) as session:
        old_sess = session.exec(
            select(UserSessionDB).where(UserSessionDB.refresh_token_hash == token_hash)
        ).first()
        if not old_sess or old_sess.revoked_at is not None:
            raise UnauthorizedError("Refresh token is invalid or revoked.")
        exp = old_sess.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < utc_now():
            raise UnauthorizedError("Refresh token has expired.")

        user = session.get(UserDB, old_sess.user_id)
        if not user or user.status != "active":
            raise UnauthorizedError("User account inactive.")

        old_sess.revoked_at = utc_now()
        session.add(old_sess)
        await request.app.state.redis.setex(
            f"session:revoked:{old_sess.id}", settings.access_token_ttl_minutes * 60, "1"
        )

        anon_id = _get_or_create_pseudonym(user.id)
        tokens = _issue_session_tokens(
            session,
            user=user,
            anon_id=anon_id,
            device_label=old_sess.device_label,
            ip_prefix=old_sess.ip_prefix,
        )
        session.commit()
        return tokens


@app.post("/api/v1/auth/logout")
@audit_feature(feature_key="auth.session.revoke", resource_type="session", action="logout")
async def logout(request: Request, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    if ctx.session_id:
        await request.app.state.redis.setex(
            f"session:revoked:{ctx.session_id}", settings.access_token_ttl_minutes * 60, "1"
        )
        with Session(auth_engine) as session:
            sess = session.get(UserSessionDB, ctx.session_id)
            if sess and sess.revoked_at is None:
                sess.revoked_at = utc_now()
                session.add(sess)
                session.commit()
    return {"success": True}


@app.post("/api/v1/auth/verify-email")
@audit_feature(feature_key="auth.otp.verify", resource_type="user", action="verify_email")
async def verify_email(payload: VerifyOtpRequest, request: Request) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    with Session(auth_engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if not user:
            raise NotFoundError("Account not found.")
        otp = session.exec(
            select(OtpVerificationDB)
            .where(
                OtpVerificationDB.user_id == user.id,
                OtpVerificationDB.purpose == "verify_email",
                OtpVerificationDB.consumed_at.is_(None),
            )
            .order_by(OtpVerificationDB.created_at.desc())
        ).first()
        if not otp or otp.code_hash != hash_token(payload.code.strip()):
            if otp:
                otp.attempts += 1
                session.add(otp)
                session.commit()
            raise UnauthorizedError("Invalid or expired verification code.")
        exp = otp.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < utc_now():
            raise UnauthorizedError("Verification code expired.")

        otp.consumed_at = utc_now()
        already_verified = user.email_verified
        user.email_verified = True
        user.updated_at = utc_now()
        session.add(otp)
        session.add(user)

        anon_id = _get_or_create_pseudonym(user.id)
        if not already_verified:
            _enqueue_outbox(
                session,
                aggregate_type="user",
                aggregate_id=user.id,
                topic="identity.lifecycle.v1",
                event_type="user.verified",
                user_id=user.id,
                anon_id=anon_id,
                feature_key="auth.otp.verify",
                payload={"user_id": user.id, "email": user.email, "starter_credits": 2},
            )
        session.commit()
    return {"verified": True, "email": email, "starter_credits_granted": not already_verified}


@app.post("/api/v1/auth/otp/resend")
async def resend_otp(payload: ResendOtpRequest) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    with Session(auth_engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if not user:
            return {"sent": True}
        code = _create_otp(session, user.id, email, payload.purpose)
        session.commit()
    await _send_email_async(email, "Your Tailored verification code", f"Code: {code}")
    resp: Dict[str, Any] = {"sent": True}
    if settings.environment == "development":
        resp["dev_otp"] = code
    return resp


@app.post("/api/v1/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    dev_code: Optional[str] = None
    with Session(auth_engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if user:
            dev_code = _create_otp(session, user.id, email, "reset_pw")
            session.commit()
    if dev_code:
        await _send_email_async(email, "Reset your Tailored password", f"Reset code: {dev_code}")
    resp: Dict[str, Any] = {"sent": True}
    if settings.environment == "development" and dev_code:
        resp["dev_otp"] = dev_code
    return resp


@app.post("/api/v1/auth/reset-password")
@audit_feature(feature_key="auth.password.reset", resource_type="user", action="reset_password")
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Dict[str, Any]:
    email = payload.email.lower().strip()
    with Session(auth_engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        if not user:
            raise NotFoundError("Account not found.")
        otp = session.exec(
            select(OtpVerificationDB)
            .where(
                OtpVerificationDB.user_id == user.id,
                OtpVerificationDB.purpose == "reset_pw",
                OtpVerificationDB.consumed_at.is_(None),
            )
            .order_by(OtpVerificationDB.created_at.desc())
        ).first()
        if not otp or otp.code_hash != hash_token(payload.code.strip()):
            raise UnauthorizedError("Invalid password reset code.")
        otp.consumed_at = utc_now()
        user.password_hash = hash_password(payload.new_password)
        user.updated_at = utc_now()
        session.add(otp)
        session.add(user)

        active_sessions = session.exec(
            select(UserSessionDB).where(UserSessionDB.user_id == user.id, UserSessionDB.revoked_at.is_(None))
        ).all()
        for s in active_sessions:
            s.revoked_at = utc_now()
            session.add(s)
            await request.app.state.redis.setex(
                f"session:revoked:{s.id}", settings.access_token_ttl_minutes * 60, "1"
            )
        session.commit()
    return {"reset": True}


@app.get("/api/v1/auth/oauth/{provider}/start")
async def oauth_start(provider: str, pending_intent: Optional[str] = None) -> Dict[str, Any]:
    if provider not in ("google", "linkedin"):
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    state = secrets.token_urlsafe(16)
    return {
        "provider": provider,
        "state": state,
        "pending_intent": pending_intent,
        "authorization_url": f"/api/v1/auth/oauth/{provider}/callback?state={state}",
    }


@app.post("/api/v1/auth/oauth/{provider}/callback")
@audit_feature(feature_key="auth.login.oauth", resource_type="oauth_identity", action="oauth_login")
async def oauth_callback(
    provider: str,
    payload: OAuthCallbackRequest,
    request: Request,
) -> Dict[str, Any]:
    if provider not in ("google", "linkedin"):
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    provider_uid = payload.provider_user_id or ""
    raw_email = payload.email or ""
    full_name = payload.full_name or ""

    if payload.code:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "google" and settings.google_client_id and settings.google_client_secret:
                tok_r = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": payload.code,
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "redirect_uri": payload.redirect_uri or f"{settings.oauth_redirect_base_url}/auth/oauth/google/callback",
                        "grant_type": "authorization_code",
                    },
                )
                tok_r.raise_for_status()
                access_tok = tok_r.json()["access_token"]
                prof_r = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_tok}"},
                )
                prof_r.raise_for_status()
                info = prof_r.json()
                provider_uid = str(info.get("sub") or provider_uid)
                raw_email = str(info.get("email") or raw_email)
                full_name = str(info.get("name") or full_name)
            elif provider == "linkedin" and settings.linkedin_client_id and settings.linkedin_client_secret:
                tok_r = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "authorization_code",
                        "code": payload.code,
                        "redirect_uri": payload.redirect_uri or f"{settings.oauth_redirect_base_url}/auth/oauth/linkedin/callback",
                        "client_id": settings.linkedin_client_id,
                        "client_secret": settings.linkedin_client_secret,
                    },
                )
                tok_r.raise_for_status()
                access_tok = tok_r.json()["access_token"]
                prof_r = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_tok}"},
                )
                prof_r.raise_for_status()
                info = prof_r.json()
                provider_uid = str(info.get("sub") or provider_uid)
                raw_email = str(info.get("email") or raw_email)
                full_name = str(info.get("name") or full_name)

    if not provider_uid or not raw_email:
        raise UnauthorizedError("OAuth identity payload missing verified subject or email.")
    email = raw_email.lower().strip()
    with Session(auth_engine) as session:
        oauth_row = session.exec(
            select(OAuthIdentityDB).where(
                OAuthIdentityDB.provider == provider,
                OAuthIdentityDB.provider_user_id == provider_uid,
            )
        ).first()
        newly_verified = False
        if oauth_row:
            user = session.get(UserDB, oauth_row.user_id)
        else:
            user = session.exec(select(UserDB).where(UserDB.email == email)).first()
            if not user:
                user = UserDB(
                    email=email,
                    full_name=full_name.strip() or email.split("@")[0],
                    password_hash=None,
                    email_verified=True,
                )
                session.add(user)
                session.flush()
                session.add(WorkspacePreferenceDB(user_id=user.id))
                session.add(PrivacyConsentDB(user_id=user.id))
                newly_verified = True
            session.add(
                OAuthIdentityDB(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_uid,
                    provider_email=email,
                )
            )
        assert user is not None
        anon_id = _get_or_create_pseudonym(user.id)
        if newly_verified:
            _enqueue_outbox(
                session,
                aggregate_type="user",
                aggregate_id=user.id,
                topic="identity.lifecycle.v1",
                event_type="user.verified",
                user_id=user.id,
                anon_id=anon_id,
                feature_key="auth.login.oauth",
                payload={"user_id": user.id, "email": user.email, "starter_credits": 2},
            )
        ip_prefix = request.client.host if request.client else "127.0.0.1"
        tokens = _issue_session_tokens(
            session,
            user=user,
            anon_id=anon_id,
            device_label=payload.device_label or f"{provider.title()} OAuth",
            ip_prefix=ip_prefix,
        )
        uid = user.id
        consent = session.get(PrivacyConsentDB, uid) or PrivacyConsentDB(user_id=uid)
        consent_dict = {
            "analytics_micro_signals": consent.analytics_micro_signals,
            "ai_passive_learning": consent.ai_passive_learning,
            "proactive_nudges": consent.proactive_nudges,
        }
        session.commit()

    await _cache_user_privacy_and_anon(request.app.state.redis, uid, anon_id, consent_dict)
    return tokens


# --- Account Security, 2FA, Sessions, Preferences, Privacy, Flags, GDPR ---

@app.get("/api/v1/account/security")
async def get_security_status(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        oauths = session.exec(select(OAuthIdentityDB).where(OAuthIdentityDB.user_id == user.id)).all()
        mfa = session.get(TotpMfaDB, user.id)
        has_pw = bool(user.password_hash)
        providers = [o.provider for o in oauths]
        can_unlink = has_pw or len(providers) > 1
        return {
            "email": user.email,
            "email_verified": user.email_verified,
            "has_password": has_pw,
            "two_factor_enabled": bool(mfa and mfa.enabled),
            "connected_providers": providers,
            "can_unlink_oauth": can_unlink,
        }


@app.post("/api/v1/account/change-password")
async def change_password(
    payload: ChangePasswordRequest, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        if user.password_hash:
            if not payload.current_password or not verify_password(payload.current_password, user.password_hash):
                raise UnauthorizedError("Current password is incorrect.")
        user.password_hash = hash_password(payload.new_password)
        user.updated_at = utc_now()
        session.add(user)
        session.commit()
    return {"updated": True, "has_password": True}


@app.post("/api/v1/account/change-email")
async def change_email(
    payload: ChangeEmailRequest, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    new_email = payload.new_email.lower().strip()
    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        if session.exec(select(UserDB).where(UserDB.email == new_email)).first():
            raise ConflictError("Email is already in use.")
        if not payload.otp_code:
            code = _create_otp(session, user.id, new_email, "change_email")
            session.commit()
            resp: Dict[str, Any] = {"verification_required": True}
            if settings.environment == "development":
                resp["dev_otp"] = code
            return resp
        otp = session.exec(
            select(OtpVerificationDB)
            .where(
                OtpVerificationDB.user_id == user.id,
                OtpVerificationDB.purpose == "change_email",
                OtpVerificationDB.target_email == new_email,
                OtpVerificationDB.consumed_at.is_(None),
            )
            .order_by(OtpVerificationDB.created_at.desc())
        ).first()
        if not otp or otp.code_hash != hash_token(payload.otp_code.strip()):
            raise UnauthorizedError("Invalid email verification code.")
        otp.consumed_at = utc_now()
        user.email = new_email
        user.updated_at = utc_now()
        session.add(otp)
        session.add(user)
        session.commit()
    return {"updated": True, "email": new_email}


@app.delete("/api/v1/account/oauth/{provider}")
async def unlink_oauth(provider: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        oauths = session.exec(select(OAuthIdentityDB).where(OAuthIdentityDB.user_id == user.id)).all()
        target = next((o for o in oauths if o.provider == provider), None)
        if not target:
            raise NotFoundError(f"{provider} is not linked.")
        if not user.password_hash and len(oauths) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Set an account password first so you don't lock yourself out.",
            )
        session.delete(target)
        session.commit()
    return {"unlinked": provider}


@app.post("/api/v1/account/2fa/setup")
async def setup_2fa(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        secret = pyotp.random_base32()
        recovery_codes = [f"TLR-{secrets.token_hex(3).upper()}" for _ in range(6)]
        hashes = [hash_token(c) for c in recovery_codes]

        existing = session.get(TotpMfaDB, user.id)
        enc = encrypt_secret(secret, settings.internal_hmac_secret)
        if existing:
            existing.encrypted_secret = enc
            existing.enabled = False
            existing.recovery_codes_hashes = json.dumps(hashes)
            session.add(existing)
        else:
            session.add(
                TotpMfaDB(
                    user_id=user.id,
                    encrypted_secret=enc,
                    enabled=False,
                    recovery_codes_hashes=json.dumps(hashes),
                )
            )
        session.commit()
        uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Tailored")
    return {"secret": secret, "otpauth_uri": uri, "recovery_codes": recovery_codes}


@app.post("/api/v1/account/2fa/enable")
@audit_feature(feature_key="auth.2fa.enable", resource_type="totp_mfa", action="enable")
async def enable_2fa(
    payload: TotpVerifyRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        mfa = session.get(TotpMfaDB, ctx.user_id)
        if not mfa:
            raise NotFoundError("Run 2FA setup first.")
        secret = decrypt_secret(mfa.encrypted_secret, settings.internal_hmac_secret)
        if not pyotp.TOTP(secret).verify(payload.code.strip(), valid_window=1):
            raise UnauthorizedError("Invalid TOTP verification code.")
        mfa.enabled = True
        mfa.enabled_at = utc_now()
        session.add(mfa)
        session.commit()
    return {"enabled": True}


@app.post("/api/v1/account/2fa/disable")
async def disable_2fa(
    payload: TotpVerifyRequest, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        mfa = session.get(TotpMfaDB, ctx.user_id)
        if not mfa or not mfa.enabled:
            return {"enabled": False}
        secret = decrypt_secret(mfa.encrypted_secret, settings.internal_hmac_secret)
        if not pyotp.TOTP(secret).verify(payload.code.strip(), valid_window=1):
            raise UnauthorizedError("Invalid TOTP code.")
        mfa.enabled = False
        session.add(mfa)
        session.commit()
    return {"enabled": False}


@app.get("/api/v1/account/sessions")
async def list_sessions(ctx: RequestContext = Depends(require_user)) -> List[Dict[str, Any]]:
    with Session(auth_engine) as session:
        rows = session.exec(
            select(UserSessionDB)
            .where(UserSessionDB.user_id == ctx.user_id, UserSessionDB.revoked_at.is_(None))
            .order_by(UserSessionDB.last_active_at.desc())
        ).all()
        return [
            {
                "id": r.id,
                "device": r.device_label,
                "location": r.geo_city,
                "last_active": r.last_active_at.isoformat(),
                "current": r.id == ctx.session_id,
            }
            for r in rows
        ]


@app.delete("/api/v1/account/sessions/{session_id}")
@audit_feature(feature_key="auth.session.revoke", resource_type="session", action="revoke")
async def revoke_session(
    session_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        row = session.get(UserSessionDB, session_id)
        if not row or row.user_id != ctx.user_id:
            raise NotFoundError("Session not found.")
        row.revoked_at = utc_now()
        session.add(row)
        session.commit()
    await request.app.state.redis.setex(
        f"session:revoked:{session_id}", settings.access_token_ttl_minutes * 60, "1"
    )
    return {"revoked": session_id}


@app.get("/api/v1/account/preferences")
async def get_preferences(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        prefs = session.get(WorkspacePreferenceDB, ctx.user_id)
        if not prefs:
            prefs = WorkspacePreferenceDB(user_id=ctx.user_id)
            session.add(prefs)
            session.commit()
            session.refresh(prefs)
        return prefs.model_dump()


@app.patch("/api/v1/account/preferences")
@audit_feature(feature_key="account.preferences.update", resource_type="workspace_preferences", action="update")
async def update_preferences(
    payload: PreferencesPatchRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        prefs = session.get(WorkspacePreferenceDB, ctx.user_id) or WorkspacePreferenceDB(user_id=ctx.user_id)
        for field_name, val in payload.model_dump(exclude_none=True).items():
            setattr(prefs, field_name, val)
        prefs.updated_at = utc_now()
        session.add(prefs)
        session.commit()
        session.refresh(prefs)
        return prefs.model_dump()


@app.get("/api/v1/account/privacy")
async def get_privacy(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        consent = session.get(PrivacyConsentDB, ctx.user_id)
        if not consent:
            consent = PrivacyConsentDB(user_id=ctx.user_id)
            session.add(consent)
            session.commit()
            session.refresh(consent)
        return consent.model_dump()


@app.patch("/api/v1/account/privacy")
@audit_feature(feature_key="account.privacy.update", resource_type="privacy_consents", action="update")
async def update_privacy(
    payload: PrivacyPatchRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        consent = session.get(PrivacyConsentDB, ctx.user_id) or PrivacyConsentDB(user_id=ctx.user_id)
        for field_name, val in payload.model_dump(exclude_none=True).items():
            setattr(consent, field_name, val)
        consent.updated_at = utc_now()
        session.add(consent)
        anon_id = _get_or_create_pseudonym(ctx.user_id)
        _enqueue_outbox(
            session,
            aggregate_type="privacy_consent",
            aggregate_id=ctx.user_id,
            topic="identity.lifecycle.v1",
            event_type="privacy.consent.updated",
            user_id=ctx.user_id,
            anon_id=anon_id,
            feature_key="account.privacy.update",
            payload={
                "user_id": ctx.user_id,
                "analytics_micro_signals": consent.analytics_micro_signals,
                "ai_passive_learning": consent.ai_passive_learning,
                "proactive_nudges": consent.proactive_nudges,
            },
        )
        session.commit()
        session.refresh(consent)
        result = consent.model_dump()
        consent_dict = {
            "analytics_micro_signals": consent.analytics_micro_signals,
            "ai_passive_learning": consent.ai_passive_learning,
            "proactive_nudges": consent.proactive_nudges,
        }

    await _cache_user_privacy_and_anon(request.app.state.redis, ctx.user_id, anon_id, consent_dict)
    return result


@app.get("/api/v1/flags")
async def list_flags(request: Request) -> Dict[str, Any]:
    raw = await request.app.state.redis.get("ff:catalog")
    if raw:
        return json.loads(raw)
    return await _sync_flags_to_redis(request.app.state.redis)


@app.put("/api/v1/admin/flags/{key}")
async def upsert_flag(
    key: str,
    payload: FeatureFlagPutRequest,
    request: Request,
    _: RequestContext = Depends(require_admin),
) -> Dict[str, Any]:
    with Session(auth_engine) as session:
        row = session.get(FeatureFlagDB, key)
        if row:
            row.enabled = payload.enabled
            row.rollout_percent = payload.rollout_percent
            row.description = payload.description or row.description
            row.updated_at = utc_now()
        else:
            row = FeatureFlagDB(
                key=key,
                enabled=payload.enabled,
                rollout_percent=payload.rollout_percent,
                description=payload.description,
            )
        session.add(row)
        session.commit()
    catalog = await _sync_flags_to_redis(request.app.state.redis)
    return {"key": key, "flag": catalog.get(key)}


@app.post("/api/v1/account/export")
@audit_feature(feature_key="account.gdpr.export", resource_type="gdpr_export", action="request")
async def request_gdpr_export(
    request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    resp = await client.post(
        f"{settings.documents_service_url}/internal/documents/gdpr-export",
        headers={"X-User-Id": ctx.user_id},
        json={"user_id": ctx.user_id, "email": ""},
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.get("/api/v1/account/export/{export_id}")
async def get_gdpr_export(
    export_id: str, request: Request, ctx: RequestContext = Depends(require_user)
) -> Any:
    client: InternalHttpClient = request.app.state.internal_http
    resp = await client.get(
        f"{settings.documents_service_url}/internal/documents/gdpr-export/{export_id}",
        headers={"X-User-Id": ctx.user_id},
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    if resp.headers.get("content-type", "").startswith("application/zip"):
        return Response(
            content=resp.content,
            media_type="application/zip",
            headers={
                "Content-Disposition": resp.headers.get(
                    "content-disposition", f'attachment; filename="tailored_export_{export_id}.zip"'
                )
            },
        )
    return resp.json()


@app.delete("/api/v1/account", status_code=status.HTTP_202_ACCEPTED)
@audit_feature(feature_key="account.gdpr.erase", resource_type="user", action="erase")
async def erase_account(
    payload: DeleteAccountRequest, request: Request, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    if payload.confirm.strip().upper() != "DELETE":
        raise HTTPException(status_code=400, detail="Confirmation text must be DELETE.")

    with Session(auth_engine) as session:
        user = session.get(UserDB, ctx.user_id)
        if not user:
            raise NotFoundError("User not found.")
        if user.password_hash and payload.password and not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Incorrect password confirmation.")

        sessions = session.exec(select(UserSessionDB).where(UserSessionDB.user_id == user.id)).all()
        for s in sessions:
            await request.app.state.redis.setex(
                f"session:revoked:{s.id}", settings.access_token_ttl_minutes * 60, "1"
            )

        user.status = "erasing"
        session.add(user)
        session.commit()

    # Publish erasure saga fan-out onto Redpanda
    producer: RedpandaProducer = request.app.state.redpanda_producer
    trace_id, span_id = get_current_trace_context()
    if producer and producer.is_ready:
        await producer.publish(
            "identity.lifecycle.v1",
            EventEnvelope(
                event_type="user.erasure.requested",
                producer_service=settings.service_name,
                trace_id=trace_id,
                span_id=span_id,
                feature_key="account.gdpr.erase",
                actor=ActorContext(user_id=ctx.user_id, analytics_anon_id=ctx.analytics_anon_id),
                payload={"user_id": ctx.user_id},
            ),
            partition_key=ctx.user_id,
        )

    # Crypto-Shredding: destroy privacy_vault_db pseudonym link + Redis caches
    with Session(vault_engine) as v_sess:
        v_sess.exec(delete(IdentityPseudonymDB).where(IdentityPseudonymDB.user_id == ctx.user_id))
        v_sess.commit()

    await request.app.state.redis.delete(f"anon_map:{ctx.user_id}", f"consent:{ctx.user_id}")

    # Hard-delete PII & auth rows in auth_db
    with Session(auth_engine) as session:
        for model in (
            OAuthIdentityDB,
            UserSessionDB,
            OtpVerificationDB,
            TotpMfaDB,
            WorkspacePreferenceDB,
            PrivacyConsentDB,
            FeatureFlagOverrideDB,
        ):
            session.exec(delete(model).where(model.user_id == ctx.user_id))
        session.exec(delete(UserDB).where(UserDB.id == ctx.user_id))
        session.commit()

    return {"status": "erased", "crypto_shredded": True, "user_id": ctx.user_id}
