"""PageVersion entity — the core versionable page definition."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class Scope(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant"


class VersionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class PageVersion:
    """A versioned snapshot of a page's schema and metadata.

    Business rules:
    - Only one version may be published per (page_key, scope, tenant_id).
    - Published versions are immutable.
    - Rollback swaps the active published version.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page_key: str = ""
    scope: Scope = Scope.GLOBAL
    tenant_id: Optional[str] = None
    base_version_id: Optional[str] = None
    version_number: int = 1
    schema_json: dict[str, Any] = field(default_factory=dict)
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ── Business rules ──────────────────────────────────────────────

    def can_edit(self) -> bool:
        """Only drafts can be modified."""
        return self.status == VersionStatus.DRAFT

    def publish(self) -> None:
        """Transition from draft to published."""
        if self.status != VersionStatus.DRAFT:
            raise ValueError(
                f"Cannot publish version in status '{self.status.value}'. "
                "Only drafts can be published."
            )
        self.status = VersionStatus.PUBLISHED
        self.updated_at = datetime.now(timezone.utc)

    def archive(self) -> None:
        """Transition from published to archived."""
        if self.status != VersionStatus.PUBLISHED:
            raise ValueError(
                f"Cannot archive version in status '{self.status.value}'. "
                "Only published versions can be archived."
            )
        self.status = VersionStatus.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)

    def update_schema(self, schema_json: dict[str, Any]) -> None:
        """Update the schema if the version is still a draft."""
        if not self.can_edit():
            raise ValueError("Cannot modify a non-draft version.")
        self.schema_json = schema_json
        self.updated_at = datetime.now(timezone.utc)
