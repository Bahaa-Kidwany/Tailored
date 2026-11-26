"""Shared SDK for Tailored microservices."""

from tailored_kit.app_factory import create_service_app
from tailored_kit.audit.decorator import audit_feature
from tailored_kit.audit.hashing import hash_actor, hash_payload
from tailored_kit.audit.middleware import TraceAndFeatureMiddleware
from tailored_kit.feature_context import get_current_feature_key
from tailored_kit.auth.context import RequestContext
from tailored_kit.auth.dependencies import optional_user, require_internal_service, require_user
from tailored_kit.config import ServiceSettings
from tailored_kit.errors import (
    ConflictError,
    ForbiddenError,
    InsufficientCreditsError,
    NotFoundError,
    ProblemDetail,
    TailoredError,
    UnauthorizedError,
    register_error_handlers,
)
from tailored_kit.feature_flags.client import FeatureFlagClient
from tailored_kit.http_client.internal import InternalHttpClient
from tailored_kit.messaging_redpanda.consumer import RedpandaConsumer
from tailored_kit.messaging_redpanda.envelope import ActorContext, EventEnvelope
from tailored_kit.messaging_redpanda.producer import RedpandaProducer
from tailored_kit.outbox.model import OutboxEvent, ProcessedEvent
from tailored_kit.outbox.relay import OutboxRelay

__all__ = [
    "ActorContext",
    "ConflictError",
    "EventEnvelope",
    "FeatureFlagClient",
    "ForbiddenError",
    "InsufficientCreditsError",
    "InternalHttpClient",
    "NotFoundError",
    "OutboxEvent",
    "OutboxRelay",
    "ProblemDetail",
    "ProcessedEvent",
    "RedpandaConsumer",
    "RedpandaProducer",
    "RequestContext",
    "ServiceSettings",
    "TailoredError",
    "TraceAndFeatureMiddleware",
    "UnauthorizedError",
    "audit_feature",
    "create_service_app",
    "get_current_feature_key",
    "hash_actor",
    "hash_payload",
    "optional_user",
    "register_error_handlers",
    "require_internal_service",
    "require_user",
]
