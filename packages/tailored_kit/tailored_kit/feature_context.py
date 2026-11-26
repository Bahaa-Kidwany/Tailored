from contextvars import ContextVar
from typing import Optional

_feature_key_ctx: ContextVar[Optional[str]] = ContextVar("tailored_feature_key", default=None)


def get_current_feature_key() -> Optional[str]:
    return _feature_key_ctx.get()


def set_current_feature_key(value: Optional[str]):
    return _feature_key_ctx.set(value)


def reset_feature_key(token) -> None:
    _feature_key_ctx.reset(token)
