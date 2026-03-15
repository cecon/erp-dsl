"""MCP authentication helper.

Validates the incoming MCP API Key (X-MCP-Api-Key header) and builds
an admin AuthContext that represents the project owner. The tenant_id
is resolved dynamically from the first admin user found in the database.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.ports.auth_port import AuthContext
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.models import UserModel


def validate_api_key(key: str) -> bool:
    """Return True if *key* matches the configured MCP_API_KEY."""
    configured = settings.mcp_api_key
    if not configured:
        return False
    return key == configured


def get_admin_context(db: Session) -> AuthContext:
    """Resolve the first admin user and return an admin AuthContext.

    Falls back to a synthetic admin context if no admin user exists.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.role == "admin")
        .limit(1)
    )
    user = db.execute(stmt).scalar_one_or_none()

    if user:
        return AuthContext(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            username=user.username,
            role="admin",
        )

    # Fallback — should not happen in a seeded project
    return AuthContext(
        user_id="mcp-admin",
        tenant_id="00000000-0000-0000-0000-000000000001",
        username="mcp-admin",
        role="admin",
    )
