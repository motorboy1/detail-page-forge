"""Tests for AI providers and ProviderRouter — M-3.2.3 & M-3.2.4.

TDD Specification: RED phase — tests written before implementation.
All provider tests use mocked API calls (no real API calls made).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# T-3.2.3: Provider tests — OpenAI, Gemini, Claude
# ---------------------------------------------------------------------------


class TestAIProviderBase:
    """Verify all providers implement AIProviderBase."""

    def test_openai_implements_base(self):
        from detail_forge.providers.base import AIProviderBase
        from detail_forge.providers.openai_provider import OpenAIProvider

        assert issubclass(OpenAIProvider, AIProviderBase)

    def test_gemini_implements_base(self):
        from detail_forge.providers.base import AIProviderBase
        from detail_forge.providers.gemini import GeminiProvider

        assert issubclass(GeminiProvider, AIProviderBase)

    def test_claude_implements_base(self):
        from detail_forge.providers.base import AIProviderBase
        from detail_forge.providers.claude import ClaudeProvider

        assert issubclass(ClaudeProvider, AIProviderBase)


# ---------------------------------------------------------------------------
# OpenAI Provider Tests
# ---------------------------------------------------------------------------


class TestOpenAIProviderGenerateCopy:
    """Test OpenAIProvider.generate_copy with mocked openai SDK."""

    @pytest.mark.asyncio
    async def test_generate_copy_returns_copy_response(self):
        pytest.importorskip("openai", reason="openai SDK not installed")
        from detail_forge.providers.base import CopyRequest, CopyResponse

        request = CopyRequest(
            product_name="테스트 세럼",
            product_features=["보습", "미백"],
            section_type="hero",
        )
        mock_message = MagicMock()
        mock_message.content = "헤드라인: 최고의 세럼\n서브헤드라인: 촉촉함\n본문: 좋아요.\nCTA: 구매하기"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.generate_copy(request)

        assert isinstance(result, CopyResponse)

    @pytest.mark.asyncio
    async def test_generate_copy_headline_not_empty(self):
        pytest.importorskip("openai", reason="openai SDK not installed")
        from detail_forge.providers.base import CopyRequest, CopyResponse

        request = CopyRequest(
            product_name="세럼",
            product_features=["보습"],
            section_type="hero",
        )
        mock_message = MagicMock()
        mock_message.content = "Test headline content"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.generate_copy(request)

        assert isinstance(result, CopyResponse)
        assert result.raw_text != ""


class TestOpenAIProviderGenerateImages:
    """Test OpenAIProvider.generate_images with mocked openai SDK."""

    @pytest.mark.asyncio
    async def test_generate_images_returns_image_response(self):
        pytest.importorskip("openai", reason="openai SDK not installed")
        import base64

        from detail_forge.providers.base import ImageRequest, ImageResponse

        request = ImageRequest(prompt="beautiful product photo", n=1)
        fake_b64 = base64.b64encode(b"fake_image_bytes").decode()
        mock_img_data = MagicMock()
        mock_img_data.b64_json = fake_b64
        mock_img_data.revised_prompt = "revised prompt"
        mock_response = MagicMock()
        mock_response.data = [mock_img_data]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.generate_images(request)

        assert isinstance(result, ImageResponse)
        assert len(result.images) == 1
        assert len(result.prompts_used) == 1

    @pytest.mark.asyncio
    async def test_generate_images_n_images(self):
        pytest.importorskip("openai", reason="openai SDK not installed")
        import base64

        from detail_forge.providers.base import ImageRequest

        request = ImageRequest(prompt="product photo", n=3)
        fake_b64 = base64.b64encode(b"fake_bytes").decode()
        mock_img_data = MagicMock()
        mock_img_data.b64_json = fake_b64
        mock_img_data.revised_prompt = "revised"
        mock_response = MagicMock()
        mock_response.data = [mock_img_data]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.generate_images(request)

        assert len(result.images) == 3


class TestOpenAIProviderAnalyzeImage:
    """Test OpenAIProvider.analyze_image with mocked openai SDK."""

    @pytest.mark.asyncio
    async def test_analyze_image_returns_string(self):
        pytest.importorskip("openai", reason="openai SDK not installed")

        mock_message = MagicMock()
        mock_message.content = "Image analysis result"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.analyze_image(b"fake_image", "Describe this image")

        assert isinstance(result, str)
        assert result == "Image analysis result"

    @pytest.mark.asyncio
    async def test_analyze_image_handles_none_content(self):
        pytest.importorskip("openai", reason="openai SDK not installed")

        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            result = await provider.analyze_image(b"fake_image", "prompt")

        assert isinstance(result, str)


class TestOpenAIProviderErrorHandling:
    """Test OpenAI provider handles API errors gracefully."""

    @pytest.mark.asyncio
    async def test_generate_copy_api_error_raises(self):
        pytest.importorskip("openai", reason="openai SDK not installed")
        from detail_forge.providers.base import CopyRequest

        request = CopyRequest(
            product_name="세럼",
            product_features=["보습"],
            section_type="hero",
        )

        with patch("detail_forge.providers.openai_provider.openai") as mock_openai_module, \
             patch("detail_forge.providers.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="test-key")
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API error")
            mock_openai_module.OpenAI.return_value = mock_client

            from detail_forge.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            with pytest.raises(Exception):
                await provider.generate_copy(request)


# ---------------------------------------------------------------------------
# Gemini Provider Tests
# ---------------------------------------------------------------------------


class TestGeminiProviderGenerateCopy:
    """Test GeminiProvider.generate_copy with mocked google-genai SDK."""

    @pytest.mark.asyncio
    async def test_generate_copy_returns_copy_response(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")
        from detail_forge.providers.base import CopyRequest, CopyResponse

        request = CopyRequest(
            product_name="테스트 제품",
            product_features=["특징1", "특징2"],
            section_type="hero",
        )
        mock_response = MagicMock()
        mock_response.text = "헤드라인: 멋진 제품\n서브헤드라인: 최고"

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.generate_copy(request)

        assert isinstance(result, CopyResponse)

    @pytest.mark.asyncio
    async def test_generate_copy_raw_text_populated(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")
        from detail_forge.providers.base import CopyRequest

        request = CopyRequest(
            product_name="제품",
            product_features=["특징"],
            section_type="features",
        )
        mock_response = MagicMock()
        mock_response.text = "Some copy text"

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.generate_copy(request)

        assert result.raw_text == "Some copy text"


class TestGeminiProviderGenerateImages:
    """Test GeminiProvider.generate_images with mocked SDK."""

    @pytest.mark.asyncio
    async def test_generate_images_returns_image_response(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")
        from detail_forge.providers.base import ImageRequest, ImageResponse

        request = ImageRequest(prompt="product image", n=1)
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake_image"
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.generate_images(request)

        assert isinstance(result, ImageResponse)

    @pytest.mark.asyncio
    async def test_generate_images_no_image_parts(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")
        from detail_forge.providers.base import ImageRequest, ImageResponse

        request = ImageRequest(prompt="product image", n=1)
        mock_part = MagicMock()
        mock_part.inline_data = None  # No image data
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.generate_images(request)

        assert isinstance(result, ImageResponse)
        assert result.images == []


class TestGeminiProviderAnalyzeImage:
    """Test GeminiProvider.analyze_image with mocked SDK."""

    @pytest.mark.asyncio
    async def test_analyze_image_returns_string(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")

        mock_response = MagicMock()
        mock_response.text = "Gemini image analysis"

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.analyze_image(b"fake_image", "Describe this")

        assert isinstance(result, str)
        assert result == "Gemini image analysis"

    @pytest.mark.asyncio
    async def test_analyze_image_handles_none_text(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")

        mock_response = MagicMock()
        mock_response.text = None

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            result = await provider.analyze_image(b"fake_image", "prompt")

        assert isinstance(result, str)
        assert result == ""


class TestGeminiProviderErrorHandling:
    """Test Gemini provider handles API errors."""

    @pytest.mark.asyncio
    async def test_generate_copy_api_error_raises(self):
        pytest.importorskip("google.genai", reason="google-genai SDK not installed")
        from detail_forge.providers.base import CopyRequest

        request = CopyRequest(
            product_name="제품",
            product_features=["특징"],
            section_type="hero",
        )

        with patch("detail_forge.providers.gemini.genai") as mock_genai, \
             patch("detail_forge.providers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="test-key")
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("Gemini API error")
            mock_genai.Client.return_value = mock_client

            from detail_forge.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            with pytest.raises(Exception):
                await provider.generate_copy(request)


# ---------------------------------------------------------------------------
# Claude Provider Tests
# ---------------------------------------------------------------------------


class TestClaudeProviderGenerateCopy:
    """Test ClaudeProvider.generate_copy with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_generate_copy_returns_copy_response(self):
        from detail_forge.providers.base import CopyRequest, CopyResponse

        request = CopyRequest(
            product_name="테스트 세럼",
            product_features=["보습", "미백"],
            section_type="hero",
        )
        mock_output = "헤드라인: 최고의 세럼\n서브헤드라인: 촉촉함\n본문: 좋습니다.\nCTA: 구매하기"

        with patch("detail_forge.providers.claude.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            from detail_forge.providers.claude import ClaudeProvider
            provider = ClaudeProvider()
            result = await provider.generate_copy(request)

        assert isinstance(result, CopyResponse)

    @pytest.mark.asyncio
    async def test_generate_copy_parses_headline(self):
        from detail_forge.providers.base import CopyRequest

        request = CopyRequest(
            product_name="세럼",
            product_features=["보습"],
            section_type="hero",
        )
        mock_output = "헤드라인: 아름다운 피부\n서브헤드라인: 최고\n본문: 좋아요\nCTA: 구매"

        with patch("detail_forge.providers.claude.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            from detail_forge.providers.claude import ClaudeProvider
            provider = ClaudeProvider()
            result = await provider.generate_copy(request)

        assert result.headline == "아름다운 피부"
        assert result.subheadline == "최고"

    @pytest.mark.asyncio
    async def test_generate_copy_cli_error_raises(self):
        from detail_forge.providers.base import CopyRequest

        request = CopyRequest(
            product_name="세럼",
            product_features=["보습"],
            section_type="hero",
        )

        with patch("detail_forge.providers.claude.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "CLI error message"
            mock_run.return_value = mock_result

            from detail_forge.providers.claude import ClaudeProvider
            provider = ClaudeProvider()
            with pytest.raises(RuntimeError):
                await provider.generate_copy(request)

    @pytest.mark.asyncio
    async def test_generate_images_raises_not_implemented(self):
        from detail_forge.providers.base import ImageRequest

        request = ImageRequest(prompt="test")

        with patch("detail_forge.providers.claude.subprocess.run"):
            from detail_forge.providers.claude import ClaudeProvider
            provider = ClaudeProvider()
            with pytest.raises(NotImplementedError):
                await provider.generate_images(request)

    @pytest.mark.asyncio
    async def test_analyze_image_returns_string(self):
        mock_output = "Claude image analysis result"

        with patch("detail_forge.providers.claude.subprocess.run") as mock_run, \
             patch("detail_forge.providers.claude.tempfile.NamedTemporaryFile"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            from detail_forge.providers.claude import ClaudeProvider
            provider = ClaudeProvider()
            # Use tmp file approach — patch unlink
            with patch("detail_forge.providers.claude.Path.unlink"):
                result = await provider.analyze_image(b"fake_image", "Describe this")

        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# T-3.2.4: ProviderRouter Tests
# ---------------------------------------------------------------------------


class TestProviderRouterImports:
    """Verify ProviderRouter and ProviderConfig can be imported."""

    def test_provider_router_importable(self):
        from detail_forge.providers.router import ProviderRouter  # noqa: F401

    def test_provider_config_importable(self):
        from detail_forge.providers.router import ProviderConfig  # noqa: F401

    def test_providers_init_exports_router(self):
        from detail_forge.providers import ProviderConfig, ProviderRouter  # noqa: F401


class TestProviderConfig:
    """Test ProviderConfig defaults and customization."""

    def test_default_copy_provider_is_claude(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig()
        assert config.copy_provider == "claude"

    def test_default_image_provider_is_openai(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig()
        assert config.image_provider == "openai"

    def test_default_analysis_provider_is_claude(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig()
        assert config.analysis_provider == "claude"

    def test_default_fallback_order(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig()
        assert isinstance(config.fallback_order, list)
        assert len(config.fallback_order) >= 2

    def test_custom_copy_provider(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig(copy_provider="openai")
        assert config.copy_provider == "openai"

    def test_custom_image_provider(self):
        from detail_forge.providers.router import ProviderConfig

        config = ProviderConfig(image_provider="gemini")
        assert config.image_provider == "gemini"


class TestProviderRouterRegister:
    """Test ProviderRouter provider registration."""

    def test_register_provider(self):
        from unittest.mock import MagicMock

        from detail_forge.providers.router import ProviderRouter

        router = ProviderRouter()
        mock_provider = MagicMock()
        router.register("test_provider", mock_provider)
        assert "test_provider" in router.list_available()

    def test_list_available_empty_initially(self):
        from detail_forge.providers.router import ProviderRouter

        router = ProviderRouter()
        assert router.list_available() == []

    def test_register_multiple_providers(self):
        from unittest.mock import MagicMock

        from detail_forge.providers.router import ProviderRouter

        router = ProviderRouter()
        router.register("provider_a", MagicMock())
        router.register("provider_b", MagicMock())
        available = router.list_available()
        assert "provider_a" in available
        assert "provider_b" in available


class TestProviderRouterGetProviders:
    """Test ProviderRouter get_*_provider methods."""

    def _make_router_with_providers(self):
        from unittest.mock import MagicMock

        from detail_forge.providers.router import ProviderConfig, ProviderRouter

        config = ProviderConfig(
            copy_provider="claude",
            image_provider="openai",
            analysis_provider="claude",
        )
        router = ProviderRouter(config=config)
        mock_claude = MagicMock()
        mock_openai = MagicMock()
        router.register("claude", mock_claude)
        router.register("openai", mock_openai)
        return router, mock_claude, mock_openai

    def test_get_copy_provider_returns_configured(self):
        router, mock_claude, _ = self._make_router_with_providers()
        provider = router.get_copy_provider()
        assert provider is mock_claude

    def test_get_image_provider_returns_configured(self):
        router, _, mock_openai = self._make_router_with_providers()
        provider = router.get_image_provider()
        assert provider is mock_openai

    def test_get_analysis_provider_returns_configured(self):
        router, mock_claude, _ = self._make_router_with_providers()
        provider = router.get_analysis_provider()
        assert provider is mock_claude

    def test_get_copy_provider_raises_when_not_registered(self):
        from detail_forge.providers.router import ProviderRouter

        router = ProviderRouter()
        with pytest.raises((KeyError, ValueError, RuntimeError)):
            router.get_copy_provider()


class TestProviderRouterFallback:
    """Test ProviderRouter.generate_copy_with_fallback."""

    @pytest.mark.asyncio
    async def test_fallback_succeeds_with_primary(self):
        from detail_forge.providers.base import CopyRequest, CopyResponse
        from detail_forge.providers.router import ProviderConfig, ProviderRouter

        config = ProviderConfig(copy_provider="claude", fallback_order=["claude", "openai"])
        router = ProviderRouter(config=config)

        mock_claude = AsyncMock()
        mock_claude.generate_copy = AsyncMock(
            return_value=CopyResponse(headline="Claude copy", raw_text="test")
        )
        mock_openai = AsyncMock()
        router.register("claude", mock_claude)
        router.register("openai", mock_openai)

        request = CopyRequest(
            product_name="제품",
            product_features=["특징"],
            section_type="hero",
        )
        result = await router.generate_copy_with_fallback(request)

        assert isinstance(result, CopyResponse)
        mock_claude.generate_copy.assert_called_once()
        mock_openai.generate_copy.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_tries_next_on_failure(self):
        from detail_forge.providers.base import CopyRequest, CopyResponse
        from detail_forge.providers.router import ProviderConfig, ProviderRouter

        config = ProviderConfig(copy_provider="claude", fallback_order=["claude", "openai"])
        router = ProviderRouter(config=config)

        mock_claude = AsyncMock()
        mock_claude.generate_copy = AsyncMock(side_effect=Exception("Claude failed"))
        mock_openai = AsyncMock()
        mock_openai.generate_copy = AsyncMock(
            return_value=CopyResponse(headline="OpenAI fallback", raw_text="test")
        )
        router.register("claude", mock_claude)
        router.register("openai", mock_openai)

        request = CopyRequest(
            product_name="제품",
            product_features=["특징"],
            section_type="hero",
        )
        result = await router.generate_copy_with_fallback(request)

        assert isinstance(result, CopyResponse)
        assert result.headline == "OpenAI fallback"

    @pytest.mark.asyncio
    async def test_fallback_raises_when_all_fail(self):
        from detail_forge.providers.base import CopyRequest
        from detail_forge.providers.router import ProviderConfig, ProviderRouter

        config = ProviderConfig(copy_provider="claude", fallback_order=["claude"])
        router = ProviderRouter(config=config)

        mock_claude = AsyncMock()
        mock_claude.generate_copy = AsyncMock(side_effect=Exception("All failed"))
        router.register("claude", mock_claude)

        request = CopyRequest(
            product_name="제품",
            product_features=["특징"],
            section_type="hero",
        )
        with pytest.raises(Exception):
            await router.generate_copy_with_fallback(request)
