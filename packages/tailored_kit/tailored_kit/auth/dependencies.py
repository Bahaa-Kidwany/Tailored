import hashlib
import hmac
from fastapi import Request

from tailored_kit.feature_context import get_current_feature_key
from tailored_kit.auth.context import RequestContext
from tailored_kit.auth.jwks_client import verify_identity_headers
from tailored_kit.errors import ForbiddenError, UnauthorizedError
from tailored_kit.telemetry_otel.setup import get_current_trace_context


async def optional_user(request: Request) -> RequestContext:
    """Extracts verified identity from Traefik ForwardAuth HMAC headers or returns anonymous context."""
    trace_id, _ = get_current_trace_context()
    feature_key = get_current_feature_key() or request.headers.get("X-Feature-Key")
    settings = getattr(request.app.state, "settings", None)
    secret = settings.internal_hmac_secret if settings else ""

    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id", "")
    anon_id = request.headers.get("X-Analytics-Anon-Id", "")
    role = request.headers.get("X-User-Role", "user")
    ts_raw = request.headers.get("X-Identity-Ts")
    sig = request.headers.get("X-Identity-Sig")

    if user_id and secret and verify_identity_headers(
        secret=secret,
        user_id=user_id,
        session_id=session_id,
        analytics_anon_id=anon_id,
        role=role,
        ts_raw=ts_raw,
        signature=sig,
    ):
        return RequestContext(
            user_id=user_id,
            session_id=session_id or None,
            analytics_anon_id=anon_id or None,
            role=role,
            trace_id=trace_id,
            feature_key=feature_key,
        )

    jwks_client = getattr(request.app.state, "jwks_client", None)
    auth_header = request.headers.get("Authorization", "")
    if jwks_client and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            claims = await jwks_client.verify_token(token)
            return RequestContext(
                user_id=str(claims.get("sub")),
                session_id=claims.get("sid"),
                analytics_anon_id=claims.get("anon_id"),
                role=claims.get("role", "user"),
                trace_id=trace_id,
                feature_key=feature_key,
            )
        except Exception:
            pass

    return RequestContext(trace_id=trace_id, feature_key=feature_key)


async def require_user(request: Request) -> RequestContext:
    """FastAPI dependency requiring an authenticated user."""
    ctx = await optional_user(request)
    if not ctx.is_authenticated:
        raise UnauthorizedError("Valid authenticated session is required.")
    return ctx


async def require_internal_service(request: Request) -> RequestContext:
    """FastAPI dependency ensuring request originated from a trusted internal service."""
    trace_id, _ = get_current_trace_context()
    feature_key = get_current_feature_key() or request.headers.get("X-Feature-Key")
    settings = getattr(request.app.state, "settings", None)
    secret = settings.internal_hmac_secret if settings else ""
    caller = request.headers.get("X-Internal-Service")
    sig = request.headers.get("X-Internal-Sig")
    if not caller or not sig or not secret:
        raise UnauthorizedError("Missing internal service authentication.")
    expected = hmac.new(secret.encode("utf-8"), caller.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise UnauthorizedError("Invalid internal service signature.")
    return RequestContext(
        user_id=request.headers.get("X-User-Id"),
        role="internal",
        is_internal=True,
        trace_id=trace_id,
        feature_key=feature_key,
    )


async def require_admin(request: Request) -> RequestContext:
    """FastAPI dependency requiring either an authenticated admin user or valid internal HMAC."""
    try:
        return await require_internal_service(request)
    except UnauthorizedError:
        pass
    ctx = await require_user(request)
    if (ctx.role or "").lower() != "admin":
        raise ForbiddenError("Administrator privileges required.")
    return ctx
