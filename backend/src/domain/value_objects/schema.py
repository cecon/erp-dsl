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

# Whitelisted component types
_ALLOWED_COMPONENT_TYPES = {
    "text", "number", "money", "select", "checkbox", "date",
    "textarea", "grid", "form", "section", "heading", "divider",
    "button", "hidden",
}

# Keys that could indicate code execution attempts
_FORBIDDEN_PATTERNS = {
    "eval", "exec", "import", "__", "function", "script",
    "onclick", "onload", "onerror", "javascript:",
}


def _validate_no_code_injection(obj: Any, path: str = "$") -> None:
    """Recursively check that no value contains code-injection patterns."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            lower_key = key.lower()
            for forbidden in _FORBIDDEN_PATTERNS:
                if forbidden in lower_key:
                    raise ValueError(
                        f"Forbidden key '{key}' at {path}.{key}"
                    )
            _validate_no_code_injection(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _validate_no_code_injection(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        lower_val = obj.lower()
        for forbidden in _FORBIDDEN_PATTERNS:
            if forbidden in lower_val:
                raise ValueError(
                    f"Forbidden value pattern '{forbidden}' at {path}"
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
