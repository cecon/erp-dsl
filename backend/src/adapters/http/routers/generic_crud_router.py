"""Generic CRUD router — single router for all DSL-driven entities.

Resolves the target table from the page schema's dataSource.tableName,
then delegates all operations to GenericCrudRepository. This eliminates
the need for per-entity routers, use cases, and repositories.

DSL transforms declared in dataSource.fields[].transforms are
automatically applied via the pipeline runner.

Tenant isolation is handled automatically by the session-level
tenant filter (see tenant_context.py). The ``get_tenant_db``
dependency sets ``session.info["tenant_id"]`` so all SELECT / UPDATE /
DELETE queries are filtered. INSERT still receives tenant_id explicitly
via ``db.info["tenant_id"]``.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_tenant_db
from src.application.dsl_functions.pipeline_runner import (
    run_request_pipeline,
    run_response_pipeline,
)
from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    GenericCrudRepository,
    StaleDataError,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    Base,
    PageVersionModel,
)

router = APIRouter()


def _resolve_schema(
    db: Session, entity_name: str
) -> dict[str, Any]:
    """Fetch the published page schema for an entity.

    NOTE: ``page_versions`` is in TENANT_EXEMPT_TABLES, so this query
    is NOT filtered by tenant_id even when the session has tenant context.
    """
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
        raise HTTPException(
            status_code=404,
            detail=f"No published schema for '{entity_name}'",
        )
    return page.schema_json


def _get_table_name(schema: dict[str, Any], entity_name: str) -> str:
    """Extract tableName from dataSource, with fallback."""
    ds = schema.get("dataSource", {})
    table_name = ds.get("tableName", entity_name)
    if table_name not in Base.metadata.tables:
        raise HTTPException(
            status_code=404,
            detail=f"Table '{table_name}' not found",
        )
    return table_name


def _coerce_field(value: Any, db_type: str) -> Any:
    """Coerce a request value to the expected DB type."""
    if value is None or value == "":
        return value
    if db_type == "decimal":
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return Decimal("0")
    return value


def _coerce_data(
    data: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    """Coerce all fields in data dict based on schema field types."""
    fields = schema.get("dataSource", {}).get("fields", [])
    type_map = {f["id"]: f.get("dbType", "string") for f in fields}

    coerced = {}
    for key, value in data.items():
        db_type = type_map.get(key, "string")
        coerced[key] = _coerce_field(value, db_type)
    return coerced


def _apply_defaults(
    data: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    """Fill missing fields with their declared defaultValue from the schema."""
    fields = schema.get("dataSource", {}).get("fields", [])
    result = dict(data)
    for field in fields:
        field_id = field.get("id")
        if field_id and field_id not in result and "defaultValue" in field:
            result[field_id] = field["defaultValue"]
    return result


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert Decimal/datetime values to JSON-safe types."""
    result = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


# ── Endpoints ────────────────────────────────────────────────────


@router.get("/{entity_name}")
def list_entities(
    entity_name: str,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_tenant_db),
) -> dict[str, Any]:
    """List all rows for an entity (auto-filtered by tenant)."""
    schema = _resolve_schema(db, entity_name)
    table_name = _get_table_name(schema, entity_name)
    repo = GenericCrudRepository(db)
    tenant_id = db.info["tenant_id"]
    result = repo.list(table_name, tenant_id, offset, limit)
    result["items"] = [
        run_response_pipeline(_serialize_row(r), schema)
        for r in result["items"]
    ]
    return result


@router.get("/{entity_name}/{entity_id}")
def get_entity(
    entity_name: str,
    entity_id: str,
    db: Session = Depends(get_tenant_db),
) -> dict[str, Any]:
    """Get a single entity row by ID (auto-filtered by tenant)."""
    schema = _resolve_schema(db, entity_name)
    table_name = _get_table_name(schema, entity_name)
    repo = GenericCrudRepository(db)
    tenant_id = db.info["tenant_id"]
    result = repo.get_by_id(table_name, tenant_id, entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return run_response_pipeline(_serialize_row(result), schema)


@router.post("/{entity_name}")
def create_entity(
    entity_name: str,
    body: dict[str, Any],
    db: Session = Depends(get_tenant_db),
) -> dict[str, Any]:
    """Create a new row for an entity."""
    schema = _resolve_schema(db, entity_name)
    table_name = _get_table_name(schema, entity_name)
    data = _apply_defaults(body, schema)
    data = _coerce_data(data, schema)
    data = run_request_pipeline(data, schema)
    repo = GenericCrudRepository(db)
    tenant_id = db.info["tenant_id"]
    result = repo.create(table_name, tenant_id, data)
    db.commit()
    return run_response_pipeline(_serialize_row(result), schema)


@router.put("/{entity_name}/{entity_id}")
def update_entity(
    entity_name: str,
    entity_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_tenant_db),
) -> dict[str, Any]:
    """Update an existing entity row (auto-filtered by tenant).

    Supports optimistic locking: if the body contains ``_version``,
    the update will only succeed if the current row version matches.
    On conflict returns 409.
    """
    schema = _resolve_schema(db, entity_name)
    table_name = _get_table_name(schema, entity_name)

    # Extract version hint before coercion (not a DB field)
    expected_version: int | None = None
    if "_version" in body:
        try:
            expected_version = int(body.pop("_version"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="_version must be an integer",
            )

    data = _coerce_data(body, schema)
    data = run_request_pipeline(data, schema)
    repo = GenericCrudRepository(db)
    tenant_id = db.info["tenant_id"]

    # StaleDataError propagates to the global handler → 409 with details
    result = repo.update(
        table_name, tenant_id, entity_id, data,
        expected_version=expected_version,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.commit()
    return run_response_pipeline(_serialize_row(result), schema)


@router.delete("/{entity_name}/{entity_id}")
def delete_entity(
    entity_name: str,
    entity_id: str,
    db: Session = Depends(get_tenant_db),
) -> dict[str, str]:
    """Delete an entity row (auto-filtered by tenant)."""
    schema = _resolve_schema(db, entity_name)
    table_name = _get_table_name(schema, entity_name)
    repo = GenericCrudRepository(db)
    tenant_id = db.info["tenant_id"]
    deleted = repo.delete(table_name, tenant_id, entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.commit()
    return {"detail": f"{entity_name} deleted"}

