"""SQLAlchemy ORM models — separate from domain entities."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TenantModel(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(64), nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    username = Column(String(128), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="user")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class PageVersionModel(Base):
    __tablename__ = "page_versions"
    __table_args__ = (
        UniqueConstraint(
            "page_key", "scope", "tenant_id", "version_number",
            name="uq_page_version",
        ),
    )

    id = Column(String(36), primary_key=True)
    page_key = Column(String(64), nullable=False, index=True)
    scope = Column(
        Enum("global", "tenant", name="page_scope"),
        nullable=False,
        default="global",
    )
    tenant_id = Column(String(36), nullable=True, index=True)
    base_version_id = Column(String(36), nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    schema_json = Column(JSON, nullable=False, default=dict)
    status = Column(
        Enum("draft", "published", "archived", name="version_status"),
        nullable=False,
        default="draft",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    sku = Column(String(64), nullable=True)
    ean = Column(String(14), nullable=True)
    foto_url = Column(Text, nullable=True)
    descricao_tecnica = Column(Text, nullable=True)
    unidade = Column(String(6), nullable=True, default="UN")
    ncm_codigo = Column(String(8), nullable=True)
    cest_codigo = Column(String(7), nullable=True)
    cclass_codigo = Column(String(16), nullable=True)
    custom_fields = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    version = Column(Integer, nullable=False, default=1)


class AuditLogModel(Base):
    """Basic audit trail for changes."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(36), nullable=False)
    action = Column(String(32), nullable=False)
    user_id = Column(String(36), nullable=True)
    tenant_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    version = Column(Integer, nullable=False, default=1)


class WorkflowModel(Base):
    """Persists workflow definitions with steps as JSON."""
    __tablename__ = "workflows"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "command", name="uq_workflow_tenant_command",
        ),
    )

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    command = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    steps = Column(JSON, nullable=False, default=list)
    status = Column(
        String(16),
        nullable=False,
        default="draft",
    )
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
