"""Workflow domain entity — pure Python, no framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class WorkflowStatus(str, Enum):
    """Allowed lifecycle states for a workflow."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class WorkflowStep:
    """Single step inside a workflow pipeline."""

    skill: str
    params: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    on_error: Literal["stop", "continue", "ask"] = "stop"


@dataclass
class Workflow:
    """Workflow aggregate root.

    A workflow is a named sequence of skill invocations that can be
    triggered via a ``/command`` in the Otto chat.
    """

    id: str
    tenant_id: str
    name: str
    command: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1

    # ── Domain validation ───────────────────────────────────────

    def validate_for_publish(self) -> list[str]:
        """Return a list of validation errors (empty = valid)."""
        errors: list[str] = []
        if not self.command.startswith("/"):
            errors.append("Command must start with '/'.")
        if not self.steps:
            errors.append("A published workflow must have at least one step.")
        if not self.name.strip():
            errors.append("Workflow name cannot be empty.")
        return errors
