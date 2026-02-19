"""Use case: Rollback to a previous page version."""

from __future__ import annotations

from typing import Any, Optional

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.entities.page_version import Scope
from src.domain.services.page_domain_service import PageDomainService


class RollbackPageUseCase:
    """Rollback page to a previously archived version."""

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo
        self._service = PageDomainService(page_repo)

    def execute(
        self,
        page_key: str,
        version_id: str,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        scope = Scope.TENANT if tenant_id else Scope.GLOBAL
        version = self._service.rollback(
            page_key=page_key,
            target_version_id=version_id,
            scope=scope,
            tenant_id=tenant_id,
        )
        return {
            "id": version.id,
            "page_key": version.page_key,
            "version_number": version.version_number,
            "status": version.status.value,
        }
