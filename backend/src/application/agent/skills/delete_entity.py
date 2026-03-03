"""Skill: delete_entity — delete a record via the generic CRUD layer.

Used by Otto to remove records from any entity table.

Contract: async def delete_entity(params: dict, context: dict) -> dict
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


async def delete_entity(params: dict, context: dict) -> dict:
    """Delete a record from an entity table.

    Args:
        params:
            - entity_key (str): e.g. 'products'
            - id (str): record ID to delete
        context: Must contain ``db`` and ``tenant_id``.

    Returns:
        dict with success status or error.
    """
    entity_key = params.get("entity_key", "").strip()
    entity_id = params.get("id", "").strip()

    if not entity_key:
        return {"error": "entity_key is required"}
    if not entity_id:
        return {"error": "id is required"}

    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or not tenant_id:
        return {"error": "No database session or tenant_id in context"}

    table_name = _resolve_table_name(db, entity_key) or entity_key
    table = Base.metadata.tables.get(table_name)
    if table is None:
        return {"error": f"Table '{table_name}' not found"}

    try:
        repo = GenericCrudRepository(db)
        deleted = repo.delete(
            table_name=table_name,
            tenant_id=tenant_id,
            entity_id=entity_id,
        )
        if not deleted:
            return {"error": f"Record '{entity_id}' not found"}

        db.commit()
        return {"success": True, "deleted_id": entity_id}

    except Exception as exc:
        logger.error("delete_entity failed for %s/%s: %s", entity_key, entity_id, exc)
        db.rollback()
        return {"error": str(exc)}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="delete_entity",
    fn=delete_entity,
    description=(
        "Delete a record from any entity table (products, clients, etc). "
        "IMPORTANT: Always confirm with the user before deleting. "
        "Params: entity_key (str), id (str)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "entity_key": {
                "type": "string",
                "description": "Entity key (e.g. 'products')",
            },
            "id": {
                "type": "string",
                "description": "Record ID to delete",
            },
        },
        "required": ["entity_key", "id"],
    },
)
