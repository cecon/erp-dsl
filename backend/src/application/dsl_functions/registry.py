"""Function Registry — maps DSL function names to safe Python callables.

Only whitelisted, registered functions can be invoked by the DSL schema.
No dynamic eval/exec is used. Functions are plain Python callables that
receive a single value and return the transformed value.
"""

from __future__ import annotations

from typing import Any, Callable

# Type alias for a transform function: receives value, returns value
TransformFn = Callable[[Any], Any]


class FunctionRegistry:
    """Thread-safe registry of named transform functions."""

    def __init__(self) -> None:
        self._functions: dict[str, TransformFn] = {}

    def register(self, name: str, fn: TransformFn) -> None:
        """Register a function by name. Overwrites if already registered."""
        self._functions[name] = fn

    def get(self, name: str) -> TransformFn | None:
        """Look up a function by name. Returns None if not found."""
        return self._functions.get(name)

    def has(self, name: str) -> bool:
        """Check if a function is registered."""
        return name in self._functions

    def list_names(self) -> list[str]:
        """Return all registered function names."""
        return list(self._functions.keys())


# Singleton registry used across the application
function_registry = FunctionRegistry()
