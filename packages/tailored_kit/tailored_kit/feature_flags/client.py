import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeatureFlagClient:
    """OpenFeature-compatible feature flag evaluator backed by Redis ff:catalog and in-memory TTL cache."""

    def __init__(
        self,
        *,
        redis_client: Any = None,
        catalog_key: str = "ff:catalog",
        cache_ttl_seconds: float = 30.0,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.redis_client = redis_client
        self.catalog_key = catalog_key
        self.cache_ttl_seconds = cache_ttl_seconds
        self._defaults = defaults or {}
        self._cached_catalog: Dict[str, Any] = {}
        self._cached_at: float = 0.0

    def set_local_catalog(self, catalog: Dict[str, Any]) -> None:
        self._cached_catalog = dict(catalog)
        self._cached_at = time.monotonic()

    async def get_catalog(self) -> Dict[str, Any]:
        now = time.monotonic()
        if self._cached_catalog and (now - self._cached_at) < self.cache_ttl_seconds:
            return self._cached_catalog

        if self.redis_client is not None:
            try:
                raw = await self.redis_client.get(self.catalog_key)
                if raw:
                    data = json.loads(raw)
                    self._cached_catalog = data
                    self._cached_at = now
                    return data
            except Exception as exc:
                logger.warning("FeatureFlagClient Redis lookup failed (%s); using fallback", exc)

        return self._cached_catalog or self._defaults

    async def is_enabled(
        self,
        flag_key: str,
        *,
        user_id: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        catalog = await self.get_catalog()
        flag = catalog.get(flag_key)
        if flag is None:
            return default
        if isinstance(flag, bool):
            return flag

        overrides = flag.get("overrides") or {}
        if user_id and user_id in overrides:
            return bool(overrides[user_id])

        if not flag.get("enabled", False):
            return False

        rollout_pct = int(flag.get("rollout_percent", 100))
        if rollout_pct >= 100:
            return True
        if rollout_pct <= 0 or not user_id:
            return rollout_pct >= 100

        bucket = self._stable_bucket(flag_key, user_id)
        return bucket < rollout_pct

    @staticmethod
    def _stable_bucket(flag_key: str, user_id: str) -> int:
        digest = hashlib.sha256(f"{flag_key}:{user_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 100
