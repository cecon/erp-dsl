"""Use case: Create a new draft page version."""

from __future__ import annotations

from typing import Any, Optional

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.entities.page_version import Scope
from src.domain.services.page_domain_service import PageDomainService


class CreateDraftUseCase:
    """Creates a new draft version for a page."""

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo
        self._service = PageDomainService(page_repo)

    def execute(
        self,
        page_key: str,
        schema_json: dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        scope = Scope.TENANT if tenant_id else Scope.GLOBAL
        draft = self._service.create_draft(
            page_key=page_key,
            scope=scope,
            schema_json=schema_json,
            tenant_id=tenant_id,
        )
        return {
            "id": draft.id,
            "page_key": draft.page_key,
            "scope": draft.scope.value,
            "tenant_id": draft.tenant_id,
            "version_number": draft.version_number,
            "status": draft.status.value,
        }
