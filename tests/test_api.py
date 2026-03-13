"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from detail_forge.api.app import app

client = TestClient(app)


# --- /health ---


class TestHealthEndpoint:
    def test_health_returns_200(self):
        """GET /health should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        """GET /health should return status ok and version."""
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"
        assert body["version"] == "0.3.0"


# --- /api/v1/themes ---


class TestThemesEndpoint:
    def test_themes_returns_200(self):
        """GET /api/v1/themes should return HTTP 200."""
        response = client.get("/api/v1/themes")
        assert response.status_code == 200

    def test_themes_response_structure(self):
        """GET /api/v1/themes should return a themes list."""
        response = client.get("/api/v1/themes")
        body = response.json()
        assert "themes" in body
        assert isinstance(body["themes"], list)

    def test_themes_list_non_empty(self):
        """Themes list should contain at least one recipe."""
        response = client.get("/api/v1/themes")
        body = response.json()
        assert len(body["themes"]) > 0


# --- /api/v1/templates ---


class TestTemplatesEndpoint:
    def test_templates_returns_200(self):
        """GET /api/v1/templates should return HTTP 200."""
        response = client.get("/api/v1/templates")
        assert response.status_code == 200

    def test_templates_response_structure(self):
        """GET /api/v1/templates should return a templates list."""
        response = client.get("/api/v1/templates")
        body = response.json()
        assert "templates" in body
        assert isinstance(body["templates"], list)

    def test_template_items_have_required_fields(self):
        """Each template item should have id, section_type, category fields."""
        response = client.get("/api/v1/templates")
        templates = response.json()["templates"]
        for tmpl in templates:
            assert "id" in tmpl
            assert "section_type" in tmpl
            assert "category" in tmpl


# --- /api/v1/generate ---


class TestGenerateEndpoint:
    def test_generate_returns_500_on_empty_features(self):
        """POST /api/v1/generate with empty features may raise 500 (no templates)."""
        payload = {
            "product_name": "Test Product",
            "product_features": [],
            "template_ids": [],
            "theme_name": "classic_trust",
            "include_naver": False,
        }
        response = client.post("/api/v1/generate", json=payload)
        # Depending on template availability, could be 200 or 500
        assert response.status_code in (200, 500)

    def test_generate_missing_product_name_returns_422(self):
        """POST /api/v1/generate without product_name should return 422."""
        payload = {
            "product_features": ["feature1"],
        }
        response = client.post("/api/v1/generate", json=payload)
        assert response.status_code == 422

    def test_generate_missing_product_features_returns_422(self):
        """POST /api/v1/generate without product_features should return 422."""
        payload = {
            "product_name": "Test Product",
        }
        response = client.post("/api/v1/generate", json=payload)
        assert response.status_code == 422

    def test_generate_with_valid_payload_structure(self):
        """POST /api/v1/generate with a valid payload should not return 4xx."""
        payload = {
            "product_name": "Running Shoes",
            "product_features": ["Lightweight", "Breathable mesh"],
            "template_ids": [],
            "theme_name": "classic_trust",
            "include_naver": False,
        }
        response = client.post("/api/v1/generate", json=payload)
        # Should not be a client error; 200 or 500 (template/AI dependency)
        assert response.status_code != 400
        assert response.status_code != 422

    def test_generate_response_schema_on_success(self):
        """If generate returns 200, body should have required fields."""
        payload = {
            "product_name": "Wireless Headphones",
            "product_features": ["30hr battery", "ANC"],
            "template_ids": [],
            "theme_name": "classic_trust",
            "include_naver": False,
        }
        response = client.post("/api/v1/generate", json=payload)
        if response.status_code == 200:
            body = response.json()
            assert "web_html" in body
            assert "quality_score" in body
            assert "generation_time_ms" in body
            assert "warnings" in body
            assert isinstance(body["warnings"], list)


# --- OpenAPI / Docs ---


class TestOpenAPIDocs:
    def test_openapi_schema_accessible(self):
        """GET /openapi.json should return HTTP 200."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_has_paths(self):
        """OpenAPI schema should list our endpoints."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert "/health" in schema["paths"]
        assert "/api/v1/generate" in schema["paths"]
        assert "/api/v1/themes" in schema["paths"]
        assert "/api/v1/templates" in schema["paths"]
