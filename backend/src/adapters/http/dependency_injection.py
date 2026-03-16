"""FastAPI dependency injection — wires infrastructure to use cases."""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.auth_port import AuthContext
from src.application.use_cases.create_draft import CreateDraftUseCase
from src.application.use_cases.get_page import GetPageUseCase
from src.application.use_cases.get_version_status import GetVersionStatusUseCase
from src.application.use_cases.merge_page import MergePageUseCase
from src.application.use_cases.publish_page import PublishPageUseCase
from src.application.use_cases.rollback_page import RollbackPageUseCase
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.page_repository_impl import (
    PageRepositoryImpl,
)
from src.infrastructure.persistence.sqlalchemy.account_repository_impl import (
    AccountRepositoryImpl,
)
from src.infrastructure.persistence.sqlalchemy.tenant_context import (
    enable_tenant_filter,
)
from src.application.use_cases.account.signup import SignupUseCase
from src.application.use_cases.account.login import LoginUseCase
from src.application.use_cases.account.create_project import CreateProjectUseCase
from src.application.use_cases.account.create_app import CreateAppUseCase
from src.infrastructure.persistence.database_provisioning import (
    SqlAlchemyDatabaseProvisioner,
)
import src.infrastructure.persistence.sqlalchemy.tax_models  # noqa: F401  — register tables
import src.infrastructure.persistence.sqlalchemy.fiscal_catalog_models  # noqa: F401
import src.infrastructure.persistence.sqlalchemy.agent_models  # noqa: F401
import src.infrastructure.persistence.sqlalchemy.account_models  # noqa: F401  — platform mgmt
import src.infrastructure.persistence.sqlalchemy.api_token_model  # noqa: F401  — api tokens
import src.application.agent.skills.fetch_by_ean  # noqa: F401  — auto-register
import src.application.agent.skills.web_search  # noqa: F401  — auto-register
import src.application.agent.skills.classify_ncm  # noqa: F401  — auto-register
import src.application.agent.skills.create_entity  # noqa: F401  — auto-register
import src.application.agent.skills.list_entities  # noqa: F401  — auto-register
import src.application.agent.skills.update_entity  # noqa: F401  — auto-register
import src.application.agent.skills.delete_entity  # noqa: F401  — auto-register
import src.application.agent.skills.alter_page_schema  # noqa: F401  — auto-register
import src.application.agent.skills.publish_page_version  # noqa: F401  — auto-register
import src.application.agent.skills.rollback_page_version  # noqa: F401  — auto-register
import src.application.agent.skills.get_entity_schema  # noqa: F401  — auto-register
from src.infrastructure.security.jwt_auth_adapter import JWTAuthAdapter

# ── Database engine & session ────────────────────────────────────────

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Register automatic tenant filtering on every Session from this factory
enable_tenant_filter(SessionLocal)

security_scheme = HTTPBearer(auto_error=False)
auth_adapter = JWTAuthAdapter()


