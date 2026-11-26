import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from tailored_kit.app_factory import create_service_app
from tailored_kit.audit.decorator import audit_feature
from tailored_kit.audit.hashing import hash_actor, hash_payload
from tailored_kit.config import ServiceSettings
from tailored_kit.errors import NotFoundError


def test_hashing_determinism_and_salt():
    h1 = hash_payload({"b": 2, "a": 1})
    h2 = hash_payload({"a": 1, "b": 2})
    assert h1 == h2
    assert len(h1) == 64

    a1 = hash_actor("user-123", "salt-a")
    a2 = hash_actor("user-123", "salt-b")
    assert a1 != a2
    assert hash_actor(None, "salt-a").startswith("anonymous")


def test_audit_feature_decorator_captures_success_and_failure():
    emitted = []
    settings = ServiceSettings(service_name="audit-test-svc", otel_enabled=False)
    app = create_service_app(settings)

    async def fake_emitter(env):
        emitted.append(env)

    app.state.audit_emitter = fake_emitter

    @app.post("/ok")
    @audit_feature(feature_key="studio.cv.tailor", resource_type="cv", credit_delta=-1)
    async def ok_endpoint(request: Request):
        return {"doc_id": "doc_999"}

    @app.post("/fail")
    @audit_feature(feature_key="studio.cv.tailor", resource_type="cv")
    async def fail_endpoint(request: Request):
        raise NotFoundError("Missing job")

    client = TestClient(app)
    r_ok = client.post("/ok", headers={"X-User-Id": "user-42"})
    assert r_ok.status_code == 200
    assert "X-Trace-Id" in r_ok.headers

    r_fail = client.post("/fail", headers={"X-User-Id": "user-42"})
    assert r_fail.status_code == 404
    assert r_fail.json()["error_code"] == "NOT_FOUND"
    assert r_fail.json()["feature_key"] == "studio.cv.tailor"

    assert len(emitted) == 2
    assert emitted[0].payload["outcome"] == "success"
    assert emitted[0].payload["resource_id"] == "doc_999"
    assert emitted[0].payload["credit_delta"] == -1
    assert emitted[1].payload["outcome"] == "failed"
    assert emitted[1].payload["error_code"] == "NOT_FOUND"
