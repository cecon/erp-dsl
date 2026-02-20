"""Generic CRUD repository — operates on any SQLAlchemy table dynamically.

Uses SQLAlchemy Core (Table + metadata) instead of ORM queries, so it can
work with ANY registered table without needing a dedicated repository class.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from src.infrastructure.persistence.sqlalchemy.models import Base


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

        self.db.execute(insert(table).values(**row_data))
        return row_data

    def update(
        self,
        table_name: str,
        tenant_id: str,
        entity_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update an existing row. Returns updated data or None."""
        table = self._get_table(table_name)

        # Filter out None values (partial update)
        updates = {k: v for k, v in data.items() if v is not None}
        updates["updated_at"] = datetime.now(timezone.utc)

        stmt = (
            update(table)
            .where(table.c.id == entity_id)
            .where(table.c.tenant_id == tenant_id)
            .values(**updates)
        )
        result = self.db.execute(stmt)

        if result.rowcount == 0:
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
