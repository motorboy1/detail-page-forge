"""ProviderRouter — auto-selects the best AI provider for each task.

Routes copy generation, image generation, and image analysis to the
configured providers with automatic fallback on failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.providers.base import AIProviderBase, CopyRequest, CopyResponse


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
        Raises the last exception if all providers fail.
        """
        last_exc: Exception | None = None
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
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                tried.append(name)
                continue

        if last_exc is not None:
            raise last_exc
        raise RuntimeError(
            f"No providers available for copy generation. "
            f"Registered: {list(self._providers.keys())}, "
            f"Tried: {tried}"
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
