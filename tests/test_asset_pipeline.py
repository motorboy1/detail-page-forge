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
