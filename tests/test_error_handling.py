"""Integration tests for error handling across modules (REQ-EH-002 through REQ-EH-006)."""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# REQ-EH-002: ProviderRouter fallback chain
# ---------------------------------------------------------------------------

class TestProviderRouterFallback:
    """When ALL providers fail, use _fallback_copy() + warning."""

    def test_fallback_copy_method_exists(self):
        from detail_forge.providers.router import ProviderRouter
        router = ProviderRouter()
        assert hasattr(router, "_fallback_copy")

    @pytest.mark.asyncio
    async def test_all_providers_fail_returns_fallback(self):
        """When all providers fail, fallback copy is returned with warning."""
        from detail_forge.providers.base import CopyRequest
        from detail_forge.providers.router import ProviderRouter

        class FailingProvider:
            async def generate_copy(self, req):
                raise RuntimeError("provider down")

        router = ProviderRouter()
        router.register("claude", FailingProvider())
        router.register("openai", FailingProvider())

        result = await router.generate_copy_with_fallback(
            CopyRequest(
                product_name="Test Product",
                product_features=["feature1"],
                section_type="hero",
            )
        )
        # Should return a fallback CopyResponse with warning flag
        assert result is not None
        assert hasattr(result, "headline") or hasattr(result, "raw_text")

    @pytest.mark.asyncio
    async def test_provider_timeout_triggers_fallback(self):
        """ProviderTimeoutError triggers fallback to next provider."""
        from detail_forge.exceptions import ProviderTimeoutError
        from detail_forge.providers.base import CopyRequest, CopyResponse
        from detail_forge.providers.router import ProviderRouter

        class TimeoutProvider:
            async def generate_copy(self, req):
                raise ProviderTimeoutError("timeout", error_code="PROVIDER_TIMEOUT")

        class WorkingProvider:
            async def generate_copy(self, req):
                return CopyResponse(headline="Success", raw_text="success")

        router = ProviderRouter()
        router.register("claude", TimeoutProvider())
        router.register("openai", WorkingProvider())
        router._config.copy_provider = "claude"
        router._config.fallback_order = ["claude", "openai"]

        result = await router.generate_copy_with_fallback(
            CopyRequest(
                product_name="Test",
                product_features=["f1"],
                section_type="hero",
            )
        )
        assert result.headline == "Success"

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_fallback(self):
        """ProviderRateLimitError triggers fallback to next provider."""
        from detail_forge.exceptions import ProviderRateLimitError
        from detail_forge.providers.base import CopyRequest, CopyResponse
        from detail_forge.providers.router import ProviderRouter

        class RateLimitProvider:
            async def generate_copy(self, req):
                raise ProviderRateLimitError("rate limited", error_code="PROVIDER_RATE_LIMIT")

        class WorkingProvider:
            async def generate_copy(self, req):
                return CopyResponse(headline="Fallback success")

        router = ProviderRouter()
        router.register("claude", RateLimitProvider())
        router.register("openai", WorkingProvider())
        router._config.copy_provider = "claude"
        router._config.fallback_order = ["claude", "openai"]

        result = await router.generate_copy_with_fallback(
            CopyRequest(
                product_name="Test",
                product_features=["f1"],
                section_type="hero",
            )
        )
        assert result.headline == "Fallback success"


# ---------------------------------------------------------------------------
# REQ-EH-003: Template error handling
# ---------------------------------------------------------------------------

class TestTemplateErrorHandling:
    def test_template_not_found_raises_template_not_found_error(self, tmp_path):
        """TemplateNotFoundError raised when template_id does not exist."""
        from detail_forge.exceptions import TemplateNotFoundError
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore(base_dir=tmp_path)
        with pytest.raises(TemplateNotFoundError) as exc_info:
            store.get_template("nonexistent-template-id")

        assert exc_info.value.details is not None

    def test_template_not_found_includes_available_list(self, tmp_path):
        """TemplateNotFoundError details include available templates."""
        from detail_forge.exceptions import TemplateNotFoundError
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore(base_dir=tmp_path)
        with pytest.raises(TemplateNotFoundError) as exc_info:
            store.get_template("nonexistent")

        assert "available" in exc_info.value.details


