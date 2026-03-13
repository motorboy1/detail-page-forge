"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AIProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"


class Platform(str, Enum):
    NAVER = "naver"
    COUPANG = "coupang"


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # AI API Keys
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    # Provider selection per phase
    copy_provider: AIProvider = AIProvider.CLAUDE
    image_provider: AIProvider = AIProvider.GEMINI
    analysis_provider: AIProvider = AIProvider.CLAUDE

    # Crawling settings
    max_competitors: int = 5
    crawl_timeout_seconds: int = 30

    # Image generation settings
    candidates_per_section: int = 3
    image_width: int = 860
    image_height: int = 1200

    # Export settings
    coupang_image_width: int = 860
    naver_max_image_kb: int = 500

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    output_dir: Path = Field(default_factory=lambda: Path.home() / "Development" / "detail-page-forge" / "data" / "output")
    references_dir: Path = Field(default_factory=lambda: Path.home() / "Development" / "detail-page-forge" / "data" / "references")

    model_config = {"env_prefix": "DETAIL_FORGE_", "env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
