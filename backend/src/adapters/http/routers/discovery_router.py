"""Introspection router — Discovery endpoints for MCP/AI tools.

These endpoints are public (no auth required) because:
1. The MCP connection itself is already authenticated via api_key
2. These are read-only discovery endpoints
3. FastApiMCP internal calls don't propagate auth headers
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_db
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

router = APIRouter()


@router.get("/entity_types")
def list_entity_types(
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Lista todas as entidades (tabelas) disponíveis no ERP.

    Retorna o nome da entidade, a descrição e os campos disponíveis.
    Use isto para descobrir quais entidades existem antes de chamar
    os endpoints /entities/{entity_name}.
    """
    pages = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.scope == "global",
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.page_key)
        .all()
    )
    # Filter in Python to avoid LIKE wildcard issues with '_'
    result = []
    for p in pages:
        if p.page_key.startswith("_") or p.page_key.endswith("_form"):
            continue
        schema = p.schema_json or {}
        ds = schema.get("dataSource", {})
        fields = ds.get("fields", [])
        result.append({
            "entity_name": p.page_key,
            "title": schema.get("title", p.page_key),
            "description": schema.get("description", ""),
            "table_name": ds.get("tableName", p.page_key),
            "fields": [
                {
                    "id": f["id"],
                    "type": f.get("dbType", "string"),
                    "required": f.get("required", False),
                }
                for f in fields
            ],
        })
    return result


@router.get("/pages")
def list_pages(
    db: Session = Depends(get_db),
) -> list[dict[str, str]]:
    """Lista todos os page schemas publicados no ERP.

    Retorna page_key, título e layout (grid ou form).
    Útil para descobrir todas as telas disponíveis no sistema.
    """
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


@router.get("/page_schema/{page_key}")
def get_page_schema(
    page_key: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retorna o schema DSL completo de uma página.

    Args:
        page_key: Nome da página (ex: 'operation_natures_form', 'products').
    """
    page = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == page_key,
            PageVersionModel.scope == "global",
            PageVersionModel.status == "published",
        )
        .first()
    )
    if not page:
        return {"error": f"Page '{page_key}' not found"}
    return page.schema_json or {}
