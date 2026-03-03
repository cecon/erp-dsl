"""Skill: create_entity — persist a new record via the generic CRUD layer.

Used by Otto after the user fills a DynamicForm in the chat.
The LLM calls this skill with entity_key and data from the form response.

Contract: async def create_entity(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
from typing import Any

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    GenericCrudRepository,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    Base,
    PageVersionModel,
)

logger = logging.getLogger(__name__)


def _resolve_schema(db: Any, entity_name: str) -> dict | None:
    """Fetch the published page schema for an entity."""
    row = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == entity_name,
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version.desc())
        .first()
    )
    return row.schema_data if row else None


def _get_table_name(schema: dict, entity_name: str) -> str:
    """Extract tableName from dataSource, with fallback."""
    ds = schema.get("dataSource", {})
    return ds.get("tableName", entity_name)


async def create_entity(params: dict, context: dict) -> dict:
    """Create a new entity record using the generic CRUD repository.

    Args:
        params: Must contain:
            - ``entity_key`` (str): e.g. 'products', 'clients'
            - ``data`` (dict): field values to insert
        context: Must contain ``db`` (SQLAlchemy Session).

    Returns:
        dict with created record or error.
    """
    entity_key = params.get("entity_key", "").strip()
    data = params.get("data", {})

    if not entity_key:
        return {"error": "entity_key is required"}
    if not data:
        return {"error": "data is required"}

    db = context.get("db")
    if db is None:
        return {"error": "No database session in context"}

    # Resolve schema
    schema = _resolve_schema(db, entity_key)
    if schema is None:
        return {"error": f"Schema not found for entity '{entity_key}'"}

    table_name = _get_table_name(schema, entity_key)

    # Check table exists
    table = Base.metadata.tables.get(table_name)
    if table is None:
        return {"error": f"Table '{table_name}' not found"}

    # Get tenant from session
    tenant_id = db.info.get("tenant_id")
    if not tenant_id:
        return {"error": "No tenant_id in session"}

    # Clean data: remove empty strings and None values
    clean_data = {
        k: v for k, v in data.items()
        if v is not None and v != "" and k not in ("id", "tenant_id", "version")
    }

    try:
        repo = GenericCrudRepository(db)
        result = repo.create(table_name, tenant_id, clean_data)
        db.commit()

        # Serialize result
        serialized = {}
        for key, val in dict(result).items():
            if hasattr(val, "isoformat"):
                serialized[key] = val.isoformat()
            else:
                serialized[key] = val

        return {"success": True, "id": serialized.get("id"), "record": serialized}

    except Exception as exc:
        logger.error("create_entity failed for %s: %s", entity_key, exc)
        db.rollback()
        return {"error": str(exc)}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="create_entity",
    fn=create_entity,
    description=(
        "Create a new record in any entity table (products, clients, etc). "
        "Use this after the user fills a form to persist the data. "
        "Params: entity_key (str, e.g. 'products'), data (dict of field values)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "entity_key": {
                "type": "string",
                "description": "Entity key matching the page schema (e.g. 'products', 'clients')",
            },
            "data": {
                "type": "object",
                "description": "Field values to insert (e.g. {name: 'Gasolina', price: 5.99})",
            },
        },
        "required": ["entity_key", "data"],
    },
)
