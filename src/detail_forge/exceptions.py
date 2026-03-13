"""Custom exception hierarchy for detail-page-forge (REQ-EH-001).

All domain exceptions inherit from DetailForgeError which extends Exception,
ensuring backward-compatible catchability via `except Exception`.
"""

from __future__ import annotations

from typing import Any


class DetailForgeError(Exception):
    """Base exception for all detail-forge domain errors.

    Attributes:
        message: User-friendly error message.
        error_code: Domain-prefixed error code (e.g., PROVIDER_TIMEOUT).
        details: Debugging context dict (never contains secrets).
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details: dict[str, Any] = details if details is not None else {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# ---------------------------------------------------------------------------
# Provider errors
# ---------------------------------------------------------------------------


class ProviderError(DetailForgeError):
    """AI provider operation failed."""


class ProviderTimeoutError(ProviderError):
    """AI provider timed out (>30s)."""


class ProviderRateLimitError(ProviderError):
    """AI provider returned 429 Rate Limit."""


class ProviderInvalidResponseError(ProviderError):
    """AI provider returned an unparseable response."""


# ---------------------------------------------------------------------------
# Template errors
# ---------------------------------------------------------------------------


class TemplateError(DetailForgeError):
    """Template operation failed."""


class TemplateNotFoundError(TemplateError):
    """Requested template ID does not exist in the store."""


class TemplateInvalidError(TemplateError):
    """Template HTML is structurally invalid."""


class TemplateSlotError(TemplateError):
    """Required data-slot attributes are missing from template HTML."""


# ---------------------------------------------------------------------------
# Synthesis errors
# ---------------------------------------------------------------------------


class SynthesisError(DetailForgeError):
    """Page synthesis pipeline failed."""


class CompositionError(SynthesisError):
    """Section composition failed (SectionCompositor)."""


class CoherenceError(SynthesisError):
    """Coherence check or adjustment failed (CoherenceEngine)."""


class AssemblyError(SynthesisError):
    """Page assembly failed (PageAssembler)."""


# ---------------------------------------------------------------------------
# Render errors
# ---------------------------------------------------------------------------


class RenderError(DetailForgeError):
    """Rendering operation failed."""


class NaverRenderError(RenderError):
    """Naver SmartStore renderer failed."""


class CoupangRenderError(RenderError):
    """Coupang renderer failed."""


class WebRenderError(RenderError):
    """Web renderer failed."""


# ---------------------------------------------------------------------------
# Storage errors
# ---------------------------------------------------------------------------


class StorageError(DetailForgeError):
    """Storage operation failed (DB or file I/O)."""


class DatabaseConnectionError(StorageError):
    """SQLAlchemy could not connect to the database."""


class FileIOError(StorageError):
    """File read/write operation failed."""


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class ValidationError(DetailForgeError):
    """Input validation failed (base for Pydantic integration)."""


class InputValidationError(ValidationError):
    """Domain-level input validation failed (missing/invalid fields)."""
