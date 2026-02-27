"""SQLAlchemy ORM models for the AI agent module."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.persistence.sqlalchemy.models import Base


class LLMProviderModel(Base):
    """LLM provider configuration per tenant."""

    __tablename__ = "llm_providers"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    base_url = Column(Text, nullable=True)
    params = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
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


class SkillModel(Base):
    """Agent skill definition — global (tenant_id=NULL) or per-tenant."""

    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    skill_type = Column(
        Enum("builtin", "custom", "llm", "http", name="skill_type_enum"),
        nullable=False,
        default="builtin",
    )
    implementation = Column(Text, nullable=True)
    params_schema = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
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


class ChatSessionModel(Base):
    """Chat session between a user and the agent."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    context = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChatMessageModel(Base):
    """Individual message in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    role = Column(
        Enum("user", "agent", "skill", name="chat_role_enum"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    skill_name = Column(String(128), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
