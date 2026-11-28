import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-SHA256 with a 16-byte random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256$200000${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    try:
        _, iters_s, salt, hex_digest = stored_hash.split("$", 3)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iters_s))
        return hmac.compare_digest(dk.hex(), hex_digest)
    except Exception:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_fernet(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str, secret: str) -> bytes:
    return get_fernet(secret).encrypt(plaintext.encode("utf-8"))


def decrypt_secret(ciphertext: bytes, secret: str) -> str:
    return get_fernet(secret).decrypt(ciphertext).decode("utf-8")


class RsaKeyManager:
    """Manages RS256 signing keypair and exposes JWK public key."""

    def __init__(self, key_dir: str = "/tmp/tailored_auth_keys") -> None:
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self.priv_path = self.key_dir / "jwt_private.pem"
        self.kid = "tailored-rs256-v1"
        self._private_key = self._load_or_create()

    def _load_or_create(self):
        if self.priv_path.exists():
            pem = self.priv_path.read_bytes()
            return serialization.load_pem_private_key(pem, password=None)
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.priv_path.write_bytes(pem)
        os.chmod(self.priv_path, 0o600)
        return private_key

    def jwks(self) -> Dict[str, Any]:
        pub = self._private_key.public_key()
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(pub))
        jwk["kid"] = self.kid
        jwk["use"] = "sig"
        jwk["alg"] = "RS256"
        return {"keys": [jwk]}

    def issue_access_token(
        self,
        *,
        user_id: str,
        session_id: str,
        analytics_anon_id: str,
        email: str,
        role: str,
        email_verified: bool,
        ttl_minutes: int = 15,
    ) -> Tuple[str, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=ttl_minutes)
        payload = {
            "sub": user_id,
            "sid": session_id,
            "anon_id": analytics_anon_id,
            "email": email,
            "role": role,
            "verified": email_verified,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "iss": "tailored-auth-service",
        }
        token = jwt.encode(payload, self._private_key, algorithm="RS256", headers={"kid": self.kid})
        return token, ttl_minutes * 60

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        pub = self._private_key.public_key()
        return jwt.decode(token, pub, algorithms=["RS256"], issuer="tailored-auth-service")
