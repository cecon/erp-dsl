"""Database seed script — creates initial tenant, admin, and page schemas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.seed_schemas import (
    DASHBOARD_SCHEMA,
    HEADER_SCHEMA,
    PRODUCTS_PAGE_SCHEMA,
    SIDEBAR_SCHEMA,
)
from src.infrastructure.persistence.seed_schemas_fiscal import (
    FISCAL_RULES_PAGE_SCHEMA,
    FISCAL_RULES_FORM_SCHEMA,
    OPERATION_NATURES_PAGE_SCHEMA,
    OPERATION_NATURES_FORM_SCHEMA,
    TAX_GROUPS_PAGE_SCHEMA,
    TAX_GROUPS_FORM_SCHEMA,
    THEME_CONFIG_SCHEMA,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    PageVersionModel,
    TenantModel,
    UserModel,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000002"

SEED_PAGES = [
    ("products", PRODUCTS_PAGE_SCHEMA),
    ("tax_groups", TAX_GROUPS_PAGE_SCHEMA),
    ("tax_groups_form", TAX_GROUPS_FORM_SCHEMA),
    ("operation_natures", OPERATION_NATURES_PAGE_SCHEMA),
    ("operation_natures_form", OPERATION_NATURES_FORM_SCHEMA),
    ("fiscal_rules", FISCAL_RULES_PAGE_SCHEMA),
    ("fiscal_rules_form", FISCAL_RULES_FORM_SCHEMA),
    ("_sidebar", SIDEBAR_SCHEMA),
    ("_header", HEADER_SCHEMA),
    ("dashboard", DASHBOARD_SCHEMA),
    ("_theme_config", THEME_CONFIG_SCHEMA),
]


def _seed_page(session: Session, page_key: str, schema: dict) -> None:
    """Create or update a published page version."""
    stmt = select(PageVersionModel).where(
        PageVersionModel.page_key == page_key,
        PageVersionModel.scope == "global",
        PageVersionModel.status == "published",
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        # Upsert: update schema_json if it changed
        if existing.schema_json != schema:
            existing.schema_json = schema
            session.commit()
        return

    page = PageVersionModel(
        id=str(uuid.uuid4()),
        page_key=page_key,
        scope="global",
        tenant_id=None,
        base_version_id=None,
        version_number=1,
        schema_json=schema,
        status="published",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(page)


def seed_database(session: Session) -> None:
    """Idempotent seed: only creates records if they don't exist."""

    # 1. Default tenant
    existing_tenant = session.get(TenantModel, DEFAULT_TENANT_ID)
    if not existing_tenant:
        tenant = TenantModel(
            id=DEFAULT_TENANT_ID,
            name="Default Tenant",
            slug="default",
            created_at=datetime.now(timezone.utc),
        )
        session.add(tenant)

    # 2. Admin user
    stmt = select(UserModel).where(UserModel.username == "admin")
    existing_user = session.execute(stmt).scalar_one_or_none()
    if not existing_user:
        admin = UserModel(
            id=ADMIN_USER_ID,
            tenant_id=DEFAULT_TENANT_ID,
            username="admin",
            password_hash=pwd_context.hash("admin"),
            role="admin",
            created_at=datetime.now(timezone.utc),
        )
        session.add(admin)

    # 3. Seed all page schemas
    for page_key, schema in SEED_PAGES:
        _seed_page(session, page_key, schema)

    session.commit()
