"""Skill Registry — singleton registry for agent skills.

Skills self-register by calling ``register()`` at import time.
The orchestrator discovers available skills via ``list_skills()``.

Every skill must follow the standard contract::

    async def skill_name(params: dict, context: dict) -> dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

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
    """Return metadata for all registered skills."""
    return [
        {
            "name": entry.name,
            "description": entry.description,
            "params_schema": entry.params_schema,
        }
        for entry in _registry.values()
    ]
