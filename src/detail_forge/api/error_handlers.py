"""Global exception handlers for FastAPI (REQ-EH-007).

JSON format:
    {
      "error": {
        "code": "DOMAIN_TYPE",
        "message": "...",
        "details": {...}
      }
    }

Domain prefixes:
    PROVIDER_*   - AI provider errors
    TEMPLATE_*   - Template errors
    SYNTHESIS_*  - Synthesis pipeline errors
    RENDER_*     - Rendering errors
    STORAGE_*    - DB/file storage errors
    VALIDATION_* - Input validation errors
    INTERNAL_*   - Unexpected internal errors
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from detail_forge.exceptions import (
    DatabaseConnectionError,
    DetailForgeError,
    InputValidationError,
    ProviderError,
    RenderError,
    StorageError,
    SynthesisError,
    TemplateError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def _error_response(code: str, message: str, details: dict, status_code: int) -> JSONResponse:
    """Build a standard structured error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def _map_status_code(exc: DetailForgeError) -> int:
    """Map a DetailForgeError subtype to an HTTP status code."""
    if isinstance(exc, DatabaseConnectionError):
        return 503
    if isinstance(exc, StorageError):
        return 500
    if isinstance(exc, TemplateError):
        return 404
    if isinstance(exc, (ValidationError, InputValidationError)):
        return 422
    if isinstance(exc, ProviderError):
        return 502
    if isinstance(exc, (SynthesisError, RenderError)):
        return 500
    return 500


async def detail_forge_exception_handler(
    request: Request, exc: DetailForgeError
) -> JSONResponse:
    """Handle all DetailForgeError subclasses with structured JSON."""
    status_code = _map_status_code(exc)
    code = exc.error_code or _default_code(exc)

    # Log the full details internally (debug level for stack traces)
    logger.error(
        "DetailForgeError: %s | code=%s | path=%s",
        exc.message,
        code,
        request.url.path,
        extra={"error_code": code, "details": exc.details},
    )

    return _error_response(
        code=code,
        message=exc.message,
        details=exc.details,
        status_code=status_code,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic ValidationError with 422 structured response."""
    errors = exc.errors()
    details = {
        "validation_errors": [
            {
                "field": " -> ".join(str(loc) for loc in e["loc"]),
                "message": e["msg"],
                "type": e["type"],
            }
            for e in errors
        ]
    }
    return _error_response(
        code="VALIDATION_INVALID_INPUT",
        message="Input validation failed",
        details=details,
        status_code=422,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with 500, logging details server-side only."""
    # Log full details internally but NEVER expose to client
    logger.exception(
        "Unexpected error at %s: %s",
        request.url.path,
        type(exc).__name__,
    )
    return _error_response(
        code="INTERNAL_ERROR",
        message="An internal server error occurred",
        details={},
        status_code=500,
    )


def _default_code(exc: DetailForgeError) -> str:
    """Generate a domain-prefixed code from the exception class name."""
    name = type(exc).__name__
    # Convert CamelCase to UPPER_SNAKE
    import re
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()
    # Ensure domain prefix
    prefixes = {
        "Provider": "PROVIDER_",
        "Template": "TEMPLATE_",
        "Synthesis": "SYNTHESIS_",
        "Render": "RENDER_",
        "Storage": "STORAGE_",
        "Validation": "VALIDATION_",
        "Input": "VALIDATION_",
        "Database": "STORAGE_",
        "File": "STORAGE_",
        "Assembly": "SYNTHESIS_",
        "Composition": "SYNTHESIS_",
        "Coherence": "SYNTHESIS_",
    }
    for prefix_key, domain_prefix in prefixes.items():
        if name.startswith(prefix_key):
            return snake
    return snake
