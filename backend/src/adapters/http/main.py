"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.http.error_handlers import register_error_handlers
from src.adapters.http.routers import (
    account_router,
    agent_router,
    auth_router,
    discovery_router,
    forge_router,
    generic_crud_router,
    llm_router,
    otto_router,
    pages_router,
    settings_router,
    workflow_router,
)
from src.infrastructure.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup / shutdown hooks.

    Table creation and migrations are handled by Alembic in start.py.
    If MCP is enabled, also runs the session_manager lifespan.
    """
    mcp_app = getattr(app.state, "mcp_sub_app", None)
    if mcp_app is not None and hasattr(mcp_app, "router"):
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(mcp_app.router.lifespan_context(mcp_app))
            yield
    else:
        yield
    # Shutdown: nothing needed


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
    app.include_router(pages_router.router, prefix="/pages", tags=["Pages"])
    
    # Generic CRUD (covers all DSL-driven entities including fiscal_rules)
    app.include_router(
        generic_crud_router.router,
        prefix="/entities",
        tags=["Generic CRUD"],
    )

    # Agent endpoints (product enrichment)
    app.include_router(
        agent_router.router,
        prefix="/agent",
        tags=["Agent"],
    )

    # Otto universal chat
    app.include_router(
        otto_router.router,
        prefix="/otto",
        tags=["Otto"],
    )

    # Forge — autonomous coding agent
    app.include_router(
        forge_router.router,
        prefix="/forge",
        tags=["Forge"],
    )

    # LLM utility endpoints (model listing)
    app.include_router(
        llm_router.router,
        prefix="/llm",
        tags=["LLM"],
    )

    # Workflows
    app.include_router(
        workflow_router.router,
        prefix="/workflows",
        tags=["Workflows"],
    )

    # Account / Platform management
    app.include_router(
        account_router.router,
        prefix="/api/accounts",
        tags=["Accounts"],
    )

    # User settings (API tokens)
    app.include_router(
        settings_router.router,
        prefix="/settings",
        tags=["Settings"],
    )

    # Standardized error handling
    register_error_handlers(app)

    # Discovery / introspection endpoints
    app.include_router(
        discovery_router.router,
        prefix="/discovery",
        tags=["Discovery"],
    )

    # MCP Server — only mounted when ERP_MCP_API_KEY is configured
    if settings.mcp_api_key:
        from src.adapters.mcp.mcp_server import create_mcp_server, build_api_key_middleware
        from src.adapters.http.dependency_injection import get_db

        # Auth middleware must be registered before mounting (middleware runs in reverse)
        build_api_key_middleware(app)

        # Mount MCP server — Streamable HTTP transport (MCP SDK >= 1.6)
        # streamable_http_app() expõe a rota /mcp internamente.
        # Montamos na raiz (path vazio) para que /mcp chegue diretamente ao sub-app.
        # O lifespan do sub-app é composto no lifespan do FastAPI via app.state.mcp_sub_app.
        mcp = create_mcp_server(get_db)
        mcp_sub_app = mcp.streamable_http_app()
        app.state.mcp_sub_app = mcp_sub_app
        app.mount("", mcp_sub_app)
    else:
        import logging
        logging.getLogger(__name__).info(
            "MCP server disabled — set ERP_MCP_API_KEY to enable"
        )

    return app

app = create_app()

