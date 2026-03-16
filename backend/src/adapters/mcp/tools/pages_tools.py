"""MCP tools — Page schema management.

Allows the Claude model to list, inspect and manage page schemas
(the DSL definitions that drive the ERP frontend).
"""

from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from src.adapters.mcp.mcp_auth import get_admin_context
from src.application.use_cases.create_draft import CreateDraftUseCase
from src.application.use_cases.get_page import GetPageUseCase
from src.application.use_cases.publish_page import PublishPageUseCase
from src.application.use_cases.rollback_page import RollbackPageUseCase
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel
from src.infrastructure.persistence.sqlalchemy.page_repository_impl import (
    PageRepositoryImpl,
)


def register_page_tools(mcp: FastMCP, get_db: Any) -> None:
    """Register all page schema tools into the FastMCP instance."""

    @mcp.tool()
    def list_pages() -> list[dict[str, Any]]:
        """Lista todas as páginas publicadas no ERP (schemas globais).

        Retorna uma lista com page_key, status e version_number de cada página.
        """
        db: Session = next(get_db())
        try:
            pages = (
                db.query(PageVersionModel)
                .filter(
                    PageVersionModel.scope == "global",
                    PageVersionModel.status == "published",
                )
                .all()
            )
            return [
                {
                    "page_key": p.page_key,
                    "version_id": str(p.id),
                    "version_number": p.version_number,
                    "status": p.status,
                    "scope": p.scope,
                }
                for p in pages
            ]
        finally:
            db.close()

    @mcp.tool()
    def get_page_schema(page_key: str) -> dict[str, Any]:
        """Retorna o schema JSON publicado de uma página do ERP.

        Args:
            page_key: Chave da página (ex: 'produtos', 'clientes', 'dashboard').
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            uc = GetPageUseCase(PageRepositoryImpl(db))
            result = uc.execute(page_key, ctx.tenant_id)
            if not result:
                raise ValueError(f"Page '{page_key}' not found or not published")
            return result
        finally:
            db.close()

    @mcp.tool()
    def create_page_draft(
        page_key: str,
        schema_json: dict[str, Any],
    ) -> dict[str, Any]:
        """Cria um rascunho (draft) de schema para uma página do ERP.

        Use este tool para propor alterações em uma página antes de publicá-la.
        Após criar um draft, use publish_page_version para publicar.

        Args:
            page_key: Chave da página (ex: 'produtos').
            schema_json: Novo schema JSON completo da página.
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            uc = CreateDraftUseCase(PageRepositoryImpl(db))
            result = uc.execute(
                page_key=page_key,
                schema_json=schema_json,
                tenant_id=ctx.tenant_id,
            )
            db.commit()
            return result
        finally:
            db.close()

    @mcp.tool()
    def publish_page_version(page_key: str, version_id: str) -> dict[str, Any]:
        """Publica uma versão de draft de uma página do ERP.

        Args:
            page_key: Chave da página (ex: 'produtos').
            version_id: ID da versão draft a ser publicada (obtido via create_page_draft).
        """
        db: Session = next(get_db())
        try:
            uc = PublishPageUseCase(PageRepositoryImpl(db))
            result = uc.execute(page_key, version_id)
            db.commit()
            return result
        finally:
            db.close()

    @mcp.tool()
    def rollback_page_version(page_key: str, version_id: str) -> dict[str, Any]:
        """Faz rollback de uma página para uma versão anterior.

        Args:
            page_key: Chave da página (ex: 'produtos').
            version_id: ID da versão para qual fazer rollback.
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            uc = RollbackPageUseCase(PageRepositoryImpl(db))
            result = uc.execute(
                page_key=page_key,
                version_id=version_id,
                tenant_id=ctx.tenant_id,
            )
            db.commit()
            return result
        finally:
            db.close()
