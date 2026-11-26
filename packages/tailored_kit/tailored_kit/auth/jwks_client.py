import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import httpx
import jwt


def sign_identity_headers(
    *,
    secret: str,
    user_id: str,
    session_id: str = "",
    analytics_anon_id: str = "",
    role: str = "user",
    timestamp: Optional[int] = None,
) -> Dict[str, str]:
    """Produces HMAC-SHA256 trusted internal headers after ForwardAuth validation."""
    ts = str(timestamp or int(time.time()))
    canonical = f"{user_id}|{session_id}|{analytics_anon_id}|{role}|{ts}"
    sig = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "X-User-Id": user_id,
        "X-Session-Id": session_id,
        "X-Analytics-Anon-Id": analytics_anon_id,
        "X-User-Role": role,
        "X-Identity-Ts": ts,
        "X-Identity-Sig": sig,
    }


def verify_identity_headers(
    *,
    secret: str,
    user_id: Optional[str],
    session_id: str,
    analytics_anon_id: str,
    role: str,
    ts_raw: Optional[str],
    signature: Optional[str],
    max_skew_seconds: int = 300,
) -> bool:
    """Verifies gateway/auth HMAC signature and prevents replay outside max_skew_seconds."""
    if not user_id or not ts_raw or not signature:
        return False
    try:
        ts_val = int(ts_raw)
    except ValueError:
        return False
    if abs(int(time.time()) - ts_val) > max_skew_seconds:
        return False
    canonical = f"{user_id}|{session_id}|{analytics_anon_id}|{role}|{ts_raw}"
    expected = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class JWKSClient:
    """Lightweight cached JWKS fetcher for verifying RS256 Bearer JWTs."""

    def __init__(self, jwks_url: str, cache_ttl_seconds: int = 300) -> None:
        self.jwks_url = jwks_url
        self.cache_ttl_seconds = cache_ttl_seconds
        self._keys_by_kid: Dict[str, Any] = {}
        self._fetched_at: float = 0.0

    async def verify_token(self, token: str) -> Dict[str, Any]:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        await self._ensure_keys(force=kid not in self._keys_by_kid)
        jwk_data = self._keys_by_kid.get(kid)
        if not jwk_data:
            raise jwt.InvalidTokenError("Unknown JWT key id")
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_data)
        return jwt.decode(token, public_key, algorithms=["RS256"])

    async def _ensure_keys(self, force: bool = False) -> None:
        now = time.time()
        if not force and self._keys_by_kid and (now - self._fetched_at) < self.cache_ttl_seconds:
            return
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(self.jwks_url)
            resp.raise_for_status()
            jwks = resp.json()
        self._keys_by_kid = {k["kid"]: k for k in jwks.get("keys", []) if "kid" in k}
        self._fetched_at = now
