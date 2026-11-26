import hashlib
import json
from typing import Any


def hash_payload(obj: Any) -> str:
    """Produces a deterministic SHA-256 hash of a structured payload without exposing PII."""
    if obj is None:
        return "0" * 64
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump(mode="json")
    try:
        serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    except Exception:
        serialized = str(obj)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_actor(user_id: str | None, salt: str = "") -> str:
    """Computes a salted SHA-256 actor hash suitable for immutable ClickHouse audit logs."""
    if not user_id:
        return "anonymous" + ("0" * 55)
    raw = f"{user_id}:{salt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
