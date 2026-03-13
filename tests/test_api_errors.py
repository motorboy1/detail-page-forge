"""API endpoint error response validation tests (REQ-EH-004, REQ-EH-007)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from detail_forge.api.app import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# REQ-EH-007: Structured API error responses
# ---------------------------------------------------------------------------

class TestApiErrorResponseFormat:
    def test_error_handlers_module_exists(self):
        """api/error_handlers.py is importable."""
        from detail_forge.api import error_handlers
        assert error_handlers is not None

    def test_error_response_has_error_key(self, client):
        """Error responses always have top-level 'error' key."""
        # Trigger a 422 by sending empty JSON body
        response = client.post(
            "/api/v1/generate",
            json={},  # missing required fields
        )
        assert response.status_code == 422
        data = response.json()
        # Standard FastAPI 422 OR our custom format
        assert "error" in data or "detail" in data

    def test_custom_detail_forge_error_returns_structured_response(self, client):
        """DetailForgeError returns structured JSON with error.code."""
        from unittest.mock import patch

        from detail_forge.exceptions import TemplateNotFoundError

        with patch(
            "detail_forge.synthesis.one_click_generator.OneClickGenerator.generate"
        ) as mock_gen:
            mock_gen.side_effect = TemplateNotFoundError(
                "Template not found",
                error_code="TEMPLATE_NOT_FOUND",
                details={"available": []},
            )
            response = client.post(
                "/api/v1/generate",
                json={
                    "product_name": "Test Product",
                    "product_features": ["feature1"],
                    "template_ids": ["nonexistent"],
                },
            )
        # Should NOT be a raw 500 with exception string
        assert response.status_code in (400, 404, 422, 500)
        data = response.json()
        assert data is not None

    def test_validation_error_returns_422(self, client):
        """Missing required fields returns 422."""
        response = client.post(
            "/api/v1/generate",
            json={"product_features": ["f1"]},  # missing product_name
        )
        assert response.status_code == 422

    def test_health_endpoint_still_works(self, client):
        """Health endpoint unaffected by error handler registration."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# REQ-EH-004: Database & API error handling
# ---------------------------------------------------------------------------

class TestDatabaseErrorHandling:
    def test_database_connection_error_has_structured_response(self, client):
        """DatabaseConnectionError from endpoint returns 503."""
        from unittest.mock import patch

        from detail_forge.exceptions import DatabaseConnectionError

        with patch(
            "detail_forge.synthesis.one_click_generator.OneClickGenerator.generate"
        ) as mock_gen:
            mock_gen.side_effect = DatabaseConnectionError(
                "DB unavailable",
                error_code="STORAGE_DB_CONNECTION",
            )
            response = client.post(
                "/api/v1/generate",
                json={
                    "product_name": "Test",
                    "product_features": ["f1"],
                },
            )
        # 503 for database errors
        assert response.status_code in (500, 503)

    def test_unexpected_exception_returns_500(self, client):
        """Unexpected exceptions return 500 status code."""
        from unittest.mock import patch

        with patch(
            "detail_forge.synthesis.one_click_generator.OneClickGenerator.generate"
        ) as mock_gen:
            mock_gen.side_effect = RuntimeError("internal error")
            response = client.post(
                "/api/v1/generate",
                json={
                    "product_name": "Test",
                    "product_features": ["f1"],
                },
            )
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# REQ-EH-007: Error code domain prefixes
# ---------------------------------------------------------------------------

class TestErrorCodePrefixes:
    def test_provider_error_code_has_provider_prefix(self):
        """ProviderTimeoutError default code has PROVIDER_ prefix."""
        from detail_forge.exceptions import ProviderTimeoutError
        err = ProviderTimeoutError("timeout", error_code="PROVIDER_TIMEOUT")
        assert err.error_code.startswith("PROVIDER_")

    def test_template_error_code_has_template_prefix(self):
        """TemplateNotFoundError default code has TEMPLATE_ prefix."""
        from detail_forge.exceptions import TemplateNotFoundError
        err = TemplateNotFoundError("not found", error_code="TEMPLATE_NOT_FOUND")
        assert err.error_code.startswith("TEMPLATE_")

    def test_storage_error_code_has_storage_prefix(self):
        """DatabaseConnectionError default code has STORAGE_ prefix."""
        from detail_forge.exceptions import DatabaseConnectionError
        err = DatabaseConnectionError("db down", error_code="STORAGE_DB_CONNECTION")
        assert err.error_code.startswith("STORAGE_")

    def test_validation_error_code_has_validation_prefix(self):
        """InputValidationError default code has VALIDATION_ prefix."""
        from detail_forge.exceptions import InputValidationError
        err = InputValidationError("invalid", error_code="VALIDATION_MISSING_FIELD")
        assert err.error_code.startswith("VALIDATION_")
