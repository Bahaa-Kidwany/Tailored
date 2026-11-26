from __future__ import annotations

import functools
import inspect
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import Request

from tailored_kit.audit.hashing import hash_actor, hash_payload
from tailored_kit.feature_context import (
    get_current_feature_key,
    reset_feature_key,
    set_current_feature_key,
)
from tailored_kit.messaging_redpanda.envelope import ActorContext, EventEnvelope
from tailored_kit.telemetry_otel.setup import get_current_trace_context

logger = logging.getLogger(__name__)

AuditPublisher = Callable[[EventEnvelope], Awaitable[None]]


def _find_request(args: tuple[Any, ...], kwargs: Dict[str, Any]) -> Optional[Request]:
    for v in list(kwargs.values()) + list(args):
        if isinstance(v, Request):
            return v
    return None


def audit_feature(
    *,
    feature_key: str,
    resource_type: str = "generic",
    action: str = "execute",
    credit_delta: int = 0,
):
    """
    Decorator emitting an immutable Feature Audit event (`audit.feature.executed`)
    onto `audit.trail.v1` with trace_id, duration_ms, outcome, and structural hashes.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = set_current_feature_key(feature_key)
            started = time.perf_counter()
            request = _find_request(args, kwargs)
            if request is not None:
                request.state.feature_key = feature_key
            outcome = "success"
            error_code = ""
            result: Any = None

            payload_arg = kwargs.get("payload") or kwargs.get("body")
            before_hash = hash_payload(payload_arg)
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as exc:
                outcome = "failed"
                error_code = getattr(exc, "error_code", type(exc).__name__)
                raise
            finally:
                duration_ms = int((time.perf_counter() - started) * 1000)
                await _emit_audit(
                    request=request,
                    feature_key=get_current_feature_key() or feature_key,
                    resource_type=resource_type,
                    action=action,
                    outcome=outcome,
                    error_code=error_code,
                    before_hash=before_hash,
                    after_hash=hash_payload(result) if outcome == "success" else ("0" * 64),
                    credit_delta=credit_delta,
                    duration_ms=duration_ms,
                    result=result,
                )
                reset_feature_key(token)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper

    return decorator


async def _emit_audit(
    *,
    request: Optional[Request],
    feature_key: str,
    resource_type: str,
    action: str,
    outcome: str,
    error_code: str,
    before_hash: str,
    after_hash: str,
    credit_delta: int,
    duration_ms: int,
    result: Any,
) -> None:
    trace_id, span_id = get_current_trace_context()
    settings = getattr(request.app.state, "settings", None) if request else None
    service_name = settings.service_name if settings else "tailored-service"
    salt = settings.audit_actor_salt if settings else ""

    user_id = request.headers.get("X-User-Id") if request else None
    anon_id = request.headers.get("X-Analytics-Anon-Id") if request else None
    resource_id = ""
    if isinstance(result, dict):
        resource_id = str(result.get("id") or result.get("doc_id") or result.get("resource_id") or "")
    elif hasattr(result, "id"):
        resource_id = str(getattr(result, "id"))

    envelope = EventEnvelope(
        event_type="audit.feature.executed",
        producer_service=service_name,
        trace_id=trace_id,
        span_id=span_id,
        feature_key=feature_key,
        actor=ActorContext(user_id=user_id, analytics_anon_id=anon_id),
        payload={
            "service_name": service_name,
            "feature_key": feature_key,
            "action": action,
            "outcome": outcome,
            "actor_user_id_hash": hash_actor(user_id, salt),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "before_hash": before_hash,
            "after_hash": after_hash,
            "diff_summary": "{}",
            "credit_delta": credit_delta,
            "duration_ms": duration_ms,
            "active_flags_json": "{}",
            "error_code": error_code,
        },
    )

    emitter: Optional[AuditPublisher] = getattr(request.app.state, "audit_emitter", None) if request else None
    if emitter is not None:
        try:
            await emitter(envelope)
            return
        except Exception as exc:
            logger.warning("Custom audit_emitter failed (%s)", exc)

    producer = getattr(request.app.state, "redpanda_producer", None) if request else None
    if producer is not None and producer.is_ready:
        try:
            await producer.publish("audit.trail.v1", envelope, partition_key=feature_key)
        except Exception as exc:
            logger.warning("Redpanda audit publish failed (%s)", exc)
