"""JWT authentication adapter implementing AuthPort."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from src.application.ports.auth_port import AuthContext
from src.infrastructure.config.settings import settings


class JWTAuthAdapter:
    """Concrete implementation of AuthPort using python-jose."""

    def __init__(
        self,
        secret: str = settings.jwt_secret,
        algorithm: str = settings.jwt_algorithm,
        expire_minutes: int = settings.jwt_expire_minutes,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        username: str,
        role: str = "user",
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._expire_minutes
        )
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_token(self, token: str) -> Optional[AuthContext]:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
            return AuthContext(
                user_id=payload["sub"],
                tenant_id=payload["tenant_id"],
                username=payload["username"],
                role=payload.get("role", "user"),
            )
        except JWTError:
            return None
