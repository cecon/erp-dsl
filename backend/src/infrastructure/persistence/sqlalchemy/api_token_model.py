"""SQLAlchemy model for user-generated API tokens."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from src.infrastructure.persistence.sqlalchemy.models import Base


class ApiTokenModel(Base):
    """Personal access token for API/MCP authentication.

    Tokens are bound to a specific user and tenant.
    The raw token is shown once on creation and only its
    SHA-256 hash is stored.
    """

    __tablename__ = "api_tokens"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    token_hash = Column(String(256), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)
