"""Seed data for agent skills.

Inserts metadata for all built-in skills into the ``skills`` table.
Each record stores the description and params_schema that the LLM
and admin UI consume.  The actual Python implementation remains in
``application/agent/skills/``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.sqlalchemy.models import SkillModel

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

# ── Built-in skill definitions ──────────────────────────────────────

BUILTIN_SKILLS: list[dict[str, Any]] = [
    {
        "name": "create_entity",
        "description": (
            "Create a new record in any entity table (products, clients, etc). "
            "Use this after the user fills a form to persist the data. "
            "Params: entity_key (str, e.g. 'products'), data (dict of field values)."
        ),
        "category": "crud",
        "params_schema": {
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
    },
    {
        "name": "update_entity",
        "description": (
            "Update an existing record in any entity table (products, clients, etc). "
            "Supports partial updates — only specified fields are changed. "
            "Params: entity_key (str), id (str), data (dict of fields to update)."
        ),
        "category": "crud",
        "params_schema": {
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
    },
    {
        "name": "delete_entity",
        "description": (
            "Delete a record from any entity table (products, clients, etc). "
            "IMPORTANT: Always confirm with the user before deleting. "
            "Params: entity_key (str), id (str)."
        ),
        "category": "crud",
        "params_schema": {
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
    },
    {
        "name": "list_entities",
        "description": (
            "List/search records from any entity table (products, clients, etc). "
            "Use this to see existing data, answer questions about records, "
            "or verify data before updates. "
            "Params: entity_key (str), limit (int, optional), offset (int, optional), "
            "filters (list of {field, operator, value}, optional)."
        ),
        "category": "crud",
        "params_schema": {
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
    },
    {
        "name": "classify_ncm",
        "description": (
            "Search the NCM catalog for codes matching a product CATEGORY. "
            "The category should be a TIPI classification term in Portuguese "
            "(e.g., 'refrigerante', 'cerveja', 'queijo', 'carne bovina', "
            "'calçado', 'smartphone'). Returns up to max_results candidates "
            "with codigo and descricao. The LLM must infer the category "
            "from the product description before calling this skill."
        ),
        "category": "fiscal",
        "params_schema": {
            "type": "object",
            "properties": {
                "categoria": {
                    "type": "string",
                    "description": (
                        "Product category in Portuguese for NCM search "
                        "(e.g., 'refrigerante', 'cerveja', 'carne bovina')"
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["categoria"],
        },
    },
    {
        "name": "fetch_by_ean",
        "description": (
            "Look up product data (name, brand, description, photo URL) "
            "by EAN/GTIN barcode using the Open Food Facts public API."
        ),
        "category": "search",
        "params_schema": {
            "type": "object",
            "properties": {
                "ean": {
                    "type": "string",
                    "description": "EAN/GTIN barcode (8 or 13 digits)",
                },
            },
            "required": ["ean"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for external information using DuckDuckGo. "
            "Use when you need data not available in the local database: "
            "product details, NCM codes, market prices, regulations, "
            "or any other publicly available information."
        ),
        "category": "search",
        "params_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query in natural language",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max number of results to return (default: 3)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "alter_page_schema",
        "description": (
            "Modify a page's layout/schema. Can change page title, description, "
            "add/remove fields and columns, AND update individual component properties "
            "using their ID (e.g. change a stat card's label or value). "
            "ALWAYS creates a new DRAFT version — never modifies the published version. "
            "After creating the draft, ask the user to confirm before publishing. "
            "IMPORTANT: When the user wants to modify a specific widget/component, "
            "use update_components with the component ID from the schema. "
            "Params: page_key (str), changes (dict)."
        ),
        "category": "admin",
        "params_schema": {
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
                        "update_components: [{id, ...props}], "
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
    },
    {
        "name": "publish_page_version",
        "description": (
            "Publish a draft page version, making it the active schema. "
            "The previous published version is automatically archived. "
            "ALWAYS ask the user for confirmation before publishing. "
            "Params: version_id (str — the draft to publish)."
        ),
        "category": "admin",
        "params_schema": {
            "type": "object",
            "properties": {
                "version_id": {
                    "type": "string",
                    "description": "ID of the draft version to publish",
                },
            },
            "required": ["version_id"],
        },
    },
    {
        "name": "rollback_page_version",
        "description": (
            "Rollback a page schema to a previous version. "
            "If no target_version is specified, rolls back to the most recent archived version. "
            "Params: page_key (str), target_version (int, optional)."
        ),
        "category": "admin",
        "params_schema": {
            "type": "object",
            "properties": {
                "page_key": {
                    "type": "string",
                    "description": "Page key to rollback (e.g. 'products')",
                },
                "target_version": {
                    "type": "integer",
                    "description": "Version number to restore (optional, defaults to most recent archived)",
                },
            },
            "required": ["page_key"],
        },
    },
]


def seed_skills(session: Session, tenant_id: str = DEFAULT_TENANT_ID) -> int:
    """Seed built-in skills for a tenant. Returns count of new records."""
    created = 0
    now = datetime.now(timezone.utc)

    for skill_def in BUILTIN_SKILLS:
        # Check if already exists for this tenant
        stmt = select(SkillModel).where(
            SkillModel.tenant_id == tenant_id,
            SkillModel.name == skill_def["name"],
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            continue

        skill = SkillModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=skill_def["name"],
            description=skill_def["description"],
            params_schema=skill_def["params_schema"],
            category=skill_def["category"],
            enabled=True,
            version=1,
            created_at=now,
            updated_at=now,
        )
        session.add(skill)
        created += 1

    return created
