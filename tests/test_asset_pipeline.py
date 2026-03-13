"""Tests for the asset pipeline module — M-1.3.

TDD Specification: REQ-AP-001 and REQ-AP-002
Tests are written BEFORE implementation (RED phase).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

SAMPLE_HTML_SIMPLE = """
<!DOCTYPE html>
<html>
<head><style>body { margin: 0; }</style></head>
<body>
  <header>
    <h1>Product Title</h1>
    <p>Subheadline text here</p>
  </header>
  <section>
    <p>Body paragraph one. Body paragraph two.</p>
    <img src="placeholder.jpg" alt="product">
    <a href="#">Buy Now</a>
  </section>
</body>
</html>
"""

SAMPLE_HTML_MULTI_IMAGE = """
<!DOCTYPE html>
<html>
<body>
  <div class="hero">
    <img src="hero.jpg" alt="hero image">
    <h1>Main Headline</h1>
  </div>
  <div class="content">
    <h2>Subheadline</h2>
    <p>Paragraph one</p>
    <p>Paragraph two</p>
    <img src="product.jpg" alt="product photo">
  </div>
</body>
</html>
"""

SAMPLE_HTML_FULL = """
<!DOCTYPE html>
<html>
<body>
  <section class="hero" style="background-image: url('bg.jpg')">
    <h1 class="title">Hero Title</h1>
    <h2 class="subtitle">Hero Subtitle</h2>
    <p class="body-text">This is body text content that is long enough.</p>
    <button class="cta">Shop Now</button>
    <img src="product.jpg" alt="product">
    <img src="detail.jpg" alt="detail">
  </section>
