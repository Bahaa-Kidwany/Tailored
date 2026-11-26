import asyncio
import hashlib
import hmac
import random
from typing import Any, Dict, Optional

import httpx

from tailored_kit.feature_context import get_current_feature_key


class InternalHttpClient:
    """Async internal service-to-service HTTP client propagating traceparent, feature_key, and HMAC auth."""

    def __init__(
        self,
        *,
        caller_service: str,
        hmac_secret: str,
        timeout_seconds: float = 3.0,
        max_get_retries: int = 2,
    ) -> None:
        self.caller_service = caller_service
        self.hmac_secret = hmac_secret
        self.timeout_seconds = timeout_seconds
        self.max_get_retries = max_get_retries
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        sig = hmac.new(
            self.hmac_secret.encode("utf-8"),
            self.caller_service.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers: Dict[str, str] = {
            "X-Internal-Service": self.caller_service,
            "X-Internal-Sig": sig,
        }
        feature_key = get_current_feature_key()
        if feature_key:
            headers["X-Feature-Key"] = feature_key
        if extra:
            headers.update(extra)
        return headers

    async def get(self, url: str, *, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        merged_headers = self._build_headers(headers)
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_get_retries + 1):
            try:
                resp = await self._client.get(url, headers=merged_headers, **kwargs)
                if resp.status_code < 500 or attempt == self.max_get_retries:
                    return resp
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt == self.max_get_retries:
                    raise
            await asyncio.sleep(0.1 * (2**attempt) + random.uniform(0, 0.05))
        assert last_exc is not None
        raise last_exc

    async def post(self, url: str, *, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        return await self._client.post(url, headers=self._build_headers(headers), **kwargs)

    async def patch(self, url: str, *, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        return await self._client.patch(url, headers=self._build_headers(headers), **kwargs)
