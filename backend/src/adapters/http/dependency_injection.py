"""FastAPI dependency injection — wires infrastructure to use cases."""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.auth_port import AuthContext
from src.application.use_cases.create_draft import CreateDraftUseCase
from src.application.use_cases.get_page import GetPageUseCase
from src.application.use_cases.merge_page import MergePageUseCase
from src.application.use_cases.publish_page import PublishPageUseCase
from src.application.use_cases.rollback_page import RollbackPageUseCase
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.page_repository_impl import (
    PageRepositoryImpl,
)
from src.infrastructure.security.jwt_auth_adapter import JWTAuthAdapter

# ── Database engine & session ────────────────────────────────────────

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

security_scheme = HTTPBearer()
auth_adapter = JWTAuthAdapter()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth dependency ──────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> AuthContext:
    ctx = auth_adapter.verify_token(credentials.credentials)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return ctx


# ── Page use case factories ──────────────────────────────────────────

def get_page_use_case(db: Session = Depends(get_db)) -> GetPageUseCase:
    return GetPageUseCase(PageRepositoryImpl(db))


def create_draft_use_case(db: Session = Depends(get_db)) -> CreateDraftUseCase:
    return CreateDraftUseCase(PageRepositoryImpl(db))


def publish_page_use_case(
    db: Session = Depends(get_db),
) -> PublishPageUseCase:
    return PublishPageUseCase(PageRepositoryImpl(db))


def rollback_page_use_case(
    db: Session = Depends(get_db),
) -> RollbackPageUseCase:
    return RollbackPageUseCase(PageRepositoryImpl(db))


def merge_page_use_case(db: Session = Depends(get_db)) -> MergePageUseCase:
    return MergePageUseCase(PageRepositoryImpl(db))

