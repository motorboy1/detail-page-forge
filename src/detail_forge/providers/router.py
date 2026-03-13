"""ProviderRouter — auto-selects the best AI provider for each task.

Routes copy generation, image generation, and image analysis to the
configured providers with automatic fallback on failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.exceptions import (
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from detail_forge.providers.base import AIProviderBase, CopyRequest, CopyResponse
from detail_forge.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for provider selection."""

    copy_provider: str = "claude"       # claude, openai, gemini
    image_provider: str = "openai"      # openai (DALL-E), gemini (Imagen)
    analysis_provider: str = "claude"   # claude (best for vision analysis)
    fallback_order: list[str] = field(
        default_factory=lambda: ["claude", "openai", "gemini"]
    )


class ProviderRouter:
    """Routes AI tasks to the optimal provider."""

    def __init__(self, config: ProviderConfig | None = None) -> None:
        self._config = config or ProviderConfig()
        self._providers: dict[str, AIProviderBase] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, provider: AIProviderBase) -> None:
        """Register a provider by name."""
        self._providers[name] = provider

    def list_available(self) -> list[str]:
        """List registered provider names."""
        return list(self._providers.keys())

    # ------------------------------------------------------------------
    # Provider accessors
    # ------------------------------------------------------------------

    def get_copy_provider(self) -> AIProviderBase:
        """Get the provider configured for copywriting."""
        return self._get_provider(self._config.copy_provider)

    def get_image_provider(self) -> AIProviderBase:
        """Get the provider configured for image generation."""
        return self._get_provider(self._config.image_provider)

    def get_analysis_provider(self) -> AIProviderBase:
        """Get the provider configured for image analysis."""
        return self._get_provider(self._config.analysis_provider)

    # ------------------------------------------------------------------
    # Fallback execution
    # ------------------------------------------------------------------

    async def generate_copy_with_fallback(self, request: CopyRequest) -> CopyResponse:
        """Try primary provider, fall back on failure.

        Iterates through fallback_order until one succeeds.
        When ALL providers fail, returns _fallback_copy() with a warning log.

        Returns:
            CopyResponse from a provider or the static fallback.
        """
        tried: list[str] = []

        # Build attempt order: primary first, then remaining fallbacks
        primary = self._config.copy_provider
        order: list[str] = [primary]
        for name in self._config.fallback_order:
            if name != primary and name not in order:
                order.append(name)

        for name in order:
            if name not in self._providers:
                continue
            try:
                result = await self._providers[name].generate_copy(request)
                return result
            except (
                ProviderTimeoutError,
                ProviderRateLimitError,
                ProviderInvalidResponseError,
                ProviderError,
            ) as exc:
                logger.warning(
                    "Provider '%s' failed (%s): %s -- trying fallback",
                    name,
                    type(exc).__name__,
                    exc.message,
                )
                tried.append(name)
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Provider '%s' raised unexpected error (%s) -- trying fallback",
                    name,
                    type(exc).__name__,
                )
                tried.append(name)
                continue

        # All providers failed — use static fallback copy + warning
        logger.warning(
            "All providers failed (%s). Using static fallback copy.",
            tried,
        )
        return self._fallback_copy(request)

    def _fallback_copy(self, request: CopyRequest) -> CopyResponse:
        """Return a minimal static CopyResponse when all providers fail.

        Ensures the generation pipeline can still complete with placeholder copy
        rather than raising to the user.
        """
        return CopyResponse(
            headline=request.product_name,
            subheadline="상품 상세 페이지",
            body="상품 정보를 확인해 주세요.",
            cta_text="지금 구매하기",
            raw_text=f"{request.product_name}\n상품 상세 페이지",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_provider(self, name: str) -> AIProviderBase:
        """Retrieve a provider by name, raising if not registered."""
        if name not in self._providers:
            raise KeyError(
                f"Provider '{name}' is not registered. "
                f"Available: {list(self._providers.keys())}"
            )
        return self._providers[name]
