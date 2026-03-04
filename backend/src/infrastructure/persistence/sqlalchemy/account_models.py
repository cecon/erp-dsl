"""SQLAlchemy models for the platform management layer.

These models live in the MAIN database and manage accounts,
plans, projects, apps and tenant database provisioning.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON

from src.infrastructure.persistence.sqlalchemy.models import Base


class AccountModel(Base):
    """Platform account — the person who signs up."""

    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class PlanModel(Base):
    """Available subscription plans."""

    __tablename__ = "plans"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    slug = Column(String(32), nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    enabled = Column(Boolean, nullable=False, default=True)
    features = Column(JSON, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class SubscriptionModel(Base):
    """Links an account to a plan."""

    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True)
    account_id = Column(
        String(36),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        String(36),
        ForeignKey("plans.id"),
        nullable=False,
    )
    status = Column(
        String(16), nullable=False, default="active",
    )  # active | cancelled | expired
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class ProjectModel(Base):
    """A project groups apps and a company under one umbrella."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    account_id = Column(
        String(36),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id = Column(
        String(36),
        ForeignKey("subscriptions.id"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(64), nullable=False)
    status = Column(
        String(16), nullable=False, default="active",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "account_id", "slug", name="uq_project_account_slug",
        ),
    )


class ProjectCompanyModel(Base):
    """Company or individual that owns a project."""

    __tablename__ = "project_companies"

    id = Column(String(36), primary_key=True)
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    type = Column(
        String(2), nullable=False, default="pj",
    )  # pj | pf
    razao_social = Column(String(255), nullable=True)
    nome_fantasia = Column(String(255), nullable=True)
    cnpj_cpf = Column(String(18), nullable=True)
    ie = Column(String(20), nullable=True)
    im = Column(String(20), nullable=True)
    endereco = Column(JSON, nullable=True, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class ProjectAppModel(Base):
    """An application within a project."""

    __tablename__ = "project_apps"

    id = Column(String(36), primary_key=True)
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(64), nullable=False)
    status = Column(
        String(16), nullable=False, default="active",
    )
    llm_provider = Column(String(64), nullable=True)
    llm_model = Column(String(128), nullable=True)
    llm_api_key = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "project_id", "slug", name="uq_app_project_slug",
        ),
    )


class ProjectDatabaseModel(Base):
    """Connection info for an app's isolated database."""

    __tablename__ = "project_databases"

    id = Column(String(36), primary_key=True)
    app_id = Column(
        String(36),
        ForeignKey("project_apps.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    db_name = Column(String(128), nullable=False)
    db_host = Column(String(255), nullable=False)
    db_port = Column(Integer, nullable=False, default=5432)
    db_user = Column(String(128), nullable=False)
    db_password = Column(String(256), nullable=False)
    status = Column(
        String(16), nullable=False, default="provisioning",
    )  # provisioning | ready | error
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class TenantMigrationModel(Base):
    """Tracks which migrations have been applied to each tenant DB."""

    __tablename__ = "tenant_migrations"

    id = Column(String(36), primary_key=True)
    app_id = Column(
        String(36),
        ForeignKey("project_apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    migration_name = Column(String(255), nullable=False)
    applied_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "app_id", "migration_name",
            name="uq_tenant_migration",
        ),
    )
