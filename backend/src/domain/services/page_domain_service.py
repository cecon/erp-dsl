"""Domain service for page versioning business rules."""

from __future__ import annotations

from typing import Optional

from src.domain.entities.page_version import (
    PageVersion,
    Scope,
    VersionStatus,
)
from src.domain.repositories.page_repository import PageRepository


class PageDomainService:
    """Encapsulates complex page-versioning invariants.

    Rules enforced:
    - Only one published version per (page_key, scope, tenant_id).
    - Publishing archives the previous published version.
    - Rollback re-publishes a previously archived version.
    """

    def __init__(self, repo: PageRepository) -> None:
        self._repo = repo

    def create_draft(
        self,
        page_key: str,
        scope: Scope,
        schema_json: dict,
        tenant_id: Optional[str] = None,
    ) -> PageVersion:
        """Create a new draft version based on the latest version number."""
        if scope == Scope.TENANT and not tenant_id:
            raise ValueError("tenant_id is required for tenant-scoped pages.")

        latest_num = self._repo.get_latest_version_number(
            page_key, scope, tenant_id
        )

        # If tenant scope, use the current global published as base
        base_version_id: Optional[str] = None
        if scope == Scope.TENANT:
            global_pub = self._repo.get_published(
                page_key, Scope.GLOBAL
            )
            if global_pub:
                base_version_id = global_pub.id

        draft = PageVersion(
            page_key=page_key,
            scope=scope,
            tenant_id=tenant_id,
            base_version_id=base_version_id,
            version_number=latest_num + 1,
            schema_json=schema_json,
            status=VersionStatus.DRAFT,
        )
        return self._repo.save(draft)

    def publish(self, version_id: str) -> PageVersion:
        """Publish a draft, archiving the current published version."""
        version = self._repo.get_by_id(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found.")

        # Archive current published version if exists
        current_pub = self._repo.get_published(
            version.page_key, version.scope, version.tenant_id
        )
        if current_pub:
            current_pub.archive()
            self._repo.update(current_pub)

        version.publish()
        return self._repo.update(version)

    def rollback(
        self,
        page_key: str,
        target_version_id: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
    ) -> PageVersion:
        """Rollback to a previous version by swapping published status."""
        target = self._repo.get_by_id(target_version_id)
        if not target:
            raise ValueError(f"Version {target_version_id} not found.")
        if target.page_key != page_key:
            raise ValueError("Version does not belong to this page.")
        if target.status not in (
            VersionStatus.ARCHIVED,
            VersionStatus.PUBLISHED,
        ):
            raise ValueError("Can only rollback to archived/published versions.")

        # Archive current published
        current_pub = self._repo.get_published(page_key, scope, tenant_id)
        if current_pub and current_pub.id != target.id:
            current_pub.archive()
            self._repo.update(current_pub)

        # Re-publish target
        if target.status == VersionStatus.ARCHIVED:
            target.status = VersionStatus.PUBLISHED
            target.updated_at = target.updated_at  # force update
        return self._repo.update(target)
