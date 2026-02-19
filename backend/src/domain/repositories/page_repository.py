"""Abstract repository interface for page versions (domain Protocol)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.entities.page_version import PageVersion, Scope, VersionStatus


class PageRepository(Protocol):
    """Port for persisting and querying page versions."""

    def get_by_id(self, version_id: str) -> Optional[PageVersion]: ...

    def get_published(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
    ) -> Optional[PageVersion]: ...

    def get_versions(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
        status: Optional[VersionStatus] = None,
    ) -> list[PageVersion]: ...

    def get_latest_version_number(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
    ) -> int: ...

    def save(self, version: PageVersion) -> PageVersion: ...

    def update(self, version: PageVersion) -> PageVersion: ...
