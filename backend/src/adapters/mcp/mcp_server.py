"""FastMCP server — mounted inside the existing FastAPI application.

Exposes ERP tools to Claude Desktop/Web via Streamable HTTP at /mcp.
Authentication supports X-MCP-Api-Key header (legacy), X-API-Key header,
and ?api_key= query parameter (for Claude Web).

When a valid token is found, the auth context is propagated via
contextvars so that internal tool calls (made by fastapi-mcp) can
inherit the authenticated identity without needing separate auth.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Context variable to propagate MCP auth to internal tool calls
mcp_auth_context: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "mcp_auth_context", default=None
)


def create_mcp_server(get_db: Any) -> FastMCP:
    """Instantiate and configure the FastMCP server.

    Args:
        get_db: A callable that yields a SQLAlchemy Session (same factory
                used by the FastAPI dependency injection layer).

    Returns:
        A configured FastMCP instance ready to be mounted in FastAPI.
    """
    if not settings.mcp_api_key:
        logger.warning(
            "ERP_MCP_API_KEY is not set — MCP server will reject all requests"
        )

    mcp = FastMCP(
        name="AutoSystem ERP",
        instructions=(
            "Você tem acesso ao ERP AutoSystem. "
            "Use list_entity_types para descobrir as entidades disponíveis. "
            "Use get_project_info para entender o contexto do projeto atual. "
            "Todas as operações de escrita requerem confirmação explícita do usuário."
        ),
    )

    # Rotas do FastAPI já cuidam das ferramentas MCP. Nenhuma ação extra necessária.
    from src.adapters.mcp.tools.account_tools import register_account_tools

    register_account_tools(mcp, get_db)

    logger.info("FastMCP server configured successfully")
    return mcp

def build_api_key_middleware(app: FastAPI) -> None:
    """Add a middleware to validate API keys on all /mcp/* requests.

    Accepts authentication via:
    1. X-MCP-Api-Key header (legacy — compared to ERP_MCP_API_KEY env var)
    2. X-API-Key header (API tokens from the settings page)
    3. ?api_key= query parameter (Claude Web MCP connector)

    On success, stores an AuthContext in contextvars so that internal
    tool calls from fastapi-mcp can inherit the identity.
    """
    import hashlib
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.types import ASGIApp, Receive, Scope, Send

    from src.adapters.mcp.mcp_auth import validate_api_key
    from src.infrastructure.persistence.sqlalchemy.api_token_model import ApiTokenModel

    class MCPAuthASGIMiddleware:
        def __init__(self, app: ASGIApp):
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if scope["type"] != "http" or not scope.get("path", "").startswith("/mcp"):
                return await self.app(scope, receive, send)

            request = Request(scope, receive=receive, send=send)
            
            # fastmcp uses /mcp/messages/?session_id=... for POST requests.
            # Claude Web does not forward the API key initialized in the SSE connection.
            # By allowing POST /mcp/messages/ to pass, we rely on fastmcp's internal session validation.
            path = scope.get("path", "")
            if request.method == "POST" and path.startswith("/mcp/messages"):
                return await self.app(scope, receive, send)

            # 1. Legacy X-MCP-Api-Key header
            legacy_key = request.headers.get("X-MCP-Api-Key", "")
            if legacy_key and validate_api_key(legacy_key):
                from src.adapters.mcp.mcp_auth import get_admin_context
                from src.adapters.http.dependency_injection import SessionLocal
                db = SessionLocal()
                try:
                    ctx = get_admin_context(db)
                    mcp_auth_context.set(ctx)
                finally:
                    db.close()
                return await self.app(scope, receive, send)

            # 2. X-API-Key header or ?api_key= query param (user API tokens)
            raw_token = (
                request.headers.get("X-API-Key", "")
                or request.query_params.get("api_key", "")
            )
            if raw_token:
                from src.adapters.http.dependency_injection import SessionLocal
                from src.infrastructure.persistence.sqlalchemy.models import UserModel
                db = SessionLocal()
                try:
                    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                    from sqlalchemy import select
                    record = db.execute(
                        select(ApiTokenModel).where(
                            ApiTokenModel.token_hash == token_hash,
                            ApiTokenModel.is_active == True,  # noqa: E712
                        )
                    ).scalar_one_or_none()
                    if record:
                        from datetime import datetime, timezone
                        from src.application.ports.auth_port import AuthContext
                        record.last_used_at = datetime.now(timezone.utc)
                        user = db.execute(
                            select(UserModel).where(UserModel.id == record.user_id)
                        ).scalar_one_or_none()
                        if user:
                            ctx = AuthContext(
                                user_id=str(user.id),
                                tenant_id=str(user.tenant_id),
                                username=user.username,
                                role=user.role,
                            )
                        else:
                            ctx = AuthContext(
                                user_id=str(record.user_id),
                                tenant_id=str(record.tenant_id),
                                username="api-token",
                                role="admin",
                            )
                        mcp_auth_context.set(ctx)
                        db.commit()
                        return await self.app(scope, receive, send)
                finally:
                    db.close()

            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid or missing API key. Use X-API-Key header or ?api_key= query parameter."},
            )
            await response(scope, receive, send)

    app.add_middleware(MCPAuthASGIMiddleware)
