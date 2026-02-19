"""Use case: Publish a draft page version."""

from __future__ import annotations

from typing import Any

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.services.page_domain_service import PageDomainService


class PublishPageUseCase:
    """Publishes a draft, archiving any previously published version."""

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo
        self._service = PageDomainService(page_repo)

    def execute(self, page_key: str, version_id: str) -> dict[str, Any]:
        version = self._service.publish(version_id)
        return {
            "id": version.id,
            "page_key": version.page_key,
            "version_number": version.version_number,
            "status": version.status.value,
        }
