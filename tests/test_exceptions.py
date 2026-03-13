"""Tests for custom exception hierarchy (REQ-EH-001)."""

import pytest

# ---------------------------------------------------------------------------
# Test: Base exception
# ---------------------------------------------------------------------------

class TestDetailForgeError:
    def test_base_is_exception_subclass(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("test message")
        assert isinstance(err, Exception)

    def test_base_has_error_code_field(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("msg", error_code="TEST_CODE")
        assert err.error_code == "TEST_CODE"

    def test_base_has_message_field(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("user message")
        assert err.message == "user message"

    def test_base_has_details_field(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("msg", details={"key": "value"})
        assert err.details == {"key": "value"}

    def test_base_details_defaults_to_empty_dict(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("msg")
        assert err.details == {}

    def test_base_error_code_defaults_to_none(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("msg")
        assert err.error_code is None

    def test_str_returns_message(self):
        from detail_forge.exceptions import DetailForgeError
        err = DetailForgeError("my message")
        assert "my message" in str(err)


# ---------------------------------------------------------------------------
# Test: ProviderError hierarchy
# ---------------------------------------------------------------------------

class TestProviderErrors:
    def test_provider_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, ProviderError
        err = ProviderError("provider failed")
        assert isinstance(err, DetailForgeError)

    def test_provider_timeout_error_is_provider_error(self):
        from detail_forge.exceptions import ProviderError, ProviderTimeoutError
        err = ProviderTimeoutError("timeout")
        assert isinstance(err, ProviderError)

    def test_provider_rate_limit_error_is_provider_error(self):
        from detail_forge.exceptions import ProviderError, ProviderRateLimitError
        err = ProviderRateLimitError("rate limited")
        assert isinstance(err, ProviderError)

    def test_provider_invalid_response_error_is_provider_error(self):
        from detail_forge.exceptions import ProviderError, ProviderInvalidResponseError
        err = ProviderInvalidResponseError("bad response")
        assert isinstance(err, ProviderError)

    def test_provider_timeout_has_error_code(self):
        from detail_forge.exceptions import ProviderTimeoutError
        err = ProviderTimeoutError("timeout", error_code="PROVIDER_TIMEOUT")
        assert err.error_code == "PROVIDER_TIMEOUT"

    def test_provider_rate_limit_has_details(self):
        from detail_forge.exceptions import ProviderRateLimitError
        err = ProviderRateLimitError("rate limited", details={"retry_after": 60})
        assert err.details["retry_after"] == 60

    def test_provider_invalid_response_has_details(self):
        from detail_forge.exceptions import ProviderInvalidResponseError
        err = ProviderInvalidResponseError("bad response", details={"raw": "garbage"})
        assert err.details["raw"] == "garbage"


# ---------------------------------------------------------------------------
# Test: TemplateError hierarchy
# ---------------------------------------------------------------------------

class TestTemplateErrors:
    def test_template_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, TemplateError
        err = TemplateError("template failed")
        assert isinstance(err, DetailForgeError)

    def test_template_not_found_error_is_template_error(self):
        from detail_forge.exceptions import TemplateError, TemplateNotFoundError
        err = TemplateNotFoundError("not found")
        assert isinstance(err, TemplateError)

    def test_template_invalid_error_is_template_error(self):
        from detail_forge.exceptions import TemplateError, TemplateInvalidError
        err = TemplateInvalidError("invalid")
        assert isinstance(err, TemplateError)

    def test_template_slot_error_is_template_error(self):
        from detail_forge.exceptions import TemplateError, TemplateSlotError
        err = TemplateSlotError("slot missing")
        assert isinstance(err, TemplateError)

    def test_template_not_found_stores_available_templates(self):
        from detail_forge.exceptions import TemplateNotFoundError
        err = TemplateNotFoundError(
            "hero-99 not found",
            details={"available": ["hero-01", "hero-02"]}
        )
        assert err.details["available"] == ["hero-01", "hero-02"]


# ---------------------------------------------------------------------------
# Test: SynthesisError hierarchy
# ---------------------------------------------------------------------------

class TestSynthesisErrors:
    def test_synthesis_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, SynthesisError
        err = SynthesisError("synthesis failed")
        assert isinstance(err, DetailForgeError)

    def test_composition_error_is_synthesis_error(self):
        from detail_forge.exceptions import CompositionError, SynthesisError
        err = CompositionError("composition failed")
        assert isinstance(err, SynthesisError)

    def test_coherence_error_is_synthesis_error(self):
        from detail_forge.exceptions import CoherenceError, SynthesisError
        err = CoherenceError("coherence failed")
        assert isinstance(err, SynthesisError)

    def test_assembly_error_is_synthesis_error(self):
        from detail_forge.exceptions import AssemblyError, SynthesisError
        err = AssemblyError("assembly failed")
        assert isinstance(err, SynthesisError)


# ---------------------------------------------------------------------------
# Test: RenderError hierarchy
# ---------------------------------------------------------------------------

class TestRenderErrors:
    def test_render_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, RenderError
        err = RenderError("render failed")
        assert isinstance(err, DetailForgeError)

    def test_naver_render_error_is_render_error(self):
        from detail_forge.exceptions import NaverRenderError, RenderError
        err = NaverRenderError("naver render failed")
        assert isinstance(err, RenderError)

    def test_coupang_render_error_is_render_error(self):
        from detail_forge.exceptions import CoupangRenderError, RenderError
        err = CoupangRenderError("coupang render failed")
        assert isinstance(err, RenderError)

    def test_web_render_error_is_render_error(self):
        from detail_forge.exceptions import RenderError, WebRenderError
        err = WebRenderError("web render failed")
        assert isinstance(err, RenderError)


# ---------------------------------------------------------------------------
# Test: StorageError hierarchy
# ---------------------------------------------------------------------------

class TestStorageErrors:
    def test_storage_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, StorageError
        err = StorageError("storage failed")
        assert isinstance(err, DetailForgeError)

    def test_database_connection_error_is_storage_error(self):
        from detail_forge.exceptions import DatabaseConnectionError, StorageError
        err = DatabaseConnectionError("db connection failed")
        assert isinstance(err, StorageError)

    def test_file_io_error_is_storage_error(self):
        from detail_forge.exceptions import FileIOError, StorageError
        err = FileIOError("file not found")
        assert isinstance(err, StorageError)

    def test_file_io_error_stores_path_info(self):
        from detail_forge.exceptions import FileIOError
        err = FileIOError(
            "file not found",
            details={"path": "/data/img.png", "alternatives": ["/tmp/img.png"]}
        )
        assert err.details["path"] == "/data/img.png"


# ---------------------------------------------------------------------------
# Test: InputValidationError
# ---------------------------------------------------------------------------

class TestInputValidationError:
    def test_input_validation_error_is_detail_forge_error(self):
        from detail_forge.exceptions import DetailForgeError, InputValidationError
        err = InputValidationError("validation failed")
        assert isinstance(err, DetailForgeError)

    def test_input_validation_error_stores_missing_fields(self):
        from detail_forge.exceptions import InputValidationError
        err = InputValidationError(
            "missing required fields",
            details={"missing_fields": ["name"]}
        )
        assert "name" in err.details["missing_fields"]


# ---------------------------------------------------------------------------
# Test: Catchability via base classes
# ---------------------------------------------------------------------------

class TestExceptionCatchability:
    def test_all_exceptions_catchable_as_exception(self):
        from detail_forge.exceptions import (
            CompositionError,
            DatabaseConnectionError,
            FileIOError,
            InputValidationError,
            NaverRenderError,
            ProviderTimeoutError,
            TemplateNotFoundError,
        )
        errors = [
            ProviderTimeoutError("t"),
            TemplateNotFoundError("t"),
            CompositionError("t"),
            NaverRenderError("t"),
            DatabaseConnectionError("t"),
            FileIOError("t"),
            InputValidationError("t"),
        ]
        for err in errors:
            with pytest.raises(Exception):
                raise err

    def test_all_exceptions_catchable_as_detail_forge_error(self):
        from detail_forge.exceptions import (
            CompositionError,
            DatabaseConnectionError,
            DetailForgeError,
            FileIOError,
            InputValidationError,
            NaverRenderError,
            ProviderTimeoutError,
            TemplateNotFoundError,
        )
        errors = [
            ProviderTimeoutError("t"),
            TemplateNotFoundError("t"),
            CompositionError("t"),
            NaverRenderError("t"),
            DatabaseConnectionError("t"),
            FileIOError("t"),
            InputValidationError("t"),
        ]
        for err in errors:
            with pytest.raises(DetailForgeError):
                raise err
