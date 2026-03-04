"""Skill Registry — singleton registry for agent skills.

Skills self-register by calling ``register()`` at import time.
The orchestrator discovers available skills via ``list_skills()``
or ``list_skills_for_tenant()`` (DB-aware, respects enabled flag).

Every skill must follow the standard contract::

    async def skill_name(params: dict, context: dict) -> dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from sqlalchemy import select
from sqlalchemy.orm import Session

# Type alias for skill functions
SkillFn = Callable[[dict, dict], Coroutine[Any, Any, dict]]


@dataclass
class SkillEntry:
    """Metadata for a registered skill."""

    name: str
    fn: SkillFn
    description: str
    params_schema: dict = field(default_factory=dict)


# Module-level singleton registry
_registry: dict[str, SkillEntry] = {}


def register(
    name: str,
    fn: SkillFn,
    description: str,
    params_schema: dict | None = None,
) -> None:
    """Register a skill function under the given name."""
    _registry[name] = SkillEntry(
        name=name,
        fn=fn,
        description=description,
        params_schema=params_schema or {},
    )


def get(name: str) -> SkillFn | None:
    """Return the callable for a registered skill, or None."""
    entry = _registry.get(name)
    return entry.fn if entry else None


def list_skills() -> list[dict]:
    """Return metadata for all registered skills (in-memory only)."""
    return [
        {
            "name": entry.name,
            "description": entry.description,
            "params_schema": entry.params_schema,
        }
        for entry in _registry.values()
    ]


def list_skills_for_tenant(db: Session, tenant_id: str) -> list[dict]:
    """Return skills that have BOTH a DB record (enabled) AND code implementation.

    Uses description and params_schema from the **database** (editable),
    but only includes skills that exist in the in-memory registry (have code).
    """
    from src.infrastructure.persistence.sqlalchemy.models import SkillModel

    stmt = select(SkillModel).where(
        SkillModel.tenant_id == tenant_id,
        SkillModel.enabled == True,  # noqa: E712
    )
    db_skills = db.execute(stmt).scalars().all()

    result = []
    for db_skill in db_skills:
        # Only include if there is a matching code implementation
        if db_skill.name not in _registry:
            continue
        result.append({
            "name": db_skill.name,
            "description": db_skill.description,
            "params_schema": db_skill.params_schema or {},
            "category": db_skill.category,
        })

    return result


def get_skill_entry(db: Session, tenant_id: str, name: str) -> dict | None:
    """Get a single skill's metadata from DB, only if it has code and is enabled."""
    from src.infrastructure.persistence.sqlalchemy.models import SkillModel

    if name not in _registry:
        return None

    stmt = select(SkillModel).where(
        SkillModel.tenant_id == tenant_id,
        SkillModel.name == name,
        SkillModel.enabled == True,  # noqa: E712
    )
    db_skill = db.execute(stmt).scalar_one_or_none()
    if db_skill is None:
        return None

    return {
        "name": db_skill.name,
        "description": db_skill.description,
        "params_schema": db_skill.params_schema or {},
        "category": db_skill.category,
    }

