"""Shared fixtures for benchmark tests.

All fixtures use deterministic, mocked data — no real AI API calls.
"""

from __future__ import annotations

import pytest

from detail_forge.copywriter.generator import ProductInfo, SectionCopy
from detail_forge.designer.design_tokens import DesignToken, DesignTokenSet
from detail_forge.templates.models import SlotMapping, TemplateMetadata
from detail_forge.templates.store import TemplateStore

# ---------------------------------------------------------------------------
# Design token helpers
# ---------------------------------------------------------------------------


def make_tokens(**overrides: str) -> DesignTokenSet:
    """Create a minimal DesignTokenSet for benchmarks."""
    base = {
        "--df-color-primary": ("#e74c3c", "color"),
        "--df-color-accent": ("#f39c12", "color"),
        "--df-color-bg": ("#ffffff", "color"),
        "--df-font-heading": ("'Noto Sans KR', sans-serif", "typography"),
        "--df-font-body": ("'Noto Sans KR', sans-serif", "typography"),
        "--df-spacing-section": ("70px 44px", "spacing"),
        "--df-spacing-element": ("24px", "spacing"),
    }
    for key, val in overrides.items():
        cat = "color" if "-color-" in key else "typography" if "-font-" in key else "spacing"
        base[key] = (val, cat)
    return DesignTokenSet(
        tokens=[DesignToken(css_name=n, css_value=v, category=c) for n, (v, c) in base.items()]
    )


# ---------------------------------------------------------------------------
# Product / copy fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def bench_product() -> ProductInfo:
    """Reusable product info for all benchmarks (session-scoped for speed)."""
    return ProductInfo(
        name="벤치마크 스킨케어 세럼",
        features=["히알루론산 3중 보습", "비타민C 함유", "피부 탄력 개선"],
        target_audience="20-30대 여성",
        price_range="3만원대",
        usp="24시간 지속 보습",
    )


@pytest.fixture(scope="session")
def bench_copy_hero() -> SectionCopy:
    return SectionCopy(
        section_index=0,
        section_type="hero",
        headline="최고의 보습 세럼",
        subheadline="피부를 촉촉하게",
        body="하루 종일 촉촉함이 지속됩니다. 히알루론산이 피부 깊숙이 침투합니다.",
        cta_text="지금 구매하기",
    )


@pytest.fixture(scope="session")
def bench_copy_features() -> SectionCopy:
    return SectionCopy(
        section_index=1,
        section_type="features",
        headline="3가지 핵심 성분",
        subheadline="피부과학 기반 포뮬러",
        body="히알루론산, 비타민C, 레티놀의 시너지 효과. 임상 테스트 완료.",
        cta_text="성분 더 알아보기",
    )


@pytest.fixture(scope="session")
def bench_copy_sections(bench_copy_hero, bench_copy_features) -> list[SectionCopy]:
    return [bench_copy_hero, bench_copy_features]


@pytest.fixture(scope="session")
def bench_tokens() -> DesignTokenSet:
    return make_tokens()


# ---------------------------------------------------------------------------
# Template store fixture (in-memory temp dir)
# ---------------------------------------------------------------------------


HERO_HTML = """
<section class="hero">
  <h1 data-slot="text_0">Hero Headline</h1>
  <h2 data-slot="text_1">Hero Subheadline</h2>
  <p data-slot="text_2">Body text here.</p>
  <a data-slot="text_3" href="#">CTA</a>
  <img data-slot="img_0" src="placeholder.jpg" alt="product" />
  <img data-slot="img_1" src="placeholder2.jpg" alt="bg" />
</section>
"""

FEATURES_HTML = """
<section class="features">
  <h2 data-slot="text_0">Features Title</h2>
  <p data-slot="text_1">Feature description.</p>
  <a data-slot="text_2" href="#">Learn More</a>
</section>
"""

HERO_SLOT_MAPPING = SlotMapping(
    headline="text_0",
    subheadline="text_1",
    body=["text_2"],
    cta_text="text_3",
    product_image="img_0",
    background_image="img_1",
)

FEATURES_SLOT_MAPPING = SlotMapping(
    headline="text_0",
    body=["text_1"],
    cta_text="text_2",
)


@pytest.fixture(scope="session")
def bench_store(tmp_path_factory) -> TemplateStore:
    """Session-scoped TemplateStore with pre-populated templates."""
    store_dir = tmp_path_factory.mktemp("bench_templates")
    store = TemplateStore(base_dir=store_dir)

    # Hero template
    hero_meta = TemplateMetadata(
        id="bench-hero-01",
        name="Benchmark Hero",
        section_type="hero",
        d1000_principles=[1, 15, 21],
        category="beauty",
        source_url="https://example.com",
        ssim_score=0.95,
        slot_count=4,
        tags=["hero", "benchmark"],
    )
    store.add_template(
        metadata=hero_meta,
        html=HERO_HTML,
        slots={"text_0": "headline", "text_1": "subheadline", "text_2": "body", "text_3": "cta", "img_0": "image"},
        slot_mapping=HERO_SLOT_MAPPING,
    )

    # Features template
    features_meta = TemplateMetadata(
        id="bench-features-01",
        name="Benchmark Features",
        section_type="features",
        d1000_principles=[3, 21],
        category="beauty",
        source_url="https://example.com",
        ssim_score=0.90,
        slot_count=3,
        tags=["features", "benchmark"],
    )
    store.add_template(
        metadata=features_meta,
        html=FEATURES_HTML,
        slots={"text_0": "headline", "text_1": "body", "text_2": "cta"},
        slot_mapping=FEATURES_SLOT_MAPPING,
    )

    return store


@pytest.fixture(scope="session")
def bench_template_ids() -> list[str]:
    return ["bench-hero-01", "bench-features-01"]


# ---------------------------------------------------------------------------
# Composed HTML fixtures (pre-computed once per session for output benchmarks)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def bench_assembled_html(bench_store, bench_copy_sections, bench_tokens, bench_template_ids) -> str:
    """Full assembled HTML for renderer/quality benchmarks."""
    from detail_forge.synthesis.coherence_engine import CoherenceEngine
    from detail_forge.synthesis.page_assembler import PageAssembler
    from detail_forge.synthesis.section_compositor import SectionCompositor

    compositor = SectionCompositor()
    coherence = CoherenceEngine()
    assembler = PageAssembler(compositor=compositor, coherence=coherence)

    sections_data = []
    for tid, copy in zip(bench_template_ids, bench_copy_sections):
        meta, html, _slots, mapping = bench_store.get_template(tid)
        sections_data.append({
            "template_html": html,
            "copy": copy,
            "slot_mapping": mapping,
        })

    page = assembler.assemble(sections_data=sections_data, tokens=bench_tokens, product_name="벤치마크 세럼")
    return page.html
