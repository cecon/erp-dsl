"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.http.routers import (
    auth_router,
    generic_crud_router,
    pages_router,
)
from src.infrastructure.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup / shutdown hooks."""
    # Startup: ensure tables exist (dev convenience; use Alembic in prod)
    from src.adapters.http.dependency_injection import engine
    from src.infrastructure.persistence.sqlalchemy.models import Base
    # Import tax_models so their tables are registered with Base.metadata
    import src.infrastructure.persistence.sqlalchemy.tax_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
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
    app.include_router(
        generic_crud_router.router,
        prefix="/entities",
        tags=["Generic CRUD"],
    )

    return app


app = create_app()

