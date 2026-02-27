"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.http.error_handlers import register_error_handlers
from src.adapters.http.routers import (
    agent_router,
    auth_router,
    generic_crud_router,
    pages_router,
)
from src.infrastructure.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup / shutdown hooks.

    Table creation and migrations are handled by Alembic in start.py.
    """
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
        prefix="/api/agent",
        tags=["Agent"],
    )

    # Standardized error handling
    register_error_handlers(app)

    return app

app = create_app()