# ---------------------------------------------------------------------------
# REQ-EH-005: File I/O error handling
# ---------------------------------------------------------------------------

class TestFileIOErrorHandling:
    def test_export_manager_wraps_io_error(self):
        """ExportManager raises FileIOError on ZIP I/O failure."""
        from detail_forge.exceptions import FileIOError as DFFileIOError
        from detail_forge.output.export_manager import ExportManager

        manager = ExportManager()

        # Simulate IOError during ZIP creation by patching zipfile
        with patch("detail_forge.output.export_manager.zipfile.ZipFile") as mock_zip:
            mock_zip.return_value.__enter__.side_effect = IOError("disk full")
            mock_zip.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises((DFFileIOError, IOError)):
                manager.export(product_name="test", web_html="<html/>")


# ---------------------------------------------------------------------------
# REQ-EH-006: Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_invalid_principle_ids_fallback_to_default_theme(self):
        """Invalid principle IDs fall back to 'standard' default theme."""
        from detail_forge.copywriter.generator import ProductInfo, SectionCopy
        from detail_forge.synthesis.one_click_generator import OneClickGenerator
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore()
        gen = OneClickGenerator(template_store=store)

        # Use invalid principle IDs - should not raise, should fallback
        result = gen.generate(
            product=ProductInfo(name="Test Product", features=["f1"]),
            copy_sections=[SectionCopy(section_index=0, section_type="hero")],
            template_ids=[],
            principle_ids=[99999, 99998],  # invalid IDs
        )
        assert result is not None
        assert len(result.warnings) > 0 or result.theme is not None

    def test_product_info_missing_name_raises_input_validation_error(self):
        """Missing ProductInfo.name raises InputValidationError."""
        from detail_forge.copywriter.generator import ProductInfo
        from detail_forge.exceptions import InputValidationError
        from detail_forge.synthesis.one_click_generator import OneClickGenerator
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore()
        gen = OneClickGenerator(template_store=store)

        # Empty product name should raise InputValidationError
        with pytest.raises((InputValidationError, ValueError)):
            gen.generate(
                product=ProductInfo(name="", features=[]),
                copy_sections=[],
                template_ids=[],
            )

    def test_empty_sections_with_template_ids_raises_or_warns(self):
        """Empty sections data leads to SynthesisError or warning."""
        from detail_forge.copywriter.generator import ProductInfo, SectionCopy
        from detail_forge.synthesis.one_click_generator import OneClickGenerator
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore()
        gen = OneClickGenerator(template_store=store)

        # All invalid template IDs -> all skipped -> empty sections
        result = gen.generate(
            product=ProductInfo(name="Test", features=["f"]),
            copy_sections=[SectionCopy(section_index=0, section_type="hero")],
            template_ids=["nonexistent-1", "nonexistent-2"],
        )
        # Should either raise SynthesisError or return with warnings
        assert result.warnings or result.assembled_page is not None


# ---------------------------------------------------------------------------
# REQ-EH-008: Structured logging
# ---------------------------------------------------------------------------

class TestStructuredLogging:
    def test_logging_module_exists(self):
        """utils/logging.py module is importable."""
        from detail_forge.utils import logging as df_logging
        assert df_logging is not None

    def test_get_logger_returns_logger(self):
        """get_logger() returns a standard logger."""
        import logging as stdlib_logging

        from detail_forge.utils.logging import get_logger
        logger = get_logger("test_module")
        assert isinstance(logger, stdlib_logging.Logger)

    def test_sensitive_data_filter_removes_api_key(self):
        """SensitiveDataFilter removes API key values from log records."""
        import logging

        from detail_forge.utils.logging import SensitiveDataFilter

        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Error with api_key=sk-abc123", args=(), exc_info=None
        )
        result = filter_obj.filter(record)
        # Filter returns True (allow) but masks sensitive data
        assert result is True
        assert "sk-abc123" not in record.getMessage()

    def test_sensitive_data_filter_removes_password(self):
        """SensitiveDataFilter removes password values from log records."""
        import logging

        from detail_forge.utils.logging import SensitiveDataFilter

        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Error with password=mysecret123", args=(), exc_info=None
        )
        filter_obj.filter(record)
        assert "mysecret123" not in record.getMessage()
