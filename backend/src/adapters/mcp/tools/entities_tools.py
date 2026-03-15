"""MCP tools — Generic entity CRUD operations.

Each tool maps to the existing GenericCrudRepository logic,
operating under the admin tenant context resolved from the database.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from src.adapters.mcp.mcp_auth import get_admin_context
from src.application.dsl_functions.pipeline_runner import (
    run_response_pipeline,
)
from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    GenericCrudRepository,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    Base,
    PageVersionModel,
)


def _resolve_schema(db: Session, entity_name: str) -> dict[str, Any]:
    """Fetch the published global page schema for an entity."""
    page = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == entity_name,
            PageVersionModel.scope == "global",
            PageVersionModel.status == "published",
        )
        .first()
    )
    if not page or not page.schema_json:
        raise ValueError(f"No published schema for '{entity_name}'")
    return page.schema_json


def _get_table_name(schema: dict[str, Any], entity_name: str) -> str:
    ds = schema.get("dataSource", {})
    table_name = ds.get("tableName", entity_name)
    if table_name not in Base.metadata.tables:
        raise ValueError(f"Table '{table_name}' not found in metadata")
    return table_name


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    from decimal import Decimal
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}


def register_entity_tools(mcp: FastMCP, get_db: Any) -> None:
    """Register all entity CRUD tools into the FastMCP instance."""

    @mcp.tool()
    def list_entities(
        entity_name: str,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Lista todos os registros de uma entidade do ERP.

        Args:
            entity_name: Nome da entidade (ex: 'produtos', 'clientes', 'fornecedores').
            offset: Paginação — início dos registros.
            limit: Quantidade máxima de registros retornados (padrão 50).
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            db.info["tenant_id"] = ctx.tenant_id
            schema = _resolve_schema(db, entity_name)
            table_name = _get_table_name(schema, entity_name)
            repo = GenericCrudRepository(db)
            result = repo.list(table_name, ctx.tenant_id, offset, limit)
            result["items"] = [
                run_response_pipeline(_serialize(r), schema)
                for r in result["items"]
            ]
            return result
        finally:
            db.close()

    @mcp.tool()
    def get_entity(entity_name: str, entity_id: str) -> dict[str, Any]:
        """Busca um registro específico de uma entidade do ERP pelo ID.

        Args:
            entity_name: Nome da entidade (ex: 'produtos', 'clientes').
            entity_id: ID (UUID ou inteiro) do registro.
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            db.info["tenant_id"] = ctx.tenant_id
            schema = _resolve_schema(db, entity_name)
            table_name = _get_table_name(schema, entity_name)
            repo = GenericCrudRepository(db)
            result = repo.get_by_id(table_name, ctx.tenant_id, entity_id)
            if not result:
                raise ValueError(f"Entity '{entity_name}' with id '{entity_id}' not found")
            return run_response_pipeline(_serialize(result), schema)
        finally:
            db.close()



    @mcp.tool()
    def delete_entity(entity_name: str, entity_id: str) -> dict[str, str]:
        """Remove um registro de uma entidade do ERP.

        Args:
            entity_name: Nome da entidade (ex: 'produtos', 'clientes').
            entity_id: ID do registro a ser removido.
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)
            db.info["tenant_id"] = ctx.tenant_id
            schema = _resolve_schema(db, entity_name)
            table_name = _get_table_name(schema, entity_name)
            repo = GenericCrudRepository(db)
            deleted = repo.delete(table_name, ctx.tenant_id, entity_id)
            if not deleted:
                raise ValueError(f"Entity '{entity_name}' with id '{entity_id}' not found")
            db.commit()
            return {"detail": f"{entity_name} '{entity_id}' deleted"}
        finally:
            db.close()

    @mcp.tool()
    def list_entity_types() -> list[dict[str, Any]]:
        """Lista todas as entidades (tabelas) disponíveis no ERP.

        Retorna o nome da entidade, a descrição e os campos disponíveis.
        Use isto para descobrir quais entidades existem antes de chamar
        list_entities, get_entity, create_entity, etc.
        """
        db: Session = next(get_db())
        try:
            pages = (
                db.query(PageVersionModel)
                .filter(
                    PageVersionModel.scope == "global",
                    PageVersionModel.status == "published",
                    PageVersionModel.page_key.notlike("\\_%"),  # Skip _sidebar, _header, etc.
                    ~PageVersionModel.page_key.endswith("_form"),  # Skip form pages
                )
                .order_by(PageVersionModel.page_key)
                .all()
            )
            result = []
            for p in pages:
                schema = p.schema_json or {}
                ds = schema.get("dataSource", {})
                fields = ds.get("fields", [])
                result.append({
                    "entity_name": p.page_key,
                    "title": schema.get("title", p.page_key),
                    "description": schema.get("description", ""),
                    "table_name": ds.get("tableName", p.page_key),
                    "fields": [
                        {"id": f["id"], "type": f.get("dbType", "string"), "required": f.get("required", False)}
                        for f in fields
                    ],
                })
            return result
        finally:
            db.close()

    @mcp.tool()
    def list_pages() -> list[dict[str, str]]:
        """Lista todos os page schemas publicados no ERP.

        Retorna page_key, título e layout (grid ou form).
        Útil para descobrir todas as telas disponíveis no sistema.
        """
        db: Session = next(get_db())
        try:
            pages = (
                db.query(PageVersionModel)
                .filter(
                    PageVersionModel.scope == "global",
                    PageVersionModel.status == "published",
                )
                .order_by(PageVersionModel.page_key)
                .all()
            )
            return [
                {
                    "page_key": p.page_key,
                    "title": (p.schema_json or {}).get("title", p.page_key),
                    "layout": (p.schema_json or {}).get("layout", "unknown"),
                }
                for p in pages
            ]
        finally:
            db.close()

