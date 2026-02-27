"""Generic CRUD repository — operates on any SQLAlchemy table dynamically.

Uses SQLAlchemy Core (Table + metadata) instead of ORM queries, so it can
work with ANY registered table without needing a dedicated repository class.

Supports optimistic locking via an optional ``version`` column. If a table
has a ``version INTEGER`` column, updates will check the expected version
and increment it atomically. A mismatch raises ``StaleDataError``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from src.infrastructure.persistence.sqlalchemy.models import Base


class StaleDataError(Exception):
    """Raised when an update conflicts due to a version mismatch.

    This indicates another transaction modified the row between the
    read and the write (optimistic locking violation).
    """

    def __init__(self, entity_id: str, expected_version: int) -> None:
        self.entity_id = entity_id
        self.expected_version = expected_version
        super().__init__(
            f"Conflict: entity {entity_id} was modified by another request "
            f"(expected version {expected_version})"
        )


class GenericCrudRepository:
    """Performs CRUD on any table registered in Base.metadata."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_table(self, table_name: str):
        """Resolve a SQLAlchemy Table from metadata by name."""
        table = Base.metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"Table '{table_name}' not found in metadata")
        return table

    def _has_version(self, table) -> bool:
        """Check if a table has a version column for optimistic locking."""
        return "version" in table.c

    def list(
        self,
        table_name: str,
        tenant_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Return paginated rows for a tenant."""
        table = self._get_table(table_name)

        # Count
        count_q = (
            select(func.count())
            .select_from(table)
            .where(table.c.tenant_id == tenant_id)
        )
        total = self.db.execute(count_q).scalar() or 0

        # Data
        data_q = (
            select(table)
            .where(table.c.tenant_id == tenant_id)
            .order_by(table.c.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = self.db.execute(data_q).mappings().all()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_by_id(
        self,
        table_name: str,
        tenant_id: str,
        entity_id: str,
    ) -> dict[str, Any] | None:
        """Return a single row by ID for a tenant."""
        table = self._get_table(table_name)
        row = self.db.execute(
            select(table)
            .where(table.c.id == entity_id)
            .where(table.c.tenant_id == tenant_id)
        ).mappings().first()
        return dict(row) if row else None

    def create(
        self,
        table_name: str,
        tenant_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Insert a new row and return it."""
        table = self._get_table(table_name)
        now = datetime.now(timezone.utc)

        row_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": now,
            "updated_at": now,
            **data,
        }

        # Set initial version for tables with optimistic locking
        if self._has_version(table) and "version" not in row_data:
            row_data["version"] = 1

        self.db.execute(insert(table).values(**row_data))
        return row_data

    def update(
        self,
        table_name: str,
        tenant_id: str,
        entity_id: str,
        data: dict[str, Any],
        expected_version: int | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing row with optimistic locking.

        If the table has a ``version`` column and ``expected_version`` is
        provided, the update will only succeed if the current row version
        matches. On success the version is incremented atomically.

        Raises:
            StaleDataError: if version mismatch (409 Conflict scenario).

        Returns:
            Updated row dict, or None if entity not found.
        """
        table = self._get_table(table_name)
        has_ver = self._has_version(table)

        # Filter out None values and internal keys (partial update)
        updates = {k: v for k, v in data.items() if v is not None}
        updates.pop("_version", None)  # Never persist the client hint
        updates["updated_at"] = datetime.now(timezone.utc)

        # Build WHERE clause
        stmt = (
            update(table)
            .where(table.c.id == entity_id)
            .where(table.c.tenant_id == tenant_id)
        )

        # Optimistic lock: check version + increment
        if has_ver and expected_version is not None:
            stmt = stmt.where(table.c.version == expected_version)
            updates["version"] = expected_version + 1
        elif has_ver:
            # No expected_version provided but table has version column:
            # still increment to keep the counter moving
            updates["version"] = table.c.version + 1

        stmt = stmt.values(**updates)
        result = self.db.execute(stmt)

        if result.rowcount == 0:
            # Distinguish "not found" from "version conflict"
            if has_ver and expected_version is not None:
                # Check if the row exists at all
                exists = self.db.execute(
                    select(func.count())
                    .select_from(table)
                    .where(table.c.id == entity_id)
                    .where(table.c.tenant_id == tenant_id)
                ).scalar()
                if exists:
                    raise StaleDataError(entity_id, expected_version)
            return None

        # Return the updated row
        row = self.db.execute(
            select(table)
            .where(table.c.id == entity_id)
            .where(table.c.tenant_id == tenant_id)
        ).mappings().first()

        return dict(row) if row else None

    def delete(
        self,
        table_name: str,
        tenant_id: str,
        entity_id: str,
    ) -> bool:
        """Delete a row. Returns True if deleted."""
        table = self._get_table(table_name)

        stmt = (
            delete(table)
            .where(table.c.id == entity_id)
            .where(table.c.tenant_id == tenant_id)
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0

