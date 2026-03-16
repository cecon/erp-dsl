"""Use case: Get version status for a page (global vs tenant divergence)."""

from typing import Any, Optional

from src.application.ports.page_repository_port import PageRepositoryPort
from src.domain.entities.page_version import Scope


class GetVersionStatusUseCase:
    """Verifica se o schema tenant está desatualizado em relação ao global.

    Retorna informações de versão para o SchemaVersionBanner do frontend:
    - Qual scope está sendo renderizado (global ou tenant)
    - Se há atualizações disponíveis no schema global
    - IDs para operações de rollback/merge
    """

    def __init__(self, page_repo: PageRepositoryPort) -> None:
        self._page_repo = page_repo

    def execute(
        self, page_key: str, tenant_id: Optional[str] = None
    ) -> dict[str, Any]:
        # Global published (latest version)
        global_pub = self._page_repo.get_published(page_key, Scope.GLOBAL)

        # Tenant-specific published (latest version)
        tenant_pub = None
        if tenant_id:
            tenant_pub = self._page_repo.get_published(
                page_key, Scope.TENANT, tenant_id
            )

        global_version = global_pub.version_number if global_pub else None
        global_version_id = global_pub.id if global_pub else None

        if tenant_pub:
            # Tenant tem customização — verifica se global avançou
            has_updates = (
                global_pub is not None
                and global_pub.version_number > 1
                # Compara se o base_version_id do tenant aponta para o global atual
                and tenant_pub.base_version_id != global_version_id
            )
            return {
                "scope": "tenant",
                "tenant_version": tenant_pub.version_number,
                "tenant_version_id": tenant_pub.id,
                "global_version": global_version,
                "global_version_id": global_version_id,
                "has_updates": has_updates,
            }

        # Sem customização — usa global, nunca tem updates pendentes
        return {
            "scope": "global",
            "tenant_version": None,
            "tenant_version_id": None,
            "global_version": global_version,
            "global_version_id": global_version_id,
            "has_updates": False,
        }
