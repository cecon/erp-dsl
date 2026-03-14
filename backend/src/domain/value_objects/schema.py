"""Value object for validated page schemas.

Ensures JSON schemas do not contain arbitrary code execution vectors.
Only whitelisted keys and component types are allowed.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


# Whitelisted top-level keys in a page schema
_ALLOWED_TOP_KEYS = {
    "title", "description", "layout", "components", "actions", "columns",
    "filters", "defaultValues", "validations", "metadata", "dataSource",
}

# Whitelisted component types — all DSL node types across all schemas
_ALLOWED_COMPONENT_TYPES = {
    # ── Inputs ────────────────────────────────────────────────────
    "text", "number", "money", "select", "checkbox", "date", "datetime",
    "textarea", "hidden", "color_swatch_picker", "theme_switch", "segmented",
    "workflow_step_editor",
    # ── Layout ────────────────────────────────────────────────────
    "form", "grid", "section", "tabs", "tab", "heading", "divider",
    # ── Actions ───────────────────────────────────────────────────
    "button", "submit", "cancel",
    # ── Dashboard widgets ─────────────────────────────────────────
    "stats_grid", "stat_card", "activity_feed", "quick_actions",
    # ── Agent / special ───────────────────────────────────────────
    "agent",
}

# Precise patterns for actual code injection — avoids false positives
# like "description" matching "script" or "import" matching field names.
import re as _re

_FORBIDDEN_REGEXES = [
    _re.compile(r"<script", _re.IGNORECASE),
    _re.compile(r"javascript\s*:", _re.IGNORECASE),
    _re.compile(r"\beval\s*\("),
    _re.compile(r"\bexec\s*\("),
    _re.compile(r"__[a-z]+__"),
    _re.compile(r"\bon(click|load|error|mouseover|submit|focus|blur)\b", _re.IGNORECASE),
]


def _validate_no_code_injection(obj: Any, path: str = "$") -> None:
    """Recursively check that no value contains code-injection patterns."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            for pattern in _FORBIDDEN_REGEXES:
                if pattern.search(str(key)):
                    raise ValueError(
                        f"Forbidden key pattern at {path}.{key}"
                    )
            _validate_no_code_injection(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _validate_no_code_injection(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        for pattern in _FORBIDDEN_REGEXES:
            if pattern.search(obj):
                raise ValueError(
                    f"Forbidden value pattern at {path}: {obj[:60]!r}"
                )


def _validate_components(components: list[dict[str, Any]]) -> None:
    """Validate that all component types are whitelisted."""
    for i, comp in enumerate(components):
        comp_type = comp.get("type", "")
        if comp_type and comp_type not in _ALLOWED_COMPONENT_TYPES:
            raise ValueError(
                f"Unknown component type '{comp_type}' at components[{i}]"
            )
        # Recurse into nested components
        nested = comp.get("components", [])
        if nested:
            _validate_components(nested)


@dataclass(frozen=True)
class PageSchema:
    """Immutable, validated page schema value object.

    Guarantees that the schema:
    - Contains only whitelisted top-level keys
    - Uses only allowed component types
    - Contains no code-injection patterns
    """

    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate top-level keys
        unknown_keys = set(self.data.keys()) - _ALLOWED_TOP_KEYS
        if unknown_keys:
            raise ValueError(f"Disallowed schema keys: {unknown_keys}")

        # Validate components
        components = self.data.get("components", [])
        if components:
            _validate_components(components)

        # Deep scan for code injection
        _validate_no_code_injection(self.data)

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self.data)
