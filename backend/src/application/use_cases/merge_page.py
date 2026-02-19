"""Use case: Merge global page version into tenant override."""

from __future__ import annotations

from typing import Any, Optional

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.entities.page_version import Scope, VersionStatus
from src.domain.services.merge_service import MergeService
from src.domain.services.page_domain_service import PageDomainService


class MergePageUseCase:
    """Merges the latest global published schema into a tenant's version.

    Creates a new draft with the merged result.
    """

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo
        self._service = PageDomainService(page_repo)
        self._merger = MergeService()

    def execute(
        self, page_key: str, tenant_id: str
    ) -> Optional[dict[str, Any]]:
        # Get global published version
        global_pub = self._page_repo.get_published(page_key, Scope.GLOBAL)
        if not global_pub:
            raise ValueError(
                f"No global published version found for '{page_key}'."
            )

        # Get tenant published version
        tenant_pub = self._page_repo.get_published(
            page_key, Scope.TENANT, tenant_id
        )
        if not tenant_pub:
            raise ValueError(
                f"No tenant published version found for '{page_key}' "
                f"in tenant '{tenant_id}'."
            )

        # Deep merge: global as base, tenant as override
        merged_schema = self._merger.deep_merge(
            base=global_pub.schema_json,
            override=tenant_pub.schema_json,
        )

        # Create a new draft with merged schema
        draft = self._service.create_draft(
            page_key=page_key,
            scope=Scope.TENANT,
            schema_json=merged_schema,
            tenant_id=tenant_id,
        )
        draft.base_version_id = global_pub.id
        self._page_repo.update(draft)

        return {
            "id": draft.id,
            "page_key": draft.page_key,
            "version_number": draft.version_number,
            "status": draft.status.value,
            "merged_from_global_version": global_pub.version_number,
        }
