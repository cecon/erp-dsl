"""Skill: list_entities — list / search records from any entity table.

Used by Otto to inspect existing data in the current page's entity.
Returns paginated, filtered records using the GenericCrudRepository.

Contract: async def list_entities(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    GenericCrudRepository,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    Base,
    PageVersionModel,
)

logger = logging.getLogger(__name__)


def _resolve_table_name(db, entity_key: str) -> str | None:
    """Get the physical table name from the published page schema."""
    row = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == entity_key,
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version_number.desc())
        .first()
    )
    if row is None:
        return None
    ds = (row.schema_json or {}).get("dataSource", {})
    return ds.get("tableName", entity_key)


async def list_entities(params: dict, context: dict) -> dict:
    """List records from an entity table.

    Args:
        params:
            - entity_key (str): e.g. 'products', 'clients'
            - limit (int, optional): max rows (default 20)
            - offset (int, optional): pagination offset (default 0)
            - filters (list[dict], optional): [{field, operator, value}]
            - search (str, optional): free-text search across text columns
        context: Must contain ``db`` and ``tenant_id``.

    Returns:
        dict with items, total, offset, limit.
    """
    entity_key = params.get("entity_key", "").strip()
    limit = min(params.get("limit", 20), 100)
    offset = params.get("offset", 0)
    filters = params.get("filters", [])

    if not entity_key:
        return {"error": "entity_key is required"}

    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or not tenant_id:
        return {"error": "No database session or tenant_id in context"}

    table_name = _resolve_table_name(db, entity_key)
    if table_name is None:
        # Fallback: try entity_key directly as table name
        table_name = entity_key

    table = Base.metadata.tables.get(table_name)
    if table is None:
        return {"error": f"Table '{table_name}' not found"}

    try:
        repo = GenericCrudRepository(db)
        result = repo.list(
            table_name=table_name,
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            filters=filters,
        )

        # Serialize dates in items
        serialized_items = []
        for item in result["items"]:
            row = {}
            for k, v in item.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
                else:
                    row[k] = v
            serialized_items.append(row)

        return {
            "items": serialized_items,
            "total": result["total"],
            "offset": result["offset"],
            "limit": result["limit"],
        }

    except Exception as exc:
        logger.error("list_entities failed for %s: %s", entity_key, exc)
        return {"error": str(exc)}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="list_entities",
    fn=list_entities,
    description=(
        "List/search records from any entity table (products, clients, etc). "
        "Use this to see existing data, answer questions about records, "
        "or verify data before updates. "
        "Params: entity_key (str), limit (int, optional), offset (int, optional), "
        "filters (list of {field, operator, value}, optional)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "entity_key": {
                "type": "string",
                "description": "Entity key matching the page (e.g. 'products')",
            },
            "limit": {
                "type": "integer",
                "description": "Max rows to return (default 20, max 100)",
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset (default 0)",
            },
            "filters": {
                "type": "array",
                "description": "Filter conditions: [{field, operator, value}]",
            },
        },
        "required": ["entity_key"],
    },
)
