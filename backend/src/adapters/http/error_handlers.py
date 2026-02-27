"""Standardized error handling for the ERP API.

All error responses follow a consistent shape:

    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable description",
            "status": 400,
            "details": { ... }     # optional, context-specific
        }
    }

Register these handlers in the FastAPI app via ``register_error_handlers(app)``.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.infrastructure.persistence.sqlalchemy.generic_crud_repository import (
    StaleDataError,
)
from src.application.dsl_functions.validators import ValidationError

logger = logging.getLogger(__name__)

# ── Error code mapping ───────────────────────────────────────────────

_HTTP_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def _error_response(
    status: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a standardized error JSONResponse."""
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
        }
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


# ── Exception handlers ───────────────────────────────────────────────


async def _handle_http_exception(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Wrap FastAPI's HTTPException in the standard shape."""
    status = exc.status_code
    code = _HTTP_CODE_MAP.get(status, "ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(status, code, message)


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Wrap Pydantic/FastAPI validation errors (422) in the standard shape."""
    errors = []
    for err in exc.errors():
        loc = " → ".join(str(part) for part in err.get("loc", []))
        errors.append({
            "field": loc,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        })

    return _error_response(
        status=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": errors},
    )


async def _handle_stale_data(
    request: Request, exc: StaleDataError
) -> JSONResponse:
    """Handle optimistic locking conflicts (409)."""
    return _error_response(
        status=409,
        code="CONFLICT",
        message=str(exc),
        details={
            "entity_id": exc.entity_id,
            "expected_version": exc.expected_version,
        },
    )


async def _handle_dsl_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle DSL field-level validation errors (422)."""
    return _error_response(
        status=422,
        code="VALIDATION_ERROR",
        message="Field validation failed",
        details={"errors": exc.errors},
    )


async def _handle_generic_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for unhandled exceptions — never leak stack traces."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _error_response(
        status=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
    )


# ── Registration ─────────────────────────────────────────────────────


def register_error_handlers(app: FastAPI) -> None:
    """Register all standardized exception handlers on the app.

    Call this in ``create_app()`` after creating the FastAPI instance.
    """
    app.add_exception_handler(HTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StaleDataError, _handle_stale_data)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, _handle_dsl_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_generic_exception)  # type: ignore[arg-type]
