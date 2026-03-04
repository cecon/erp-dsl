"""Domain entities for the platform management layer.

Pure Python dataclasses — no SQLAlchemy or framework dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Account:
    """A platform account — the person who signs up."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Subscription:
    """Links an account to a plan."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    plan_id: str = ""
    status: str = "active"  # active | cancelled | expired
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Plan:
    """An available subscription plan."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    slug: str = ""
    price: float = 0.0
    enabled: bool = True
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """A project groups apps and a company under one umbrella."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    subscription_id: str = ""
    name: str = ""
    slug: str = ""
    status: str = "active"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Company:
    """Company or individual that owns a project."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    type: str = "pj"  # pj | pf
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    ie: Optional[str] = None
    im: Optional[str] = None
    endereco: Optional[dict[str, Any]] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class App:
    """An application within a project."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = ""
    slug: str = ""
    status: str = "active"
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class DatabaseInfo:
    """Connection info for an app's isolated database."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    app_id: str = ""
    db_name: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_user: str = ""
    db_password: str = ""
    status: str = "provisioning"  # provisioning | ready | error
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
