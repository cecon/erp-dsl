"""Built-in text transform functions for the DSL pipeline.

All functions follow the signature: (value: Any) -> Any
They are auto-registered in the function_registry on import.
"""

from __future__ import annotations

import re
from typing import Any

from src.application.dsl_functions.registry import function_registry


def strip_punctuation(value: Any) -> Any:
    """Remove common punctuation (., -, /, (, ), spaces) from strings.

    Useful for CPF, CNPJ, phone numbers, CEP, etc.
    """
    if not isinstance(value, str):
        return value
    return re.sub(r"[.\-/()\s]", "", value)


def uppercase(value: Any) -> Any:
    """Convert string to uppercase."""
    if not isinstance(value, str):
        return value
    return value.upper()


def lowercase(value: Any) -> Any:
    """Convert string to lowercase."""
    if not isinstance(value, str):
        return value
    return value.lower()


def trim(value: Any) -> Any:
    """Strip leading and trailing whitespace."""
    if not isinstance(value, str):
        return value
    return value.strip()


def only_digits(value: Any) -> Any:
    """Keep only numeric digits from a string."""
    if not isinstance(value, str):
        return value
    return re.sub(r"\D", "", value)


# ── Auto-register all functions ──────────────────────────────────

function_registry.register("strip_punctuation", strip_punctuation)
function_registry.register("uppercase", uppercase)
function_registry.register("lowercase", lowercase)
function_registry.register("trim", trim)
function_registry.register("only_digits", only_digits)
