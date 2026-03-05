"""Skill: get_entity_schema — fetch the DSL form schema for any entity.

Used by Otto to discover the real field definitions before creating
interactive forms in the chat. Returns dataSource fields, form components,
endpoint, and tableName from the published page_version.

Contract: async def get_entity_schema(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

logger = logging.getLogger(__name__)


def _extract_form_fields(components: list) -> list[dict]:
    """Recursively extract field definitions from the component tree."""
    fields: list[dict] = []
    for comp in components:
        ctype = comp.get("type", "")
        # Skip structural containers, recurse into their children
        if ctype in ("form", "section", "grid", "tabs", "tab"):
            fields.extend(_extract_form_fields(comp.get("components", [])))
        else:
            # This is an actual field
            field = {"id": comp.get("id", ""), "type": ctype}
            if comp.get("label"):
                field["label"] = comp["label"]
            if comp.get("options"):
                field["options"] = comp["options"]
            if comp.get("required"):
                field["required"] = True
            if comp.get("dataSource"):
                field["dataSource"] = comp["dataSource"]
            fields.append(field)
    return fields


async def get_entity_schema(params: dict, context: dict) -> dict:
    """Fetch the DSL schema for any entity page.

    Args:
        params:
            - page_key (str): e.g. 'products_form', 'operation_natures_form',
              or just 'products' (will try '{page_key}_form' too).
        context: Must contain ``db``.

    Returns:
        dict with form_fields, ds_fields, endpoint, tableName.
    """
    page_key = params.get("page_key", "").strip()
    if not page_key:
        return {"error": "page_key is required"}

    db = context.get("db")
    if db is None:
        return {"error": "No database session in context"}

    # Try the given key first, then the _form variant
    candidates = [page_key]
    if not page_key.endswith("_form"):
        candidates.append(f"{page_key}_form")

    row = None
    used_key = page_key
    for key in candidates:
        row = (
            db.query(PageVersionModel)
            .filter(
                PageVersionModel.page_key == key,
                PageVersionModel.status == "published",
            )
            .order_by(PageVersionModel.version_number.desc())
            .first()
        )
        if row:
            used_key = key
            break

    if row is None:
        return {"error": f"Schema not found for '{page_key}'"}

    schema = row.schema_json or {}
    ds = schema.get("dataSource", {})

    # Extract form field definitions from the component tree
    form_fields = _extract_form_fields(schema.get("components", []))

    # Extract dataSource field definitions
    ds_fields = ds.get("fields", [])

    return {
        "page_key": used_key,
        "title": schema.get("title", used_key),
        "endpoint": ds.get("endpoint", ""),
        "tableName": ds.get("tableName", ""),
        "form_fields": form_fields,
        "ds_fields": [
            {"id": f.get("id", ""), "dbType": f.get("dbType", "string"), "required": f.get("required", False)}
            for f in ds_fields
        ],
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="get_entity_schema",
    fn=get_entity_schema,
    description=(
        "Fetch the DSL form schema for any entity (products, operation_natures, etc). "
        "Returns the real field definitions (id, type, label, options) from the published "
        "page schema. ALWAYS call this BEFORE creating a form in the chat to ensure "
        "fields match the actual cadastro. "
        "Params: page_key (str) — e.g. 'operation_natures' or 'products_form'."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "page_key": {
                "type": "string",
                "description": "Page key of the entity form (e.g. 'products_form', 'operation_natures')",
            },
        },
        "required": ["page_key"],
    },
)
