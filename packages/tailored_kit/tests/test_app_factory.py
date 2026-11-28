import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from tailored_kit.app_factory import create_service_app
from tailored_kit.auth.context import RequestContext
from tailored_kit.auth.dependencies import require_admin, require_internal_service, require_user
from tailored_kit.auth.jwks_client import sign_identity_headers
from tailored_kit.config import ServiceSettings
from tailored_kit.errors import InsufficientCreditsError
from tailored_kit.http_client.internal import InternalHttpClient
from tailored_kit.llm import LangfuseClient, LlmClient


def test_app_factory_health_and_rfc7807_and_hmac_auth():
    settings = ServiceSettings(
        service_name="billing-test",
        otel_enabled=False,
        internal_hmac_secret="unit-test-secret",
    )
    app = create_service_app(settings)

    @app.get("/protected")
    async def protected(ctx: RequestContext = Depends(require_user)):
        return {"user_id": ctx.user_id, "anon_id": ctx.analytics_anon_id}

    @app.get("/internal-ping")
    async def internal_ping(ctx: RequestContext = Depends(require_internal_service)):
        return {"internal": ctx.is_internal}

    @app.get("/admin-only")
    async def admin_only(ctx: RequestContext = Depends(require_admin)):
        return {"role": ctx.role}

    @app.get("/no-credits")
    async def no_credits():
        raise InsufficientCreditsError("Need 1 credit", metadata={"required_credits": 1})

    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"

    assert client.get("/protected").status_code == 401

    headers = sign_identity_headers(
        secret="unit-test-secret",
        user_id="user-001",
        session_id="sess-1",
        analytics_anon_id="anon-99",
    )
    r_ok = client.get("/protected", headers=headers)
    assert r_ok.status_code == 200
    assert r_ok.json() == {"user_id": "user-001", "anon_id": "anon-99"}

    # Tampered header rejected
    bad_headers = dict(headers)
    bad_headers["X-User-Id"] = "user-999"
    assert client.get("/protected", headers=bad_headers).status_code == 401

    # Internal HMAC header verification
    internal_client = InternalHttpClient(caller_service="documents-service", hmac_secret="unit-test-secret")
    internal_headers = internal_client._build_headers()
    assert client.get("/internal-ping", headers=internal_headers).status_code == 200

    # RFC 7807 error shape
    err_resp = client.get("/no-credits", headers={"X-Feature-Key": "studio.cv.tailor"})
    assert err_resp.status_code == 402
    body = err_resp.json()
    assert body["error_code"] == "INSUFFICIENT_CREDITS"
    assert body["feature_key"] == "studio.cv.tailor"
    assert body["metadata"]["required_credits"] == 1

    # Admin RBAC check: regular user blocked with 403, admin user & internal HMAC allowed
    assert client.get("/admin-only").status_code == 401
    assert client.get("/admin-only", headers=headers).status_code == 403
    admin_headers = sign_identity_headers(
        secret="unit-test-secret",
        user_id="admin-001",
        role="admin",
    )
    assert client.get("/admin-only", headers=admin_headers).status_code == 200
    assert client.get("/admin-only", headers=internal_headers).status_code == 200

    # Prometheus /metrics endpoint active
    m_resp = client.get("/metrics")
    assert m_resp.status_code == 200
    assert "tailored_http_requests_total" in m_resp.text


@pytest.mark.asyncio
async def test_llm_and_langfuse_unconfigured_fallback():
    llm = LlmClient(gemini_api_key="", openai_api_key="")
    assert llm.is_configured is False
    assert await llm.generate_text("sys", "user") is None
    assert await llm.embed_text("Senior Python Engineer") is None

    lf = LangfuseClient(host="", public_key="", secret_key="")
    assert lf.is_configured is False
    await lf.record_trace("tr-1", "coach.turn", "u-1", {"prompt": "hi"}, {"text": "ok"})
    await lf.record_score("tr-1", "proposal_resolution", 1.0, "applied")
