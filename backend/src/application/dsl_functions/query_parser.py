"""Query Parser — extracts filters and sort from HTTP query params.

Parses ``filter[field]=value`` and ``sort=field`` (or ``sort=-field``
for descending) from the request query string.  Validates filter fields
against a whitelist declared in the schema DSL.

Schema example::

    "dataSource": {
        "filters": [
            {"field": "uf_origem", "operator": "eq"},
            {"field": "icms_aliquota", "operator": "gte"}
        ],
        "defaultSort": "-created_at"
    }

Supported operators: ``eq``, ``neq``, ``gt``, ``gte``, ``lt``, ``lte``,
``like`` (case-insensitive ILIKE), ``in`` (comma-separated values).
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

# Regex for filter[field_name]=value
_FILTER_PATTERN = re.compile(r"^filter\[(\w+)\]$")


class ParsedQuery:
    """Holds parsed filters and sort directive."""

    __slots__ = ("filters", "sort_field", "sort_desc")

    def __init__(self) -> None:
        self.filters: list[dict[str, Any]] = []
        self.sort_field: str | None = None
        self.sort_desc: bool = False

    def __repr__(self) -> str:
        return (
            f"ParsedQuery(filters={self.filters}, "
            f"sort={'-' if self.sort_desc else ''}{self.sort_field})"
        )


def _get_allowed_filters(schema: dict[str, Any]) -> dict[str, str]:
    """Return {field_name: operator} from the schema's filter whitelist."""
    raw = schema.get("dataSource", {}).get("filters", [])
    return {f["field"]: f.get("operator", "eq") for f in raw if "field" in f}


def parse_query_params(
    query_params: dict[str, str],
    schema: dict[str, Any],
) -> ParsedQuery:
    """Parse and validate filter/sort from raw query params.

    Args:
        query_params: Raw query params dict (e.g. from ``request.query_params``).
        schema: The page schema for this entity.

    Returns:
        A ``ParsedQuery`` with validated filters and sort.

    Raises:
        HTTPException(400): if a filter field is not in the whitelist.
    """
    allowed = _get_allowed_filters(schema)
    result = ParsedQuery()

    for key, value in query_params.items():
        # Skip pagination params
        if key in ("offset", "limit"):
            continue

        # Sort
        if key == "sort":
            if value.startswith("-"):
                result.sort_field = value[1:]
                result.sort_desc = True
            else:
                result.sort_field = value
                result.sort_desc = False
            continue

        # Filters
        match = _FILTER_PATTERN.match(key)
        if match:
            field_name = match.group(1)
            if field_name not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' is not filterable. "
                    f"Allowed: {sorted(allowed.keys())}",
                )
            operator = allowed[field_name]
            result.filters.append({
                "field": field_name,
                "operator": operator,
                "value": value,
            })

    # Default sort from schema
    if result.sort_field is None:
        default_sort = schema.get("dataSource", {}).get("defaultSort")
        if default_sort:
            if default_sort.startswith("-"):
                result.sort_field = default_sort[1:]
                result.sort_desc = True
            else:
                result.sort_field = default_sort
                result.sort_desc = False

    return result
