import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from app.config import Settings


COOKIE_NAME = "perpetum_session"


class AuthManager:
    def __init__(self, config: Settings):
        self.username = config.auth_username
        self.password = config.auth_password
        self.secret = config.auth_secret.encode("utf-8")
        self.session_seconds = config.auth_session_hours * 3600

    @property
    def configured(self) -> bool:
        return bool(self.username and self.password and len(self.secret) >= 32)

    def authenticate(self, username: str, password: str) -> bool:
        if not self.configured:
            return False
        return hmac.compare_digest(
            username.encode("utf-8"), self.username.encode("utf-8")
        ) and hmac.compare_digest(
            password.encode("utf-8"), self.password.encode("utf-8")
        )

    def create_session(self, username: str) -> str:
        payload = json.dumps(
            {"sub": username, "exp": int(time.time()) + self.session_seconds},
            separators=(",", ":"),
        ).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.new(self.secret, encoded, hashlib.sha256).digest()
        return (encoded + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()

    def verify_session(self, token: Optional[str]) -> Optional[str]:
        if not token or not self.configured:
            return None
        try:
            encoded, encoded_signature = token.encode().split(b".", 1)
            signature = base64.urlsafe_b64decode(encoded_signature + b"=" * (-len(encoded_signature) % 4))
            expected = hmac.new(self.secret, encoded, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                return None
            payload_bytes = base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4))
            payload = json.loads(payload_bytes)
            if payload.get("exp", 0) < time.time():
                return None
            username = payload.get("sub")
            return username if username == self.username else None
        except (ValueError, TypeError, json.JSONDecodeError):
            return None