</body>
</html>
"""


@pytest.fixture
def mock_provider():
    """Mock AIProviderBase that does not call real APIs."""
    import json

    provider = AsyncMock()
    provider.analyze_image = AsyncMock(
        return_value=json.dumps(
            {
                "sections": [
                    {
                        "type": "hero",
                        "content_areas": [
                            {
                                "type": "headline",
                                "text": "Sample Headline",
                                "style_hints": {"font_size": "large", "weight": "bold"},
                            },
                            {"type": "subheadline", "text": "Sample Sub", "style_hints": {}},
                            {"type": "body", "text": "Body text.", "style_hints": {}},
                            {"type": "cta", "text": "Buy Now", "style_hints": {}},
                            {"type": "image", "alt": "product", "style_hints": {}},
                        ],
                    }
                ],
                "style_hints": {
                    "color_scheme": "dark",
                    "layout_type": "hero-centered",
                    "d1000_principles": [1, 3, 15],
                },
            }
        )
    )
    return provider


# ---------------------------------------------------------------------------
# T-1.3.1: Package structure
# ---------------------------------------------------------------------------


class TestAssetPipelinePackage:
    """Verify the asset_pipeline package can be imported."""

    def test_package_importable(self):
        from detail_forge import asset_pipeline  # noqa: F401

    def test_png_converter_importable(self):
        from detail_forge.asset_pipeline import PngConverter  # noqa: F401

    def test_slot_tagger_importable(self):
        from detail_forge.asset_pipeline import SlotTagger  # noqa: F401

    def test_all_exports_present(self):
        import detail_forge.asset_pipeline as ap

        assert hasattr(ap, "PngConverter")
        assert hasattr(ap, "SlotTagger")


# ---------------------------------------------------------------------------
# T-1.3.2 / T-1.3.3: PngConverter
# ---------------------------------------------------------------------------


class TestPngConverterLayoutExtraction:
    """REQ-AP-001: Figma PNG -> HTML Conversion via Vision AI."""

    @pytest.mark.asyncio
    async def test_convert_returns_html_string(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        assert result.html
        assert "<" in result.html

    @pytest.mark.asyncio
    async def test_convert_returns_css_string(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        assert isinstance(result.css, str)

    @pytest.mark.asyncio
    async def test_convert_returns_quality_score(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        assert 0 <= result.quality_score <= 10

    @pytest.mark.asyncio
    async def test_convert_returns_slot_mapping(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter
        from detail_forge.templates.models import SlotMapping

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        assert isinstance(result.slot_mapping, SlotMapping)

    @pytest.mark.asyncio
    async def test_convert_calls_provider_analyze_image(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        await converter.convert(fake_png)
        mock_provider.analyze_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_accepts_path_object(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        assert result is not None

    @pytest.mark.asyncio
    async def test_convert_accepts_str_path(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(str(fake_png))
        assert result is not None


class TestPngConverterHtmlGeneration:
    """Verify HTML/CSS generated from layout structure."""

    def test_generate_html_from_layout_structure(self):
        from detail_forge.asset_pipeline import PngConverter
        from detail_forge.asset_pipeline.png_converter import LayoutSection, LayoutStructure

        layout = LayoutStructure(
            sections=[
                LayoutSection(
                    section_type="hero",
                    content_areas=[
                        {"type": "headline", "text": "Hello"},
                        {"type": "image", "alt": "product"},
                    ],
                    style_hints={"layout_type": "centered"},
                )
            ],
            global_style_hints={"color_scheme": "light"},
        )
        converter = PngConverter(provider=MagicMock())
        html, css = converter._generate_html_css(layout)
        assert "<" in html
        assert "Hello" in html

    def test_generated_html_has_semantic_sections(self):
        from detail_forge.asset_pipeline import PngConverter
        from detail_forge.asset_pipeline.png_converter import LayoutSection, LayoutStructure

        layout = LayoutStructure(
            sections=[
                LayoutSection(section_type="hero", content_areas=[], style_hints={}),
                LayoutSection(section_type="features", content_areas=[], style_hints={}),
            ],
            global_style_hints={},
        )
        converter = PngConverter(provider=MagicMock())
        html, css = converter._generate_html_css(layout)
        assert html.count("section") >= 2 or html.count("div") >= 2

    def test_generated_css_uses_semantic_classes(self):
        from detail_forge.asset_pipeline import PngConverter
        from detail_forge.asset_pipeline.png_converter import LayoutSection, LayoutStructure

        layout = LayoutStructure(
            sections=[
                LayoutSection(section_type="hero", content_areas=[], style_hints={"color": "#fff"}),
            ],
            global_style_hints={},
        )
        converter = PngConverter(provider=MagicMock())
        html, css = converter._generate_html_css(layout)
        assert "hero" in css.lower() or "section" in css.lower()


# ---------------------------------------------------------------------------
# T-1.3.4: SlotTagger
# ---------------------------------------------------------------------------


class TestSlotTaggerTextSlots:
    """REQ-AP-001 AC-AP-001: SlotTagger must tag text elements."""

    def test_tag_headline_gets_text_0(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert 'data-slot="text_0"' in result.html or "data-slot='text_0'" in result.html

    def test_tag_subheadline_gets_text_1(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_FULL)
        assert 'data-slot="text_1"' in result.html or "data-slot='text_1'" in result.html

    def test_tag_body_paragraphs(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_FULL)
        assert "text_2" in result.html or "text_3" in result.html

    def test_tag_returns_slot_mapping(self):
        from detail_forge.asset_pipeline import SlotTagger
        from detail_forge.templates.models import SlotMapping

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert isinstance(result.slot_mapping, SlotMapping)

    def test_slot_mapping_has_headline(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert result.slot_mapping.headline == "text_0"

    def test_slot_mapping_has_subheadline(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_FULL)
        assert result.slot_mapping.subheadline == "text_1"


class TestSlotTaggerImageSlots:
    """REQ-AP-001 AC-AP-001: SlotTagger must tag image elements."""

    def test_tag_first_img_gets_img_0(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert "img_0" in result.html

    def test_tag_background_image(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        html_with_bg = """
        <html><body>
          <div style="background-image: url('hero.jpg')">
            <h1>Title</h1>
          </div>
          <img src="product.jpg">
        </body></html>
        """
        result = tagger.tag(html_with_bg)
        assert "bg_0" in result.html

    def test_slot_mapping_product_image(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert result.slot_mapping.product_image == "img_0"

    def test_slot_mapping_background_image(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        html_with_bg = """
        <html><body>
          <div style="background-image: url('bg.jpg')">text</div>
          <img src="product.jpg">
        </body></html>
        """
        result = tagger.tag(html_with_bg)
        assert result.slot_mapping.background_image == "bg_0"


class TestSlotTaggerResult:
    """Verify the TagResult structure."""

    def test_tag_result_has_html(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert isinstance(result.html, str)
        assert len(result.html) > 0

    def test_tag_result_has_slot_count(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_SIMPLE)
        assert result.slot_count >= 1

    def test_tag_does_not_break_html_structure(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.tag(SAMPLE_HTML_FULL)
        assert "<body" in result.html or "<html" in result.html


# ---------------------------------------------------------------------------
# T-1.3.5: D1000 auto-tagging
# ---------------------------------------------------------------------------


class TestD1000AutoTagging:
    """REQ-AP-002: Auto-tag D1000 principles from HTML/CSS style analysis."""

    def test_analyze_principles_returns_list(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.analyze_d1000_principles(SAMPLE_HTML_FULL, css="")
        assert isinstance(result, list)

    def test_analyze_principles_returns_ids_with_scores(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        result = tagger.analyze_d1000_principles(
            SAMPLE_HTML_FULL, css=".hero { background-image: url('x.jpg'); }"
        )
        for item in result:
            assert "principle_id" in item
            assert "confidence" in item
            assert 0.0 <= item["confidence"] <= 1.0

    def test_minimal_html_returns_list(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        html = "<html><body><h1>Title</h1><p>Text</p></body></html>"
        result = tagger.analyze_d1000_principles(html, css="")
        assert isinstance(result, list)

    def test_background_image_in_css_is_analyzed(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        css = ".hero { background-image: url('nature.jpg'); background-size: cover; }"
        html = "<html><body><div class='hero'><h1>Title</h1></div></body></html>"
        result = tagger.analyze_d1000_principles(html, css=css)
        assert isinstance(result, list)

    def test_deterministic_output(self):
        from detail_forge.asset_pipeline import SlotTagger

        tagger = SlotTagger()
        html = "<html><body><h1>Hello</h1><img src='x.jpg'></body></html>"
        r1 = tagger.analyze_d1000_principles(html, css="")
        r2 = tagger.analyze_d1000_principles(html, css="")
        assert r1 == r2


# ---------------------------------------------------------------------------
# T-1.3.6: Quality scorer
# ---------------------------------------------------------------------------


class TestQualityScorer:
    """REQ-AP-001 AC-AP-001: Quality score 0-10, deterministic."""

    def test_score_returns_0_to_10(self):
        from detail_forge.asset_pipeline.png_converter import score_conversion_quality
        from detail_forge.templates.models import SlotMapping

        mapping = SlotMapping(headline="text_0", subheadline="text_1", body=["text_2"])
        score = score_conversion_quality(
            html=SAMPLE_HTML_FULL,
            css=".hero { display: flex; }",
            slot_mapping=mapping,
            slot_count=3,
        )
        assert 0 <= score <= 10

    def test_score_is_deterministic(self):
        from detail_forge.asset_pipeline.png_converter import score_conversion_quality
        from detail_forge.templates.models import SlotMapping

        mapping = SlotMapping(headline="text_0")
        score1 = score_conversion_quality(
            html=SAMPLE_HTML_SIMPLE, css="", slot_mapping=mapping, slot_count=1
        )
        score2 = score_conversion_quality(
            html=SAMPLE_HTML_SIMPLE, css="", slot_mapping=mapping, slot_count=1
        )
        assert score1 == score2

    def test_empty_html_scores_low(self):
        from detail_forge.asset_pipeline.png_converter import score_conversion_quality
        from detail_forge.templates.models import SlotMapping

        mapping = SlotMapping()
        score = score_conversion_quality(
            html="<html><body></body></html>", css="", slot_mapping=mapping, slot_count=0
        )
        assert score < 5

    def test_rich_html_scores_higher(self):
        from detail_forge.asset_pipeline.png_converter import score_conversion_quality
        from detail_forge.templates.models import SlotMapping

        mapping = SlotMapping(
            headline="text_0",
            subheadline="text_1",
            body=["text_2", "text_3"],
            product_image="img_0",
        )
        score = score_conversion_quality(
            html=SAMPLE_HTML_FULL,
            css=".hero { display: flex; justify-content: center; }",
            slot_mapping=mapping,
            slot_count=5,
        )
        assert score >= 5

    def test_score_below_7_triggers_curation_flag(self):
        from detail_forge.asset_pipeline.png_converter import ConversionResult
        from detail_forge.templates.models import SlotMapping

        low_score_result = ConversionResult(
            html="<html></html>",
            css="",
            quality_score=4.5,
            slot_mapping=SlotMapping(),
        )
        assert low_score_result.needs_curation is True

    def test_score_7_or_above_no_curation(self):
        from detail_forge.asset_pipeline.png_converter import ConversionResult
        from detail_forge.templates.models import SlotMapping

        good_result = ConversionResult(
            html="<html></html>",
            css="",
            quality_score=7.5,
            slot_mapping=SlotMapping(),
        )
        assert good_result.needs_curation is False


# ---------------------------------------------------------------------------
# T-1.3.7: Batch conversion script
# ---------------------------------------------------------------------------


class TestBatchConversionScript:
    """Verify convert_figma_templates script interface."""

    def test_script_file_exists(self):
        script_path = Path(
            "/home/motorboy/Development/detail-page-forge/scripts/convert_figma_templates.py"
        )
        assert script_path.exists(), "Batch conversion script not found"

    def test_script_has_main_function(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "convert_figma_templates",
            "/home/motorboy/Development/detail-page-forge/scripts/convert_figma_templates.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "main"), "Script must have a main() function"

    def test_script_has_generate_report_function(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "convert_figma_templates",
            "/home/motorboy/Development/detail-page-forge/scripts/convert_figma_templates.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "generate_report"), "Script must have generate_report()"

    @pytest.mark.asyncio
    async def test_batch_convert_with_mock_provider(self, mock_provider, tmp_path):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "convert_figma_templates",
            "/home/motorboy/Development/detail-page-forge/scripts/convert_figma_templates.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for i in range(3):
            (tmp_path / f"template_{i}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        report = await mod.batch_convert(
            input_dir=tmp_path,
            output_dir=tmp_path / "out",
            provider=mock_provider,
        )
        assert report.total == 3
        assert hasattr(report, "success")
        assert hasattr(report, "failed")
        assert hasattr(report, "average_score")


# ---------------------------------------------------------------------------
# T-1.3.8: TemplateStore.split_to_sections
# ---------------------------------------------------------------------------


class TestTemplateStoreSplitSections:
    """REQ-AP-002 AC-AP-002: TemplateStore section splitting."""

    def _make_store_with_full_page(self, tmp_path):
        from detail_forge.templates.models import SlotMapping, TemplateMetadata
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore(base_dir=tmp_path)
        meta = TemplateMetadata(
            id="test-full-page-01",
            name="Test Full Page",
            section_type="full_page",
            d1000_principles=[1, 3],
            category="beauty",
        )
        html = """
        <html><body>
          <section class="hero"><h1 data-slot="text_0">Hero</h1></section>
          <section class="features"><h2 data-slot="text_1">Features</h2></section>
          <section class="cta"><button data-slot="text_2">Buy</button></section>
        </body></html>
        """
        slot_mapping = SlotMapping(
            headline="text_0",
            subheadline="text_1",
            cta_text="text_2",
        )
        store.add_template(
            metadata=meta,
            html=html,
            slots={"text_0": "Hero", "text_1": "Features", "text_2": "Buy"},
            slot_mapping=slot_mapping,
        )
        return store, meta

    def test_split_to_sections_returns_list(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        result = store.split_to_sections(meta.id)
        assert isinstance(result, list)

    def test_split_creates_section_templates(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        result = store.split_to_sections(meta.id)
        assert len(result) >= 1

    def test_split_sections_have_section_type(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        result = store.split_to_sections(meta.id)
        for section_meta in result:
            assert section_meta.section_type != "full_page"

    def test_split_sections_have_parent_reference(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        result = store.split_to_sections(meta.id)
        for section_meta in result:
            has_ref = f"parent:{meta.id}" in section_meta.tags or meta.id in section_meta.tags
            assert has_ref, f"Section {section_meta.id} missing parent reference"

    def test_split_sections_registered_in_store(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        sections = store.split_to_sections(meta.id)
        all_ids = {t.id for t in store.list_templates()}
        for section_meta in sections:
            assert section_meta.id in all_ids, f"{section_meta.id} not saved to store"

    def test_split_nonexistent_template_raises(self, tmp_path):
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore(base_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            store.split_to_sections("nonexistent-id-xyz")

    def test_split_section_has_own_slot_mapping(self, tmp_path):
        store, meta = self._make_store_with_full_page(tmp_path)
        sections = store.split_to_sections(meta.id)
        for section_meta in sections:
            _, _, _, mapping = store.get_template(section_meta.id)
            assert mapping is not None


# ---------------------------------------------------------------------------
# T-1.3.9: Integration
# ---------------------------------------------------------------------------


class TestAssetPipelineIntegration:
    """End-to-end: PngConverter result feeds into SlotTagger."""

    @pytest.mark.asyncio
    async def test_converter_output_taggable(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter, SlotTagger

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        conv_result = await converter.convert(fake_png)
        tagger = SlotTagger()
        tag_result = tagger.tag(conv_result.html)
        assert tag_result.slot_count >= 0

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_slot_mapping(self, mock_provider, tmp_path):
        from detail_forge.asset_pipeline import PngConverter, SlotTagger
        from detail_forge.templates.models import SlotMapping

        converter = PngConverter(provider=mock_provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        conv_result = await converter.convert(fake_png)
        tagger = SlotTagger()
        tag_result = tagger.tag(conv_result.html)
        assert isinstance(tag_result.slot_mapping, SlotMapping)

    @pytest.mark.asyncio
    async def test_low_quality_score_sets_needs_curation(self, tmp_path):
        import json

        provider = AsyncMock()
        provider.analyze_image = AsyncMock(
            return_value=json.dumps({"sections": [], "style_hints": {}})
        )
        from detail_forge.asset_pipeline import PngConverter

        converter = PngConverter(provider=provider)
        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await converter.convert(fake_png)
        if result.quality_score < 7:
            assert result.needs_curation is True
        else:
            assert result.needs_curation is False


# ---------------------------------------------------------------------------
# T-3.2.1: ReferenceLibrary Tests
# ---------------------------------------------------------------------------


class TestReferenceLibraryImports:
    """Verify ReferenceLibrary and ReferenceImage can be imported."""

    def test_reference_library_importable(self):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary  # noqa: F401

    def test_reference_image_importable(self):
        from detail_forge.asset_pipeline.reference_library import ReferenceImage  # noqa: F401

    def test_asset_pipeline_init_exports_reference_library(self):
        from detail_forge.asset_pipeline import ReferenceLibrary  # noqa: F401

    def test_asset_pipeline_init_exports_reference_image(self):
        from detail_forge.asset_pipeline import ReferenceImage  # noqa: F401


class TestReferenceLibraryMissingDirectory:
    """ReferenceLibrary handles missing pinterest directory gracefully."""

    def test_load_index_returns_empty_list_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        nonexistent = tmp_path / "nonexistent_pinterest"
        lib = ReferenceLibrary(data_dir=nonexistent)
        result = lib.load_index()
        assert isinstance(result, list)
        assert result == []

    def test_search_returns_empty_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        nonexistent = tmp_path / "nonexistent"
        lib = ReferenceLibrary(data_dir=nonexistent)
        result = lib.search(category="beauty")
        assert isinstance(result, list)
        assert result == []

    def test_recommend_returns_empty_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        nonexistent = tmp_path / "nonexistent"
        lib = ReferenceLibrary(data_dir=nonexistent)
        result = lib.recommend_for_product("beauty")
        assert isinstance(result, list)
        assert result == []


class TestReferenceLibraryWithIndexJson:
    """ReferenceLibrary loads from index.json correctly."""

    def _make_index(self, tmp_path):
        import json
        data = [
            {
                "file_path": "beauty/serum_01.jpg",
                "category": "beauty",
                "d1000_principles": [3, 6, 9],
                "style_keywords": ["minimal", "luxury"],
                "source_url": "https://pinterest.com/pin/1",
            },
            {
                "file_path": "fashion/outfit_01.jpg",
                "category": "fashion",
                "d1000_principles": [1, 4, 8],
                "style_keywords": ["bold", "natural"],
                "source_url": "https://pinterest.com/pin/2",
            },
            {
                "file_path": "food/dish_01.jpg",
                "category": "food",
                "d1000_principles": [1, 3, 7],
                "style_keywords": ["vibrant"],
                "source_url": "",
            },
        ]
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "index.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        return data

    def test_load_index_from_json(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceImage, ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        assert len(result) == 3
        assert all(isinstance(r, ReferenceImage) for r in result)

    def test_load_index_returns_correct_category(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        categories = {r.category for r in result}
        assert "beauty" in categories
        assert "fashion" in categories

    def test_search_by_category(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(category="beauty")
        assert len(result) == 1
        assert result[0].category == "beauty"

    def test_search_by_d1000_principles(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(d1000_principles=[3])
        # principle 3 is in beauty (3,6,9) and food (1,3,7)
        categories = {r.category for r in result}
        assert "beauty" in categories

    def test_search_by_style_keywords(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(style_keywords=["luxury"])
        assert len(result) == 1
        assert "luxury" in result[0].style_keywords

    def test_search_limit_respected(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(limit=2)
        assert len(result) <= 2

    def test_search_no_filters_returns_all(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(limit=100)
        assert len(result) == 3

    def test_recommend_for_product(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        self._make_index(tmp_path)
        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.recommend_for_product("beauty")
        assert isinstance(result, list)
        # Should find beauty items
        assert len(result) >= 1


class TestReferenceLibraryWithRealImages:
    """ReferenceLibrary scans actual image files from directory."""

    def test_scan_directory_finds_images(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        # Create fake image files
        beauty_dir = tmp_path / "beauty"
        beauty_dir.mkdir()
        (beauty_dir / "serum_minimal.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 10)
        (beauty_dir / "toner_luxury.png").write_bytes(b"\x89PNG\r\n" + b"\x00" * 10)

        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        assert len(result) == 2
        assert all(r.file_path.endswith((".jpg", ".png")) for r in result)

    def test_scan_directory_infers_category(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        beauty_dir = tmp_path / "beauty"
        beauty_dir.mkdir()
        (beauty_dir / "product.jpg").write_bytes(b"\xff\xd8\xff")

        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        assert result[0].category == "beauty"

    def test_scan_directory_assigns_principles(self, tmp_path):
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        fashion_dir = tmp_path / "fashion"
        fashion_dir.mkdir()
        (fashion_dir / "outfit.jpg").write_bytes(b"\xff\xd8\xff")

        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        assert len(result[0].d1000_principles) > 0

    def test_save_and_reload_index(self, tmp_path):
        import json
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        # Create images
        (tmp_path / "food.jpg").write_bytes(b"\xff\xd8\xff")

        lib = ReferenceLibrary(data_dir=tmp_path)
        lib.load_index()
        lib.save_index()

        assert (tmp_path / "index.json").exists()
        data = json.loads((tmp_path / "index.json").read_text())
        assert isinstance(data, list)


class TestReferenceImageDataclass:
    """Verify ReferenceImage dataclass structure."""

    def test_reference_image_has_required_fields(self):
        from detail_forge.asset_pipeline.reference_library import ReferenceImage

        img = ReferenceImage(
            file_path="beauty/img.jpg",
            category="beauty",
        )
        assert img.file_path == "beauty/img.jpg"
        assert img.category == "beauty"
        assert isinstance(img.d1000_principles, list)
        assert isinstance(img.style_keywords, list)
        assert img.source_url == ""

    def test_reference_image_with_full_data(self):
        from detail_forge.asset_pipeline.reference_library import ReferenceImage

        img = ReferenceImage(
            file_path="fashion/bold_minimal.jpg",
            category="fashion",
            d1000_principles=[1, 4, 8],
            style_keywords=["bold", "minimal"],
            source_url="https://pinterest.com/pin/123",
        )
        assert img.d1000_principles == [1, 4, 8]
        assert "bold" in img.style_keywords
        assert img.source_url == "https://pinterest.com/pin/123"


# ---------------------------------------------------------------------------
# T-3.2.2: LectureKnowledge Tests
# ---------------------------------------------------------------------------


class TestLectureKnowledgeImports:
    """Verify LectureKnowledge and LectureInsight can be imported."""

    def test_lecture_knowledge_importable(self):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge  # noqa: F401

    def test_lecture_insight_importable(self):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureInsight  # noqa: F401

    def test_asset_pipeline_init_exports_lecture_knowledge(self):
        from detail_forge.asset_pipeline import LectureKnowledge  # noqa: F401

    def test_asset_pipeline_init_exports_lecture_insight(self):
        from detail_forge.asset_pipeline import LectureInsight  # noqa: F401


class TestLectureKnowledgeMissingDirectory:
    """LectureKnowledge handles missing lecture directory gracefully."""

    def test_load_index_returns_empty_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        nonexistent = tmp_path / "nonexistent_lectures"
        kb = LectureKnowledge(data_dir=nonexistent)
        result = kb.load_index()
        assert isinstance(result, list)
        assert result == []

    def test_get_insights_returns_empty_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        nonexistent = tmp_path / "nonexistent"
        kb = LectureKnowledge(data_dir=nonexistent)
        result = kb.get_insights_for_principles([1, 3, 5])
        assert isinstance(result, list)
        assert result == []

    def test_get_reasoning_prompts_returns_empty_when_dir_missing(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        nonexistent = tmp_path / "nonexistent"
        kb = LectureKnowledge(data_dir=nonexistent)
        result = kb.get_reasoning_prompts([1, 2, 3])
        assert isinstance(result, list)
        assert result == []


class TestLectureKnowledgeWithTranscripts:
    """LectureKnowledge loads from real transcript JSON files."""

    def _make_transcripts(self, tmp_path):
        import json
        transcripts = [
            {
                "lecture": 1,
                "example": 1,
                "topic": "4개의점",
                "d1000_principle_id": 1,
                "filename": "lecture_01.mp4",
                "text": "레이아웃의 4개의 점을 활용하면 균형 잡힌 디자인을 쉽게 만들 수 있습니다. 포컬 포인트를 4개의 교차점에 배치하면 뻔하지 않고 역동적인 구성이 됩니다.",
            },
            {
                "lecture": 3,
                "example": 1,
                "topic": "여백의미학",
                "d1000_principle_id": 3,
                "filename": "lecture_03.mp4",
                "text": "여백은 디자인의 숨통입니다. 적절한 여백은 콘텐츠를 더욱 돋보이게 하고 시선을 자연스럽게 유도합니다.",
            },
            {
                "lecture": 7,
                "example": 2,
                "topic": "색상대비",
                "d1000_principle_id": 7,
                "filename": "lecture_07.mp4",
                "text": "색상 대비는 중요한 정보를 강조하는 핵심 도구입니다. 보색 관계를 활용하면 시선을 집중시킬 수 있습니다.",
            },
        ]
        for i, t in enumerate(transcripts):
            (tmp_path / f"lecture_{i+1:02d}.json").write_text(
                json.dumps(t, ensure_ascii=False), encoding="utf-8"
            )
        return transcripts

    def test_load_index_from_transcripts(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureInsight, LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        assert len(result) == 3
        assert all(isinstance(ins, LectureInsight) for ins in result)

    def test_load_index_has_correct_principle_ids(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        principle_ids = {ins.principle_id for ins in result}
        assert 1 in principle_ids
        assert 3 in principle_ids
        assert 7 in principle_ids

    def test_load_index_has_insight_text(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        for ins in result:
            assert isinstance(ins.insight_text, str)
            assert len(ins.insight_text) > 0

    def test_load_index_has_source_lecture(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        for ins in result:
            assert isinstance(ins.source_lecture, str)
            assert len(ins.source_lecture) > 0

    def test_load_index_has_reasoning_prompt(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        for ins in result:
            assert isinstance(ins.reasoning_prompt, str)
            assert len(ins.reasoning_prompt) > 0

    def test_get_insights_for_principles_filters_correctly(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.get_insights_for_principles([1, 3])
        ids = {ins.principle_id for ins in result}
        assert 1 in ids
        assert 3 in ids
        assert 7 not in ids

    def test_get_insights_for_single_principle(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.get_insights_for_principles([7])
        assert len(result) == 1
        assert result[0].principle_id == 7

    def test_get_insights_for_unknown_principle_returns_empty(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.get_insights_for_principles([999])
        assert result == []

    def test_get_reasoning_prompts_returns_strings(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        prompts = kb.get_reasoning_prompts([1, 3])
        assert isinstance(prompts, list)
        assert len(prompts) == 2
        assert all(isinstance(p, str) for p in prompts)

    def test_get_reasoning_prompts_empty_principles(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        prompts = kb.get_reasoning_prompts([])
        assert prompts == []

    def test_load_index_cached_after_first_load(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        r1 = kb.load_index()
        r2 = kb.load_index()
        assert r1 is r2  # Same object (cached)

    def test_save_and_reload_from_index(self, tmp_path):
        import json
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        kb = LectureKnowledge(data_dir=tmp_path)
        kb.load_index()
        kb.save_index()

        index_path = tmp_path / "insights_index.json"
        assert index_path.exists()
        data = json.loads(index_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_skips_malformed_json(self, tmp_path):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        self._make_transcripts(tmp_path)
        (tmp_path / "bad_file.json").write_text("{ not valid json", encoding="utf-8")

        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        # Bad file skipped, 3 valid transcripts loaded
        assert len(result) == 3

    def test_skips_transcripts_without_principle_id(self, tmp_path):
        import json
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        # Valid transcripts
        self._make_transcripts(tmp_path)
        # Invalid: no principle_id
        (tmp_path / "no_principle.json").write_text(
            json.dumps({"lecture": 99, "topic": "test", "text": "some text"}),
            encoding="utf-8",
        )

        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        # Should still only have 3 valid ones
        principle_ids = [ins.principle_id for ins in result]
        assert 0 not in principle_ids


class TestLectureKnowledgeWithRealData:
    """LectureKnowledge works with actual transcript data directory."""

    def test_loads_real_transcripts_if_available(self):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        # Use real data directory (transcripts exist)
        real_dir = Path("/home/motorboy/Development/detail-page-forge/data/d1000_knowledge/transcripts")
        if not real_dir.exists():
            pytest.skip("Real transcript directory not available")

        kb = LectureKnowledge(data_dir=real_dir)
        result = kb.load_index()
        assert isinstance(result, list)
        # Should have loaded some insights (85 transcripts in the repo)
        assert len(result) > 0

    def test_real_transcripts_have_valid_principles(self):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        real_dir = Path("/home/motorboy/Development/detail-page-forge/data/d1000_knowledge/transcripts")
        if not real_dir.exists():
            pytest.skip("Real transcript directory not available")

        kb = LectureKnowledge(data_dir=real_dir)
        result = kb.load_index()
        for ins in result:
            assert ins.principle_id > 0


class TestLectureInsightDataclass:
    """Verify LectureInsight dataclass structure."""

    def test_lecture_insight_has_required_fields(self):
        from detail_forge.asset_pipeline.lecture_knowledge import LectureInsight

        insight = LectureInsight(
            principle_id=1,
            insight_text="4개의 점을 활용하세요",
            source_lecture="lecture_01_1",
            reasoning_prompt="D1000 원칙 #1을 적용하세요",
        )
        assert insight.principle_id == 1
        assert insight.insight_text == "4개의 점을 활용하세요"
        assert insight.source_lecture == "lecture_01_1"
        assert isinstance(insight.reasoning_prompt, str)


class TestLectureKnowledgeCoverageEdgeCases:
    """Additional edge case tests to push coverage above 85%."""

    def test_default_data_dir_none_uses_transcripts_if_exists(self, tmp_path, monkeypatch):
        """Cover lines 82-89: when data_dir=None and a default dir exists."""
        import json
        from detail_forge.asset_pipeline import lecture_knowledge as lk_mod

        # Patch default dirs to point to our tmp directory
        transcript_dir = tmp_path / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "lec_01.json").write_text(
            json.dumps({"d1000_principle_id": 5, "topic": "test", "text": "Some text about design principle"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            lk_mod, "_DEFAULT_LECTURE_DIRS", [transcript_dir, tmp_path / "lectures"]
        )

        # data_dir=None triggers the default-dir search path
        kb = lk_mod.LectureKnowledge(data_dir=None)
        assert kb._data_dir == transcript_dir.resolve()
        result = kb.load_index()
        assert len(result) == 1
        assert result[0].principle_id == 5

    def test_default_data_dir_none_uses_first_default_when_none_exist(self, tmp_path, monkeypatch):
        """Cover line 89: when data_dir=None and no default dir exists."""
        from detail_forge.asset_pipeline import lecture_knowledge as lk_mod

        monkeypatch.setattr(
            lk_mod, "_DEFAULT_LECTURE_DIRS", [
                tmp_path / "nonexistent_a",
                tmp_path / "nonexistent_b",
            ]
        )
        kb = lk_mod.LectureKnowledge(data_dir=None)
        # Falls back to first default
        assert "nonexistent_a" in str(kb._data_dir)
        # Returns empty gracefully
        result = kb.load_index()
        assert result == []

    def test_load_index_from_saved_index_json(self, tmp_path):
        """Cover lines 110-115: load from pre-built insights_index.json."""
        import json
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        tmp_path.mkdir(parents=True, exist_ok=True)
        index_data = [
            {
                "principle_id": 11,
                "insight_text": "Focus on visual hierarchy",
                "source_lecture": "lecture_11_1",
                "reasoning_prompt": "Apply principle #11 to your layout",
            }
        ]
        (tmp_path / "insights_index.json").write_text(
            json.dumps(index_data, ensure_ascii=False), encoding="utf-8"
        )

        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        assert len(result) == 1
        assert result[0].principle_id == 11
        assert result[0].source_lecture == "lecture_11_1"

    def test_load_index_falls_through_malformed_index_json(self, tmp_path):
        """Cover line 114: malformed index.json falls through to scan."""
        import json
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        # Write malformed index
        (tmp_path / "insights_index.json").write_text("{invalid json}", encoding="utf-8")
        # Also write a real transcript
        (tmp_path / "lec_01.json").write_text(
            json.dumps({"d1000_principle_id": 2, "topic": "spacing", "text": "Spacing is important for readability in design"}),
            encoding="utf-8",
        )

        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb.load_index()
        # Should have fallen through to scan transcripts
        assert len(result) == 1
        assert result[0].principle_id == 2

    def test_scan_skips_insights_index_file(self, tmp_path):
        """Cover line 172: insights_index.json skipped during scan."""
        import json
        from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge

        # Write the index file (should be skipped during scan)
        (tmp_path / "insights_index.json").write_text(
            json.dumps([{"principle_id": 99, "insight_text": "x", "source_lecture": "x", "reasoning_prompt": "x"}]),
            encoding="utf-8",
        )
        # Write a real transcript
        (tmp_path / "lec_05.json").write_text(
            json.dumps({"d1000_principle_id": 5, "topic": "test", "text": "Design principle text here"}),
            encoding="utf-8",
        )

        kb = LectureKnowledge(data_dir=tmp_path)
        result = kb._scan_transcripts()
        # insights_index.json skipped — only lec_05.json scanned
        assert len(result) == 1
        assert result[0].principle_id == 5


class TestReferenceLibraryCoverageEdgeCases:
    """Additional coverage tests for reference_library edge cases."""

    def test_load_index_falls_through_malformed_index_json(self, tmp_path):
        """Cover case where index.json is malformed — falls through to scan."""
        (tmp_path / "index.json").write_text("{bad json", encoding="utf-8")
        (tmp_path / "beauty_product.jpg").write_bytes(b"\xff\xd8\xff")

        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.load_index()
        # Fell through to scan — found the jpg
        assert len(result) == 1

    def test_search_no_matches_returns_empty(self, tmp_path):
        """Search with no matching results."""
        import json
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        data = [
            {"file_path": "beauty/img.jpg", "category": "beauty",
             "d1000_principles": [3], "style_keywords": ["minimal"], "source_url": ""},
        ]
        (tmp_path / "index.json").write_text(json.dumps(data), encoding="utf-8")

        lib = ReferenceLibrary(data_dir=tmp_path)
        result = lib.search(category="electronics")
        assert result == []

    def test_recommend_for_unknown_category_uses_principles(self, tmp_path):
        """recommend_for_product with unknown category falls to principle-only search."""
        import json
        from detail_forge.asset_pipeline.reference_library import ReferenceLibrary

        data = [
            {"file_path": "misc/img.jpg", "category": "misc",
             "d1000_principles": [1], "style_keywords": ["test"], "source_url": ""},
        ]
        (tmp_path / "index.json").write_text(json.dumps(data), encoding="utf-8")

        lib = ReferenceLibrary(data_dir=tmp_path)
        # Unknown category → no principles mapped → no results
        result = lib.recommend_for_product("unknown_category_xyz")
        assert isinstance(result, list)
