"""Pipeline Runner — applies DSL-declared transforms to field data.

Reads the `transforms` array from each field in the schema's
dataSource.fields and applies the matching registered functions.
"""

from __future__ import annotations

import logging
from typing import Any

from src.application.dsl_functions.registry import function_registry

logger = logging.getLogger(__name__)


def _get_field_transforms(
    schema: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract all fields that have transforms declared."""
    fields = schema.get("dataSource", {}).get("fields", [])
    return [f for f in fields if f.get("transforms")]


def _should_run(transform: dict[str, Any], phase: str) -> bool:
    """Check if a transform should run in the given phase."""
    on = transform.get("on", "request")
    return on == phase or on == "both"


def run_request_pipeline(
    data: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Apply all 'on=request' transforms to the data before saving."""
    return _run_pipeline(data, schema, "request")


def run_response_pipeline(
    data: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Apply all 'on=response' transforms to the data before returning."""
    return _run_pipeline(data, schema, "response")


def _run_pipeline(
    data: dict[str, Any],
    schema: dict[str, Any],
    phase: str,
) -> dict[str, Any]:
    """Internal: iterate fields with transforms, apply matching ones."""
    fields_with_transforms = _get_field_transforms(schema)
    result = dict(data)

    for field_def in fields_with_transforms:
        field_id = field_def["id"]
        if field_id not in result:
            continue

        for transform in field_def["transforms"]:
            if not _should_run(transform, phase):
                continue

            fn_name = transform.get("fn", "")
            fn = function_registry.get(fn_name)
            if fn is None:
                logger.warning(
                    "Transform function '%s' not found for field '%s'",
                    fn_name,
                    field_id,
                )
                continue

            try:
                result[field_id] = fn(result[field_id])
            except Exception:
                logger.exception(
                    "Error running transform '%s' on field '%s'",
                    fn_name,
                    field_id,
                )

    return result
