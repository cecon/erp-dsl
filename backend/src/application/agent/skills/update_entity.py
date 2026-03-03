"""Skill: update_entity — update an existing record via the generic CRUD layer.

Used by Otto to modify existing records in any entity table.

Contract: async def update_entity(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
from typing import Any

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    GenericCrudRepository,
    StaleDataError,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    Base,
    PageVersionModel,
)

logger = logging.getLogger(__name__)


def _resolve_table_name(db: Any, entity_key: str) -> str | None:
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


async def update_entity(params: dict, context: dict) -> dict:
    """Update an existing entity record.

    Args:
        params:
            - entity_key (str): e.g. 'products'
            - id (str): record ID to update
            - data (dict): fields to update (partial update)
        context: Must contain ``db`` and ``tenant_id``.

    Returns:
        dict with updated record or error.
    """
    entity_key = params.get("entity_key", "").strip()
    entity_id = params.get("id", "").strip()
    data = params.get("data", {})

    if not entity_key:
        return {"error": "entity_key is required"}
    if not entity_id:
        return {"error": "id is required"}
    if not data:
        return {"error": "data is required (fields to update)"}

    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or not tenant_id:
        return {"error": "No database session or tenant_id in context"}

    table_name = _resolve_table_name(db, entity_key) or entity_key
    table = Base.metadata.tables.get(table_name)
    if table is None:
        return {"error": f"Table '{table_name}' not found"}

    # Clean data: remove internal keys
    clean_data = {
        k: v for k, v in data.items()
        if k not in ("id", "tenant_id", "created_at")
    }

    try:
        repo = GenericCrudRepository(db)
        result = repo.update(
            table_name=table_name,
            tenant_id=tenant_id,
            entity_id=entity_id,
            data=clean_data,
        )
        if result is None:
            return {"error": f"Record '{entity_id}' not found"}

        db.commit()

        # Serialize
        serialized = {}
        for key, val in result.items():
            if hasattr(val, "isoformat"):
                serialized[key] = val.isoformat()
            else:
                serialized[key] = val

        return {"success": True, "record": serialized}

    except StaleDataError as exc:
        db.rollback()
        return {"error": f"Conflict: {exc}"}
    except Exception as exc:
        logger.error("update_entity failed for %s/%s: %s", entity_key, entity_id, exc)
        db.rollback()
        return {"error": str(exc)}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="update_entity",
    fn=update_entity,
    description=(
        "Update an existing record in any entity table (products, clients, etc). "
        "Supports partial updates — only specified fields are changed. "
        "Params: entity_key (str), id (str), data (dict of fields to update)."
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
                "description": "Record ID to update",
            },
            "data": {
                "type": "object",
                "description": "Fields to update (e.g. {price: 10.99})",
            },
        },
        "required": ["entity_key", "id", "data"],
    },
)
