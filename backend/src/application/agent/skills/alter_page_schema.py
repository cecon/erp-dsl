"""Skill: alter_page_schema — modify a page's DSL schema with auto-versioning.

Creates a NEW draft version with the requested changes, preserving the
current published version for rollback.  The draft must be explicitly
published (via ``publish_page_version``) to take effect.

Contract: async def alter_page_schema(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime, timezone

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

logger = logging.getLogger(__name__)


def _find_component_by_id(components: list, target_id: str) -> dict | None:
    """Recursively find a component by its ID in a nested component tree."""
    for comp in components:
        if comp.get("id") == target_id:
            return comp
        # Search in nested components
        nested = comp.get("components", [])
        if nested:
            found = _find_component_by_id(nested, target_id)
            if found:
                return found
        # Search in items (for activity_feed, quick_actions, etc.)
        items = comp.get("items", [])
        if items:
            found = _find_component_by_id(items, target_id)
            if found:
                return found
    return None


def _list_all_components(components: list, prefix: str = "") -> list[dict]:
    """Flatten the component tree into a list with path info."""
    result = []
    for comp in components:
        comp_id = comp.get("id", "?")
        comp_type = comp.get("type", "?")
        label = comp.get("label", comp.get("text", ""))
        path = f"{prefix}/{comp_id}" if prefix else comp_id

        result.append({
            "id": comp_id,
            "type": comp_type,
            "label": label,
            "path": path,
        })

        # Recurse into nested components
        for child_key in ("components", "items"):
            children = comp.get(child_key, [])
            if children:
                result.extend(_list_all_components(children, path))
    return result


def _apply_changes(schema: dict, changes: dict) -> tuple[dict, list[str]]:
    """Apply requested changes to a schema copy.

    Supported change keys:
        add_fields: [{id, type, label, ...}]
        remove_fields: [field_id, ...]
        add_columns: [{key, label, ...}]
        remove_columns: [column_key, ...]
        update_title: str
        update_description: str
        update_components: [{id, ...props_to_update}]

    Returns:
        (modified_schema, list_of_change_descriptions)
    """
    descriptions: list[str] = []

    # ── Title / Description ──────────────────────────────────────
    if "update_title" in changes:
        schema["title"] = changes["update_title"]
        descriptions.append(f"Título alterado para '{changes['update_title']}'")

    if "update_description" in changes:
        schema["description"] = changes["update_description"]
        descriptions.append("Descrição atualizada")

    # ── Update specific components by ID ─────────────────────────
    if changes.get("update_components"):
        all_components = schema.get("components", [])
        for update in changes["update_components"]:
            target_id = update.get("id")
            if not target_id:
                continue
            comp = _find_component_by_id(all_components, target_id)
            if comp is None:
                descriptions.append(f"⚠️ Componente '{target_id}' não encontrado")
                continue
            # Apply all properties except 'id'
            changed_props = []
            for key, value in update.items():
                if key == "id":
                    continue
                old_value = comp.get(key)
                comp[key] = value
                changed_props.append(f"{key}: '{old_value}' → '{value}'")
            if changed_props:
                label = comp.get("label", target_id)
                descriptions.append(
                    f"Componente '{label}' (id={target_id}) atualizado: "
                    + ", ".join(changed_props)
                )

    # ── Fields (inside form component) ───────────────────────────
    form_comp = None
    for comp in schema.get("components", []):
        if comp.get("type") == "form":
            form_comp = comp
            break

    if form_comp is None and (changes.get("add_fields") or changes.get("remove_fields")):
        # Create a form component if none exists
        form_comp = {"type": "form", "components": []}
        schema.setdefault("components", []).append(form_comp)

    if changes.get("add_fields"):
        for field in changes["add_fields"]:
            if not field.get("id"):
                continue
            form_comp.setdefault("components", []).append(field)
            descriptions.append(f"Campo '{field.get('label', field['id'])}' adicionado")

    if changes.get("remove_fields"):
        if form_comp and form_comp.get("components"):
            ids_to_remove = set(changes["remove_fields"])
            original_count = len(form_comp["components"])
            form_comp["components"] = [
                f for f in form_comp["components"]
                if f.get("id") not in ids_to_remove
            ]
            removed = original_count - len(form_comp["components"])
            if removed:
                descriptions.append(f"{removed} campo(s) removido(s)")

    # ── Columns ──────────────────────────────────────────────────
    if changes.get("add_columns"):
        cols = schema.setdefault("columns", [])
        for col in changes["add_columns"]:
            if not col.get("key"):
                continue
            cols.append(col)
            descriptions.append(f"Coluna '{col.get('label', col['key'])}' adicionada")

    if changes.get("remove_columns"):
        if schema.get("columns"):
            keys_to_remove = set(changes["remove_columns"])
            original_count = len(schema["columns"])
            schema["columns"] = [
                c for c in schema["columns"]
                if c.get("key") not in keys_to_remove
            ]
            removed = original_count - len(schema["columns"])
            if removed:
                descriptions.append(f"{removed} coluna(s) removida(s)")

    return schema, descriptions


async def alter_page_schema(params: dict, context: dict) -> dict:
    """Alter a page schema by creating a new draft version.

    Args:
        params:
            - page_key (str): the page to modify
            - changes (dict): changes to apply (see _apply_changes)
        context: Must contain ``db`` and ``tenant_id``.

    Returns:
        dict with the new version info, changes made, and version_id.
    """
    page_key = params.get("page_key", "").strip()
    changes = params.get("changes", {})

    if not page_key:
        return {"error": "page_key is required"}
    if not changes:
        return {"error": "changes dict is required"}

    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or not tenant_id:
        return {"error": "No database session or tenant_id in context"}

    # Find current published version
    current = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == page_key,
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version_number.desc())
        .first()
    )

    if current is None:
        return {"error": f"No published schema found for '{page_key}'"}

    # Copy schema and apply changes
    new_schema = copy.deepcopy(current.schema_json or {})
    modified_schema, change_descriptions = _apply_changes(new_schema, changes)

    if not change_descriptions:
        return {"error": "No valid changes were applied"}

    # Get latest version number (including drafts)
    latest_num = (
        db.query(PageVersionModel.version_number)
        .filter(PageVersionModel.page_key == page_key)
        .order_by(PageVersionModel.version_number.desc())
        .limit(1)
        .scalar()
    ) or current.version_number

    # Create new draft version
    now = datetime.now(timezone.utc)
    new_version = PageVersionModel(
        id=str(uuid.uuid4()),
        page_key=page_key,
        scope=current.scope,
        tenant_id=current.tenant_id,
        base_version_id=current.id,
        version_number=latest_num + 1,
        schema_json=modified_schema,
        status="draft",
        created_at=now,
        updated_at=now,
    )
    db.add(new_version)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("alter_page_schema failed: %s", exc)
        return {"error": str(exc)}

    return {
        "success": True,
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "base_version_id": current.id,
        "changes_applied": change_descriptions,
        "message": (
            f"Draft v{new_version.version_number} criado com {len(change_descriptions)} alteração(ões). "
            "Use 'publish_page_version' para publicar ou descarte para manter a versão atual."
        ),
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="alter_page_schema",
    fn=alter_page_schema,
    description=(
        "Modify a page's layout/schema. Can change page title, description, "
        "add/remove fields and columns, AND update individual component properties "
        "using their ID (e.g. change a stat card's label or value). "
        "ALWAYS creates a new DRAFT version — never modifies the published version. "
        "After creating the draft, ask the user to confirm before publishing. "
        "IMPORTANT: When the user wants to modify a specific widget/component, "
        "use update_components with the component ID from the schema. "
        "Example: to change 'Total Revenue' label on stat-revenue card, use: "
        "changes: {update_components: [{id: 'stat-revenue', label: 'Receita Total'}]}. "
        "Params: page_key (str), changes (dict)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "page_key": {
                "type": "string",
                "description": "Page key to modify (e.g. 'products', 'dashboard')",
            },
            "changes": {
                "type": "object",
                "description": (
                    "Changes to apply. Available keys: "
                    "update_components: [{id, ...props}] — modify specific components by ID, "
                    "add_fields: [{id, type, label}], "
                    "remove_fields: [field_id], "
                    "add_columns: [{key, label}], "
                    "remove_columns: [col_key], "
                    "update_title: str, "
                    "update_description: str"
                ),
            },
        },
        "required": ["page_key", "changes"],
    },
)

