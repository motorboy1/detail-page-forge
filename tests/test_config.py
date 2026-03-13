"""Unit tests for config.py — T-1.2.7."""

from __future__ import annotations

from pathlib import Path

import pytest

from detail_forge.config import AIProvider, Platform, Settings, get_settings

# ── AIProvider enum ──────────────────────────────────────────────────────────


class TestAIProviderEnum:
    def test_has_claude_value(self):
        assert AIProvider.CLAUDE == "claude"

    def test_has_openai_value(self):
        assert AIProvider.OPENAI == "openai"

    def test_has_gemini_value(self):
        assert AIProvider.GEMINI == "gemini"

    def test_is_string_enum(self):
        assert isinstance(AIProvider.CLAUDE, str)
        assert isinstance(AIProvider.OPENAI, str)

    def test_all_values(self):
        values = {p.value for p in AIProvider}
        assert values == {"claude", "openai", "gemini"}

    def test_can_construct_from_string(self):
        assert AIProvider("claude") is AIProvider.CLAUDE
        assert AIProvider("openai") is AIProvider.OPENAI


# ── Platform enum ────────────────────────────────────────────────────────────


class TestPlatformEnum:
    def test_has_naver_value(self):
        assert Platform.NAVER == "naver"

    def test_has_coupang_value(self):
        assert Platform.COUPANG == "coupang"

    def test_all_values(self):
        values = {p.value for p in Platform}
        assert values == {"naver", "coupang"}


# ── Settings defaults ────────────────────────────────────────────────────────


class TestSettingsDefaults:
    @pytest.fixture
    def settings(self, monkeypatch):
        # Ensure no env vars bleed in from system
        for key in [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "DETAIL_FORGE_MAX_COMPETITORS",
            "DETAIL_FORGE_CRAWL_TIMEOUT_SECONDS",
        ]:
            monkeypatch.delenv(key, raising=False)
        return Settings()

    def test_default_api_keys_are_string_type(self, settings):
        # API keys default to empty string but may be populated from .env;
        # we verify the type is str and the field exists rather than requiring empty.
        assert isinstance(settings.anthropic_api_key, str)
        assert isinstance(settings.openai_api_key, str)
        assert isinstance(settings.google_api_key, str)

    def test_default_copy_provider_is_claude(self, settings):
        assert settings.copy_provider == AIProvider.CLAUDE

    def test_default_image_provider_is_gemini(self, settings):
        assert settings.image_provider == AIProvider.GEMINI

    def test_default_analysis_provider_is_claude(self, settings):
        assert settings.analysis_provider == AIProvider.CLAUDE

    def test_default_max_competitors(self, settings):
        assert settings.max_competitors == 5

    def test_default_crawl_timeout(self, settings):
        assert settings.crawl_timeout_seconds == 30

    def test_default_candidates_per_section(self, settings):
        assert settings.candidates_per_section == 3

    def test_default_image_dimensions(self, settings):
        assert settings.image_width == 860
        assert settings.image_height == 1200

    def test_default_export_settings(self, settings):
        assert settings.coupang_image_width == 860
        assert settings.naver_max_image_kb == 500

    def test_project_root_is_path(self, settings):
        assert isinstance(settings.project_root, Path)

    def test_output_dir_is_path(self, settings):
        assert isinstance(settings.output_dir, Path)

    def test_references_dir_is_path(self, settings):
        assert isinstance(settings.references_dir, Path)


# ── Settings env overrides ───────────────────────────────────────────────────


class TestSettingsEnvOverrides:
    def test_anthropic_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        settings = Settings()
        assert settings.anthropic_api_key == "test-anthropic-key"

    def test_openai_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        settings = Settings()
        assert settings.openai_api_key == "test-openai-key"

    def test_google_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        settings = Settings()
        assert settings.google_api_key == "test-google-key"

    def test_extra_fields_ignored(self, monkeypatch):
        # Settings has extra="ignore"
        monkeypatch.setenv("DETAIL_FORGE_UNKNOWN_FIELD", "should_be_ignored")
        settings = Settings()  # Should not raise
        assert settings is not None

    def test_model_config_env_prefix(self):
        # The model_config should specify "DETAIL_FORGE_" prefix
        assert Settings.model_config.get("env_prefix") == "DETAIL_FORGE_"


# ── get_settings function ────────────────────────────────────────────────────


class TestGetSettings:
    def test_returns_settings_instance(self):
        result = get_settings()
        assert isinstance(result, Settings)

    def test_returns_new_instance_each_call(self):
        # get_settings() is not cached (no lru_cache), each call is fresh
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is not s2

    def test_settings_has_correct_type_for_providers(self):
        settings = get_settings()
        assert isinstance(settings.copy_provider, AIProvider)
        assert isinstance(settings.image_provider, AIProvider)
        assert isinstance(settings.analysis_provider, AIProvider)
