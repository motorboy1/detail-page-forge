"""Shared pytest fixtures for detail-page-forge test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from detail_forge.copywriter.generator import ProductInfo, SectionCopy
from detail_forge.providers.base import (
    AIProviderBase,
    CopyRequest,
    CopyResponse,
    ImageRequest,
    ImageResponse,
)
from detail_forge.templates.models import SlotMapping, TemplateMetadata

# ── Product fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def sample_product_info() -> ProductInfo:
    """Basic product for use across tests."""
    return ProductInfo(
        name="테스트 스킨케어 세럼",
        features=["히알루론산 3중 보습", "비타민C 함유", "피부 탄력 개선"],
        target_audience="20-30대 여성",
        price_range="3만원대",
        usp="24시간 지속 보습",
    )


@pytest.fixture
def sample_section_copy() -> SectionCopy:
    """A single hero section copy for renderer tests."""
    return SectionCopy(
        section_index=0,
        section_type="hero",
        headline="최고의 보습 세럼",
        subheadline="피부를 촉촉하게",
        body="하루 종일 촉촉함이 지속됩니다. 히알루론산이 피부 깊숙이 침투합니다.",
        cta_text="지금 구매하기",
    )


# ── D1000 principle fixtures ────────────────────────────────────────────────


@pytest.fixture
def sample_principles() -> list[int]:
    """A representative selection of D1000 principle IDs."""
    return [1, 3, 15, 21, 28, 36]


# ── Template model fixtures ─────────────────────────────────────────────────


@pytest.fixture
def sample_template_metadata() -> TemplateMetadata:
    """Minimal valid TemplateMetadata instance."""
    return TemplateMetadata(
        id="test-hero-01",
        name="Test Hero Template",
        section_type="hero",
        d1000_principles=[1, 4, 15],
        category="beauty",
        source_url="https://example.com",
        ssim_score=0.92,
        slot_count=3,
        tags=["minimal", "premium"],
        created_at="2024-01-01T00:00:00+00:00",
    )


@pytest.fixture
def sample_slot_mapping() -> SlotMapping:
    """Slot mapping with common fields populated."""
    return SlotMapping(
        headline="text_0",
        subheadline="text_1",
        body=["text_2", "text_3"],
        cta_text="text_4",
        product_image="img_0",
    )


# ── AI provider mock ────────────────────────────────────────────────────────


class _MockAIProvider(AIProviderBase):
    """Deterministic mock that never calls real APIs."""

    async def generate_copy(self, request: CopyRequest) -> CopyResponse:
        return CopyResponse(
            headline="Mock Headline",
            subheadline="Mock Subheadline",
            body="Mock body text for testing purposes.",
            cta_text="Mock CTA",
            raw_text="Mock raw text",
        )

    async def generate_images(self, request: ImageRequest) -> ImageResponse:
        return ImageResponse(images=[b"fake_image_bytes"], prompts_used=["mock prompt"])

    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        return "Mock image analysis result"


@pytest.fixture
def mock_ai_provider() -> _MockAIProvider:
    """Provide a mock AI provider that never calls real APIs."""
    return _MockAIProvider()


# ── File-system fixtures ────────────────────────────────────────────────────


@pytest.fixture
def tmp_template_dir(tmp_path: Path) -> Path:
    """Temporary directory suitable for TemplateStore tests."""
    store_dir = tmp_path / "templates"
    store_dir.mkdir()
    return store_dir