def get_db() -> Generator[Session, None, None]:
    """Provide a DB session WITHOUT tenant context.

    Use this for operations that don't need tenant isolation:
    login, seed, admin, schema resolution.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth dependency ──────────────────────────────────────────────────

def _resolve_api_key_context(db: Session) -> AuthContext:
    """Resolve admin AuthContext from the first admin user in the DB.

    Used when a valid X-API-Key header is provided instead of a JWT.
    """
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.models import UserModel

    user = db.execute(
        select(UserModel).where(UserModel.role == "admin").limit(1)
    ).scalar_one_or_none()

    if user:
        return AuthContext(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            username=user.username,
            role="admin",
        )
    return AuthContext(
        user_id="api-key-admin",
        tenant_id="00000000-0000-0000-0000-000000000001",
        username="api-key-admin",
        role="admin",
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolve the current user from a JWT Bearer token, API token header, or Bearer API token.

    Priority:
    0. MCP context — if the request comes from an MCP tool call,
       the middleware already authenticated and stored the context in contextvars.
    1. X-API-Key header — looked up in the api_tokens table by SHA-256 hash.
       On match, resolves to the token owner's AuthContext.
    2. ?api_key= query parameter — same lookup as X-API-Key.
    3. Authorization: Bearer <value> — if it doesn't decode as a valid JWT,
       also tried as an API token via the same hash lookup.
    4. Authorization: Bearer <jwt> — standard JWT app authentication.
    """
    # 0. MCP context (propagated from MCP middleware via contextvars)
    from src.adapters.mcp.mcp_server import mcp_auth_context
    mcp_ctx = mcp_auth_context.get(None)
    if mcp_ctx is not None:
        return mcp_ctx

    import hashlib
    from datetime import datetime, timezone
    from sqlalchemy import select
    from src.infrastructure.persistence.sqlalchemy.api_token_model import ApiTokenModel
    from src.infrastructure.persistence.sqlalchemy.models import UserModel

    def _lookup_token(raw: str) -> AuthContext | None:
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        record = db.execute(
            select(ApiTokenModel).where(
                ApiTokenModel.token_hash == token_hash,
                ApiTokenModel.is_active == True,  # noqa: E712
            )
        ).scalar_one_or_none()
        if not record:
            return None
        user = db.execute(
            select(UserModel).where(UserModel.id == record.user_id)
        ).scalar_one_or_none()
        if not user:
            return None
        # Update last_used_at without affecting the outer transaction
        record.last_used_at = datetime.now(timezone.utc)
        db.flush()
        return AuthContext(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            username=user.username,
            role=user.role,
        )

    # 1. X-API-Key header (ChatGPT Actions sends as custom header)
    api_key_header = request.headers.get("X-API-Key", "")
    if api_key_header:
        ctx = _lookup_token(api_key_header)
        if ctx:
            return ctx

    # 2. ?api_key= query parameter (Claude Web MCP connector)
    api_key_param = request.query_params.get("api_key", "")
    if api_key_param:
        ctx = _lookup_token(api_key_param)
        if ctx:
            return ctx

    # 3. Bearer token — try as API token first, then as JWT
    if credentials is not None:
        ctx = _lookup_token(credentials.credentials)
        if ctx:
            return ctx
        # Fall through to JWT verification
        jwt_ctx = auth_adapter.verify_token(credentials.credentials)
        if jwt_ctx:
            return jwt_ctx

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: provide a valid Bearer token or X-API-Key header",
    )


def require_role(*roles: str):
    """Dependência reutilizável para proteger endpoints por role.

    Uso: auth: AuthContext = Depends(require_role("admin"))
    """
    def _check(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if auth.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão insuficiente. Role necessário: {', '.join(roles)}",
            )
        return auth
    return _check


# ── Tenant-aware DB session ──────────────────────────────────────────

def get_tenant_db(
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Session:
    """Provide a DB session WITH tenant context.

    Sets ``session.info["tenant_id"]`` so that the automatic
    tenant filter injects WHERE clauses on every query.
    The tenant_id is also accessible via ``db.info["tenant_id"]``
    from the router when needed (e.g. for INSERT operations).
    """
    db.info["tenant_id"] = auth.tenant_id
    return db


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


def get_version_status_use_case(db: Session = Depends(get_db)) -> GetVersionStatusUseCase:
    return GetVersionStatusUseCase(PageRepositoryImpl(db))


# ── Account use case factories ───────────────────────────────────────

def get_account_repo(db: Session = Depends(get_db)) -> AccountRepositoryImpl:
    return AccountRepositoryImpl(db)


def get_signup_use_case(
    db: Session = Depends(get_db),
) -> SignupUseCase:
    return SignupUseCase(
        repo=AccountRepositoryImpl(db),
        auth=auth_adapter,
    )


def get_login_use_case(
    db: Session = Depends(get_db),
) -> LoginUseCase:
    return LoginUseCase(
        repo=AccountRepositoryImpl(db),
        auth=auth_adapter,
    )


def get_create_project_use_case(
    db: Session = Depends(get_db),
) -> CreateProjectUseCase:
    return CreateProjectUseCase(repo=AccountRepositoryImpl(db))


def get_create_app_use_case(
    db: Session = Depends(get_db),
) -> CreateAppUseCase:
    return CreateAppUseCase(
        repo=AccountRepositoryImpl(db),
        provisioner=SqlAlchemyDatabaseProvisioner(db),
    )

