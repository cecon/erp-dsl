"""DSL Function Pipeline — pluggable transform functions for schema fields.

Provides a registry of named functions that can be declared in the DSL
schema and automatically applied during request/response processing.
"""

from src.application.dsl_functions.registry import function_registry  # noqa: F401

# Auto-register built-in functions on import
import src.application.dsl_functions.text_transforms  # noqa: F401
import src.application.dsl_functions.image_transforms  # noqa: F401
