"""Application port for authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class AuthContext:
    """Immutable context extracted from a validated auth token."""

    user_id: str
    tenant_id: str
    username: str
    role: str = "user"


class AuthPort(Protocol):
    """Port defining authentication behaviour."""

    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        username: str,
        role: str = "user",
    ) -> str:
        """Create a signed JWT token."""
        ...

    def verify_token(self, token: str) -> Optional[AuthContext]:
        """Verify and decode a JWT token, returning AuthContext or None."""
        ...
