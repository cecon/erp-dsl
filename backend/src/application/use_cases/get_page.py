"""Use case: Get the resolved page for a tenant (with global fallback)."""

from __future__ import annotations

from typing import Any, Optional

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.entities.page_version import Scope


class GetPageUseCase:
    """Resolves the published page for a given tenant.

    Strategy:
    1. Look for a tenant-scoped published version.
    2. Fall back to the global published version.
    """

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo

    def execute(
        self, page_key: str, tenant_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        # Try tenant-specific first
        if tenant_id:
            tenant_version = self._page_repo.get_published(
                page_key, Scope.TENANT, tenant_id
            )
            if tenant_version:
                return {
                    "id": tenant_version.id,
                    "page_key": tenant_version.page_key,
                    "scope": tenant_version.scope.value,
                    "tenant_id": tenant_version.tenant_id,
                    "version_number": tenant_version.version_number,
                    "schema": tenant_version.schema_json,
                    "status": tenant_version.status.value,
                }

        # Fallback to global
        global_version = self._page_repo.get_published(
            page_key, Scope.GLOBAL
        )
        if global_version:
            return {
                "id": global_version.id,
                "page_key": global_version.page_key,
                "scope": global_version.scope.value,
                "tenant_id": None,
                "version_number": global_version.version_number,
                "schema": global_version.schema_json,
                "status": global_version.status.value,
            }

        return None
