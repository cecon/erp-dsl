"""Value object representing a validated page key."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PageKey:
    """Immutable value object for a page identifier.

    Valid keys are lowercase alphanumeric strings with hyphens/underscores,
    between 2 and 64 characters.
    """

    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            raise ValueError(
                f"Invalid page key '{self.value}'. Must match pattern: "
                "lowercase letters, digits, hyphens, underscores (2-64 chars)."
            )

    def __str__(self) -> str:
        return self.value
