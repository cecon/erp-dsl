"""FastMCP server — mounted inside the existing FastAPI application.

Exposes ERP tools to Claude Desktop via SSE transport at /mcp.
Authentication is done via X-MCP-Api-Key header validated against
the ERP_MCP_API_KEY environment variable, after which all tool calls
execute under the project admin's tenant context.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from mcp.server.fastmcp import FastMCP

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


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

    # Register tool groups
    from src.adapters.mcp.tools.entities_tools import register_entity_tools
    from src.adapters.mcp.tools.pages_tools import register_page_tools
    from src.adapters.mcp.tools.account_tools import register_account_tools

    register_entity_tools(mcp, get_db)
    register_page_tools(mcp, get_db)
    register_account_tools(mcp, get_db)

    logger.info("FastMCP server configured successfully")
    return mcp


def build_api_key_middleware(app: FastAPI) -> None:
    """Add a middleware to validate X-MCP-Api-Key on all /mcp/* requests."""

    from src.adapters.mcp.mcp_auth import validate_api_key

    @app.middleware("http")
    async def mcp_auth_middleware(request: Request, call_next: Any) -> Any:
        if request.url.path.startswith("/mcp"):
            api_key = request.headers.get("X-MCP-Api-Key", "")
            if not validate_api_key(api_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing X-MCP-Api-Key header",
                )
        return await call_next(request)
