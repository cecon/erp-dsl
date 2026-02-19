"""Pure-domain merge service for deep-merging page schemas.

This service is pure domain logic with zero external dependencies.
It performs deterministic deep merges of JSON schemas, treating
arrays of objects with stable IDs as keyed collections.
"""

from __future__ import annotations

import copy
from typing import Any


class MergeService:
    """Deterministic deep-merge of page schemas.

    Merge strategy:
    - Dicts are merged recursively; tenant values override global.
    - Arrays of objects with an 'id' field are merged by matching IDs.
    - Arrays without 'id' fields are replaced entirely by the override.
    - Scalar values in the override replace the base.
    """

    @staticmethod
    def deep_merge(
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge override into base, returning a new dict."""
        result = copy.deepcopy(base)
        MergeService._merge_into(result, override)
        return result

    @staticmethod
    def _merge_into(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, source_val in source.items():
            if key not in target:
                target[key] = copy.deepcopy(source_val)
                continue

            target_val = target[key]

            if isinstance(target_val, dict) and isinstance(source_val, dict):
                MergeService._merge_into(target_val, source_val)

            elif (
                isinstance(target_val, list)
                and isinstance(source_val, list)
            ):
                target[key] = MergeService._merge_arrays(
                    target_val, source_val
                )
            else:
                # Scalar override
                target[key] = copy.deepcopy(source_val)

    @staticmethod
    def _merge_arrays(
        base_arr: list[Any], override_arr: list[Any]
    ) -> list[Any]:
        """Merge arrays using stable IDs when available."""
        if not base_arr or not override_arr:
            return copy.deepcopy(override_arr) if override_arr else copy.deepcopy(base_arr)

        # Check if items are dicts with 'id' keys
        base_has_ids = all(
            isinstance(item, dict) and "id" in item for item in base_arr
        )
        override_has_ids = all(
            isinstance(item, dict) and "id" in item for item in override_arr
        )

        if not (base_has_ids and override_has_ids):
            # No stable IDs — full replace
            return copy.deepcopy(override_arr)

        # Build index of base items by ID
        base_index: dict[Any, dict] = {
            item["id"]: copy.deepcopy(item) for item in base_arr
        }

        # Merge overrides into base by ID
        override_ids_seen: set[Any] = set()
        for item in override_arr:
            item_id = item["id"]
            override_ids_seen.add(item_id)
            if item_id in base_index:
                MergeService._merge_into(base_index[item_id], item)
            else:
                base_index[item_id] = copy.deepcopy(item)

        # Preserve order: base items first, then new override items
        result: list[dict] = []
        seen: set[Any] = set()
        for item in base_arr:
            item_id = item["id"]
            if item_id not in seen:
                result.append(base_index[item_id])
                seen.add(item_id)
        for item in override_arr:
            item_id = item["id"]
            if item_id not in seen:
                result.append(base_index[item_id])
                seen.add(item_id)

        return result
