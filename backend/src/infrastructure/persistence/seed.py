"""Database seed script — creates initial tenant, admin, and page schemas."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.seed_schemas import (
    DASHBOARD_SCHEMA,
    HEADER_SCHEMA,
    PRODUCTS_FORM_SCHEMA,
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
from src.infrastructure.persistence.seed_schemas_llm import (
    LLM_PROVIDERS_PAGE_SCHEMA,
    LLM_PROVIDERS_FORM_SCHEMA,
)
from src.infrastructure.persistence.seed_schemas_workflows import (
    WORKFLOWS_PAGE_SCHEMA,
    WORKFLOWS_FORM_SCHEMA,
)
from src.infrastructure.persistence.seed_schemas_skills import (
    SKILLS_PAGE_SCHEMA,
    SKILLS_FORM_SCHEMA,
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
    ("products_form", PRODUCTS_FORM_SCHEMA),
    ("tax_groups", TAX_GROUPS_PAGE_SCHEMA),
    ("tax_groups_form", TAX_GROUPS_FORM_SCHEMA),
    ("operation_natures", OPERATION_NATURES_PAGE_SCHEMA),
    ("operation_natures_form", OPERATION_NATURES_FORM_SCHEMA),
    ("fiscal_rules", FISCAL_RULES_PAGE_SCHEMA),
    ("fiscal_rules_form", FISCAL_RULES_FORM_SCHEMA),
    ("workflows", WORKFLOWS_PAGE_SCHEMA),
    ("workflows_form", WORKFLOWS_FORM_SCHEMA),
    ("skills", SKILLS_PAGE_SCHEMA),
    ("skills_form", SKILLS_FORM_SCHEMA),
    ("llm_providers", LLM_PROVIDERS_PAGE_SCHEMA),
    ("llm_providers_form", LLM_PROVIDERS_FORM_SCHEMA),
    ("_sidebar", SIDEBAR_SCHEMA),
    ("_header", HEADER_SCHEMA),
    ("dashboard", DASHBOARD_SCHEMA),
    ("_theme_config", THEME_CONFIG_SCHEMA),
]

logger = logging.getLogger(__name__)


def _schema_hash(schema: dict) -> str:
    """MD5 do JSON canônico. Usado para detectar mudanças no schema em código."""
    canonical = json.dumps(schema, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(canonical.encode()).hexdigest()


def _seed_page(session: Session, page_key: str, schema: dict) -> None:
    """Cria uma published page version SE ainda não existir.

    Não sobrescreve versões existentes — use sync_schemas() para atualizar
    schemas de sistema após um deploy.
    """
    stmt = (
        select(PageVersionModel)
        .where(
            PageVersionModel.page_key == page_key,
            PageVersionModel.scope == "global",
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version_number.desc())
        .limit(1)
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
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


def sync_schemas(session: Session) -> None:
    """Sincroniza page schemas de sistema criando NOVAS versões quando necessário.

    Princípio arquitetural: nunca mutamos versões existentes. Quando o schema
    em código diverge do banco, criamos uma nova versão publicada com
    version_number incrementado. O histórico completo fica preservado para
    rollback, e o renderer sempre busca a versão mais recente.

    Hash MD5 do JSON canônico garante que só atualizamos quando algo realmente
    mudou — evitando versões desnecessárias a cada deploy.

    .. note::
        Schemas scope="global" têm tenant_id=NULL: uma única linha cobre
        todos os tenants da plataforma.
    """
    updated = 0
    skipped = 0

    for page_key, new_schema in SEED_PAGES:
        # Busca a versão published mais recente (maior version_number)
        stmt = (
            select(PageVersionModel)
            .where(
                PageVersionModel.page_key == page_key,
                PageVersionModel.scope == "global",
                PageVersionModel.status == "published",
            )
            .order_by(PageVersionModel.version_number.desc())
            .limit(1)
        )
        current = session.execute(stmt).scalar_one_or_none()
        if not current:
            skipped += 1
            continue

        current_hash = _schema_hash(current.schema_json or {})
        new_hash = _schema_hash(new_schema)

        if current_hash == new_hash:
            skipped += 1
            continue

        # Cria nova versão — não toca na versão anterior (histórico preservado)
        next_version = current.version_number + 1
        new_page = PageVersionModel(
            id=str(uuid.uuid4()),
            page_key=page_key,
            scope="global",
            tenant_id=None,
            base_version_id=current.id,
            version_number=next_version,
            schema_json=new_schema,
            status="published",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(new_page)
        updated += 1
        logger.info(
            "[schema-sync] '%s' v%d → v%d (hash changed)",
            page_key, current.version_number, next_version,
        )

    if updated:
        session.commit()
        logger.info("[schema-sync] %d schemas atualizados, %d sem mudanças", updated, skipped)
    else:
        logger.debug("[schema-sync] Todos os %d schemas estão atualizados", skipped)

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

    # 4. Seed NCM catalog
    from src.infrastructure.persistence.seed_ncm import seed_ncm
    ncm_count = seed_ncm(session)
    if ncm_count:
        print(f"  Seeded {ncm_count} NCM records")

    # 5. Seed agent data (LLM provider for Otto)
    from src.infrastructure.persistence.seed_agent import seed_agent_data
    seed_agent_data()

    # 6. Seed built-in skills metadata
    from src.infrastructure.persistence.seed_skills import seed_skills
    skills_count = seed_skills(session, DEFAULT_TENANT_ID)
    if skills_count:
        print(f"  Seeded {skills_count} skill records")

    # 7. Seed subscription plans
    _seed_plans(session)

    session.commit()


def _seed_plans(session: Session) -> None:
    """Create Free and Pro plans if they don't exist."""
    from src.infrastructure.persistence.sqlalchemy.account_models import (
        PlanModel,
    )

    existing = session.execute(
        select(PlanModel).where(PlanModel.slug == "free")
    ).scalar_one_or_none()
    if existing:
        return

    import uuid as _uuid

    free = PlanModel(
        id=str(_uuid.uuid4()),
        name="Free",
        slug="free",
        price=0,
        enabled=True,
        features={
            "max_projects": 1,
            "max_apps": 1,
            "max_records": 1000,
        },
    )
    pro = PlanModel(
        id=str(_uuid.uuid4()),
        name="Pro",
        slug="pro",
        price=1000,
        enabled=False,
        features={
            "max_projects": 10,
            "max_apps": 50,
            "max_records": -1,
            "priority_support": True,
        },
    )
    session.add_all([free, pro])
    print("  Seeded subscription plans (Free + Pro)")
