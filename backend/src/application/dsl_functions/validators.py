"""DSL Validators — field-level validation based on schema declarations.

Reads validation rules from each field in ``dataSource.fields`` and
checks the incoming data before persistence.  Two formats are supported:

1. **Inline shorthand** — ``"required": true`` on the field definition.
2. **Explicit rules** — ``"validations": [{...}]`` array on the field.

Supported rules
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Rule
     - Params
     - Example
   * - ``required``
     - —
     - ``{"rule": "required"}``
   * - ``minLength``
     - ``value``
     - ``{"rule": "minLength", "value": 2}``
   * - ``maxLength``
     - ``value``
     - ``{"rule": "maxLength", "value": 14}``
   * - ``min``
     - ``value``
     - ``{"rule": "min", "value": 0}``
   * - ``max``
     - ``value``
     - ``{"rule": "max", "value": 100}``
   * - ``pattern``
     - ``value``, optional ``message``
     - ``{"rule": "pattern", "value": "^[0-9]{4}$"}``

Context
~~~~~~~

``validate_data()`` accepts a ``context`` argument (``"create"`` or
``"update"``).  The ``required`` rule **only fires on create** — in an
update, a missing field simply means "don't change it".
"""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Raised when one or more fields fail validation.

    Carries a list of ``{"field": ..., "rule": ..., "message": ...}``
    dicts ready for the standardised error response.
    """

    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        summary = "; ".join(
            f"{e['field']}: {e['message']}" for e in errors[:5]
        )
        super().__init__(f"Validation failed — {summary}")


# ── Rule implementations ─────────────────────────────────────────────


def _check_required(
    value: Any,
    _params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return f"{label} is required"
    return None


def _check_min_length(
    value: Any,
    params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    min_len = params.get("value", 0)
    if isinstance(value, str) and len(value) < min_len:
        return f"{label} must be at least {min_len} characters"
    return None


def _check_max_length(
    value: Any,
    params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    max_len = params.get("value", 0)
    if isinstance(value, str) and len(value) > max_len:
        return f"{label} must be at most {max_len} characters"
    return None


def _check_min(
    value: Any,
    params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    min_val = params.get("value", 0)
    try:
        if float(value) < float(min_val):
            return f"{label} must be at least {min_val}"
    except (ValueError, TypeError):
        pass
    return None


def _check_max(
    value: Any,
    params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    max_val = params.get("value", 0)
    try:
        if float(value) > float(max_val):
            return f"{label} must be at most {max_val}"
    except (ValueError, TypeError):
        pass
    return None


def _check_pattern(
    value: Any,
    params: dict[str, Any],
    field_id: str,
    label: str,
) -> str | None:
    pattern = params.get("value", "")
    custom_msg = params.get("message")
    if isinstance(value, str) and pattern:
        if not re.match(pattern, value):
            return custom_msg or f"{label} does not match the required format"
    return None


_RULE_MAP = {
    "required": _check_required,
    "minLength": _check_min_length,
    "maxLength": _check_max_length,
    "min": _check_min,
    "max": _check_max,
    "pattern": _check_pattern,
}


# ── Public API ───────────────────────────────────────────────────────


def validate_data(
    data: dict[str, Any],
    schema: dict[str, Any],
    context: str = "create",
) -> None:
    """Validate ``data`` against the field definitions in ``schema``.

    Args:
        data: the request body dict to validate.
        schema: the full page schema (with ``dataSource.fields``).
        context: ``"create"`` or ``"update"``.

    Raises:
        ValidationError: if one or more fields fail validation.
    """
    fields = schema.get("dataSource", {}).get("fields", [])
    errors: list[dict[str, str]] = []

    for field_def in fields:
        field_id = field_def.get("id")
        if not field_id:
            continue

        label = field_def.get("label", field_id)
        value = data.get(field_id)

        # Build the validation rules list for this field
        rules = list(field_def.get("validations", []))

        # Honour inline "required": true as shorthand
        if field_def.get("required") is True:
            # Only add if not already declared explicitly
            if not any(r.get("rule") == "required" for r in rules):
                rules.insert(0, {"rule": "required"})

        for rule_def in rules:
            rule_name = rule_def.get("rule", "")
            checker = _RULE_MAP.get(rule_name)
            if checker is None:
                continue

            # required only fires on create — in update, missing = "don't change"
            if rule_name == "required" and context == "update":
                if field_id not in data:
                    continue

            # Skip validation for absent fields in update (partial update)
            if context == "update" and field_id not in data:
                continue

            msg = checker(value, rule_def, field_id, label)
            if msg:
                errors.append({
                    "field": field_id,
                    "rule": rule_name,
                    "message": msg,
                })

    if errors:
        raise ValidationError(errors)
