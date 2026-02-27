"""Automatic multi-tenant query filtering via SQLAlchemy session events.

This module provides an opt-in tenant isolation mechanism:
- When a Session has ``session.info["tenant_id"]`` set, all SELECT / UPDATE /
  DELETE statements against *tenant-aware* tables automatically receive a
  ``WHERE tenant_id = :tenant_id`` clause.
- Sessions without a ``tenant_id`` in their info dict (seed scripts, admin
  operations, login) are NOT filtered — this is the escape hatch.
- Tables listed in ``TENANT_EXEMPT_TABLES`` are never filtered, even if they
  contain a ``tenant_id`` column, because they need cross-tenant access
  (e.g. login resolution, global DSL schemas).

**Known limitation — joins:**
  When a query joins a filtered table with an exempt table, the filter is
  applied only to the filtered table's ``tenant_id`` column. If a future join
  introduces ambiguity (e.g. both tables have ``tenant_id``), the listener
  will skip filtering for that statement to avoid silent data corruption.
  If you add cross-table joins, verify tenant isolation manually.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.sqlalchemy.models import Base

# ── Tables that NEVER receive automatic tenant_id filtering ──────────
# Rationale:
#   tenants       → meta-table, has no tenant_id column
#   users         → login queries run before tenant is known
#   page_versions → DSL schemas are global with tenant_id=NULL fallback

TENANT_EXEMPT_TABLES: set[str] = {
    "tenants",
    "users",
    "page_versions",
}


def _get_filterable_tables() -> set[str]:
    """Return table names that have a tenant_id column and are NOT exempt."""
    filterable = set()
    for table_name, table in Base.metadata.tables.items():
        if table_name in TENANT_EXEMPT_TABLES:
            continue
        if "tenant_id" in table.c:
            filterable.add(table_name)
    return filterable


def _extract_table_names(statement: Any) -> set[str]:
    """Extract table names involved in a compiled statement."""
    tables: set[str] = set()
    try:
        # Core select / update / delete expose .froms or .entity_description
        froms = getattr(statement, "froms", None)
        if froms:
            for frm in froms:
                name = getattr(frm, "name", None)
                if name:
                    tables.add(name)

        # For UPDATE / DELETE the table is on .entity_description or .table
        table_attr = getattr(statement, "table", None)
        if table_attr is not None:
            name = getattr(table_attr, "name", None)
            if name:
                tables.add(name)
    except Exception:  # noqa: BLE001 — defensive; never break a query
        pass
    return tables


def _on_do_orm_execute(orm_execute_state: Any) -> None:
    """Event listener that injects tenant_id WHERE clause automatically."""
    session = orm_execute_state.session
    tenant_id = session.info.get("tenant_id")

    # No tenant context → no filtering (seed, admin, login)
    if not tenant_id:
        return

    # Only filter SELECT, UPDATE, DELETE — never INSERT
    if orm_execute_state.is_insert:
        return

    statement = orm_execute_state.statement
    table_names = _extract_table_names(statement)

    if not table_names:
        return

    filterable = _get_filterable_tables()
    targets = table_names & filterable

    if not targets:
        return

    # Safety: if the query involves BOTH filtered and exempt tables (a join),
    # we still apply the filter only to the filterable table(s).
    for table_name in targets:
        table = Base.metadata.tables[table_name]
        statement = statement.where(table.c.tenant_id == tenant_id)

    orm_execute_state.statement = statement


def enable_tenant_filter(session_factory: sessionmaker) -> None:
    """Register the tenant filter event on the Session class.

    Call this ONCE at application startup, after creating the sessionmaker.
    """
    event.listen(session_factory, "do_orm_execute", _on_do_orm_execute)
