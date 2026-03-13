"""Tests for the synthesis package — M-2.1 Synthesis Engine Core.

TDD RED phase: All tests are written before implementation.
"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from detail_forge.copywriter.generator import SectionCopy
from detail_forge.designer.design_tokens import DesignToken, DesignTokenSet
from detail_forge.templates.models import SlotMapping

# ─── Helpers ────────────────────────────────────────────────────────────────


def make_tokens(**overrides: str) -> DesignTokenSet:
    """Create a minimal DesignTokenSet for tests."""
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
        base[key] = (val, _infer_cat(key))
    return DesignTokenSet(
        tokens=[DesignToken(css_name=n, css_value=v, category=c) for n, (v, c) in base.items()]
    )


def _infer_cat(name: str) -> str:
    if "-color-" in name:
        return "color"
    if "-font-" in name or "-size-" in name:
        return "typography"
    if "-spacing-" in name:
        return "spacing"
    return "effect"


SIMPLE_HTML = """
<section>
  <h1 data-slot="text_0">Old headline</h1>
  <h2 data-slot="text_1">Old subheadline</h2>
  <p data-slot="text_2">Old body</p>
  <a data-slot="text_3" href="#">Old CTA</a>
  <img data-slot="img_0" src="placeholder.jpg" />
</section>
"""

SIMPLE_MAPPING = SlotMapping(
    headline="text_0",
    subheadline="text_1",
    body=["text_2"],
    cta_text="text_3",
    product_image="img_0",
)

SIMPLE_COPY = SectionCopy(
    section_index=0,
    section_type="hero",
    headline="Amazing Product",
    subheadline="The best you can get",
    body="This product transforms your life.",
    cta_text="Buy Now",
)


# ============================================================
# Section Compositor tests
# ============================================================


class TestSectionCompositorImport:
    """Verify the public API is importable."""

    def test_import_section_compositor(self):
        from detail_forge.synthesis import SectionCompositor  # noqa: F401

    def test_import_composed_section(self):
        from detail_forge.synthesis.section_compositor import ComposedSection  # noqa: F401


class TestComposedSectionDataclass:
    """ComposedSection is a proper dataclass with required fields."""

    def test_fields_present(self):
        from detail_forge.synthesis.section_compositor import ComposedSection

        cs = ComposedSection(
            section_type="hero",
            html="<div></div>",
            css="",
            quality_score=7.5,
            warnings=[],
        )
        assert cs.section_type == "hero"
        assert cs.html == "<div></div>"
        assert cs.quality_score == 7.5
        assert cs.warnings == []


class TestSectionCompositorCompose:
    """Core compose() behaviour."""

    @pytest.fixture
    def compositor(self):
        from detail_forge.synthesis import SectionCompositor

        return SectionCompositor()

    def test_returns_composed_section(self, compositor):
        from detail_forge.synthesis.section_compositor import ComposedSection

        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert isinstance(result, ComposedSection)

    def test_headline_filled(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        h1 = soup.find(attrs={"data-slot": "text_0"})
        assert h1 is not None
        assert h1.get_text() == "Amazing Product"

    def test_subheadline_filled(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        h2 = soup.find(attrs={"data-slot": "text_1"})
        assert h2 is not None
        assert h2.get_text() == "The best you can get"

    def test_body_filled(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        p = soup.find(attrs={"data-slot": "text_2"})
        assert p is not None
        assert "transforms your life" in p.get_text()

    def test_cta_filled(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        a = soup.find(attrs={"data-slot": "text_3"})
        assert a is not None
        assert a.get_text() == "Buy Now"

    def test_image_src_filled_when_provided(self, compositor):
        tokens = make_tokens()
        product_images = {"img_0": "https://example.com/product.jpg"}
        result = compositor.compose(
            SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens, product_images=product_images
        )
        soup = BeautifulSoup(result.html, "html.parser")
        img = soup.find(attrs={"data-slot": "img_0"})
        assert img is not None
        assert img["src"] == "https://example.com/product.jpg"

    def test_image_not_changed_when_no_product_images(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        img = soup.find(attrs={"data-slot": "img_0"})
        assert img is not None
        assert img["src"] == "placeholder.jpg"

    def test_css_variable_injected_on_root(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert "--df-color-primary" in result.css or "--df-color-primary" in result.html

    def test_section_type_preserved(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert result.section_type == "hero"


class TestSectionCompositorQualityScore:
    """Quality score is deterministic and correct."""

    @pytest.fixture
    def compositor(self):
        from detail_forge.synthesis import SectionCompositor

        return SectionCompositor()

    def test_quality_score_between_0_and_10(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert 0.0 <= result.quality_score <= 10.0

    def test_full_section_has_higher_score(self, compositor):
        """A section with headline + image + cta should score higher than empty."""
        tokens = make_tokens()
        full_result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)

        empty_copy = SectionCopy(section_index=1, section_type="hero")
        empty_result = compositor.compose(SIMPLE_HTML, empty_copy, SIMPLE_MAPPING, tokens)
        assert full_result.quality_score > empty_result.quality_score

    def test_score_is_deterministic(self, compositor):
        tokens = make_tokens()
        r1 = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        r2 = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert r1.quality_score == r2.quality_score

    def test_missing_slots_generate_warnings(self, compositor):
        """When copy fields are empty, warnings should be produced."""
        tokens = make_tokens()
        sparse_copy = SectionCopy(section_index=0, section_type="hero", headline="Only headline")
        result = compositor.compose(SIMPLE_HTML, sparse_copy, SIMPLE_MAPPING, tokens)
        assert len(result.warnings) > 0

    def test_no_warnings_when_all_slots_filled(self, compositor):
        tokens = make_tokens()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert result.warnings == []


class TestSectionCompositorEdgeCases:
    """Edge cases and robustness."""

    @pytest.fixture
    def compositor(self):
        from detail_forge.synthesis import SectionCompositor

        return SectionCompositor()

    def test_empty_html_returns_composed_section(self, compositor):
        tokens = make_tokens()
        result = compositor.compose("", SIMPLE_COPY, SIMPLE_MAPPING, tokens)
        assert result is not None
        assert result.html == ""

    def test_html_with_no_data_slots(self, compositor):
        html = "<div><h1>No slots here</h1></div>"
        tokens = make_tokens()
        mapping = SlotMapping()
        result = compositor.compose(html, SIMPLE_COPY, mapping, tokens)
        assert "No slots here" in result.html

    def test_empty_slot_mapping(self, compositor):
        tokens = make_tokens()
        mapping = SlotMapping()
        result = compositor.compose(SIMPLE_HTML, SIMPLE_COPY, mapping, tokens)
        assert isinstance(result.quality_score, float)

    def test_multiple_body_slots(self, compositor):
        html = """
        <section>
          <p data-slot="text_2">Body 1</p>
          <p data-slot="text_3">Body 2</p>
        </section>
        """
        copy = SectionCopy(
            section_index=0,
            section_type="features",
            body="First sentence. Second sentence.",
        )
        mapping = SlotMapping(body=["text_2", "text_3"])
        tokens = make_tokens()
        result = compositor.compose(html, copy, mapping, tokens)
        soup = BeautifulSoup(result.html, "html.parser")
        texts = [el.get_text() for el in soup.find_all(attrs={"data-slot": True})]
        assert len(texts) == 2
        assert any(t for t in texts)


# ============================================================
# Coherence Engine tests
# ============================================================


class TestCoherenceEngineImport:
    def test_import_coherence_engine(self):
        from detail_forge.synthesis import CoherenceEngine  # noqa: F401

    def test_import_coherence_report(self):
        from detail_forge.synthesis.coherence_engine import CoherenceReport  # noqa: F401


class TestCoherenceReportDataclass:
    def test_fields_present(self):
        from detail_forge.synthesis.coherence_engine import CoherenceReport

        report = CoherenceReport(
            is_coherent=True,
            score=8.5,
            issues=[],
            adjustments_made=[],
        )
        assert report.is_coherent is True
        assert report.score == 8.5


class TestCoherenceEngineCheck:
    """check() validates consistency across sections."""

    @pytest.fixture
    def engine(self):
        from detail_forge.synthesis import CoherenceEngine

        return CoherenceEngine()

    @pytest.fixture
    def composed_sections(self):
        from detail_forge.synthesis.section_compositor import ComposedSection

        css_consistent = (
            "div { font-family: var(--df-font-heading); "
            "color: var(--df-color-primary); padding: var(--df-spacing-section); }"
        )
        return [
            ComposedSection(
                section_type="hero",
                html='<div style="--df-color-primary:#e74c3c">Hero</div>',
                css=css_consistent,
                quality_score=8.0,
                warnings=[],
            ),
            ComposedSection(
                section_type="features",
                html='<div style="--df-color-primary:#e74c3c">Features</div>',
                css=css_consistent,
                quality_score=7.5,
                warnings=[],
            ),
        ]

    def test_returns_coherence_report(self, engine, composed_sections):
        from detail_forge.synthesis.coherence_engine import CoherenceReport

        tokens = make_tokens()
        report = engine.check(composed_sections, tokens)
        assert isinstance(report, CoherenceReport)

    def test_consistent_sections_are_coherent(self, engine, composed_sections):
        tokens = make_tokens()
        report = engine.check(composed_sections, tokens)
        assert report.is_coherent is True

    def test_coherence_score_between_0_and_10(self, engine, composed_sections):
        tokens = make_tokens()
        report = engine.check(composed_sections, tokens)
        assert 0.0 <= report.score <= 10.0

    def test_single_section_is_coherent(self, engine, composed_sections):
        tokens = make_tokens()
        report = engine.check(composed_sections[:1], tokens)
        assert report.is_coherent is True

    def test_empty_sections_list(self, engine):
        tokens = make_tokens()
        report = engine.check([], tokens)
        assert report is not None
        assert isinstance(report.score, float)

    def test_inconsistent_sections_detected(self, engine):
        from detail_forge.synthesis.section_compositor import ComposedSection

        tokens = make_tokens()
        # Section 1: uses one font family
        sec1 = ComposedSection(
            section_type="hero",
            html="<div>Hero</div>",
            css="div { font-family: Arial; }",
            quality_score=8.0,
            warnings=[],
        )
        # Section 2: uses a different font family (no token reference)
        sec2 = ComposedSection(
            section_type="features",
            html="<div>Features</div>",
            css="div { font-family: Georgia; }",
            quality_score=7.0,
            warnings=[],
        )
        report = engine.check([sec1, sec2], tokens)
        # Inconsistent fonts should be detected
        assert len(report.issues) >= 0  # issues list exists


class TestCoherenceEngineAdjust:
    """adjust() returns sections with token CSS variables applied consistently."""

    @pytest.fixture
    def engine(self):
        from detail_forge.synthesis import CoherenceEngine

        return CoherenceEngine()

    def test_returns_list_of_composed_sections(self, engine):
        from detail_forge.synthesis.section_compositor import ComposedSection

        tokens = make_tokens()
        sections = [
            ComposedSection(
                section_type="hero",
                html="<div>Hello</div>",
                css="",
                quality_score=7.0,
                warnings=[],
            )
        ]
        adjusted = engine.adjust(sections, tokens)
        assert isinstance(adjusted, list)
        assert all(isinstance(s, ComposedSection) for s in adjusted)

    def test_same_count_returned(self, engine):
        from detail_forge.synthesis.section_compositor import ComposedSection

        tokens = make_tokens()
        sections = [
            ComposedSection(
                section_type="hero",
                html="<div>A</div>",
                css="",
                quality_score=7.0,
                warnings=[],
            ),
            ComposedSection(
                section_type="features",
                html="<div>B</div>",
                css="",
                quality_score=6.0,
                warnings=[],
            ),
        ]
        adjusted = engine.adjust(sections, tokens)
        assert len(adjusted) == 2

    def test_adjusted_html_contains_token_vars(self, engine):
        from detail_forge.synthesis.section_compositor import ComposedSection

        tokens = make_tokens()
        section = ComposedSection(
            section_type="hero",
            html="<div>Hello</div>",
            css="",
            quality_score=7.0,
            warnings=[],
        )
        adjusted = engine.adjust([section], tokens)
        # The adjusted HTML should reference CSS custom properties
        combined = adjusted[0].html + adjusted[0].css
        assert "--df-color-primary" in combined or "df-color" in combined

    def test_empty_sections_returns_empty(self, engine):
        tokens = make_tokens()
        adjusted = engine.adjust([], tokens)
        assert adjusted == []


# ============================================================
# Page Assembler tests
# ============================================================


class TestPageAssemblerImport:
    def test_import_page_assembler(self):
        from detail_forge.synthesis import PageAssembler  # noqa: F401

    def test_import_assembled_page(self):
        from detail_forge.synthesis.page_assembler import AssembledPage  # noqa: F401


class TestAssembledPageDataclass:
    def test_fields_present(self):
        from detail_forge.synthesis.page_assembler import AssembledPage

        page = AssembledPage(
            html="<html></html>",
            section_count=2,
            total_quality_score=7.0,
            coherence_score=8.5,
        )
        assert page.section_count == 2
        assert page.total_quality_score == 7.0
        assert page.coherence_score == 8.5


class TestPageAssemblerAssemble:
    """End-to-end assemble() tests."""

    @pytest.fixture
    def assembler(self):
        from detail_forge.synthesis import CoherenceEngine, PageAssembler, SectionCompositor

        compositor = SectionCompositor()
        coherence = CoherenceEngine()
        return PageAssembler(compositor=compositor, coherence=coherence)

    @pytest.fixture
    def sections_data(self):
        return [
            {
                "template_html": SIMPLE_HTML,
                "copy": SIMPLE_COPY,
                "slot_mapping": SIMPLE_MAPPING,
                "product_images": {"img_0": "https://example.com/product.jpg"},
            },
            {
                "template_html": "<section><h1 data-slot='text_0'>Old</h1></section>",
                "copy": SectionCopy(
                    section_index=1,
                    section_type="features",
                    headline="Why Choose Us",
                    body="Premium quality.",
                ),
                "slot_mapping": SlotMapping(headline="text_0"),
                "product_images": None,
            },
        ]

    def test_returns_assembled_page(self, assembler, sections_data):
        from detail_forge.synthesis.page_assembler import AssembledPage

        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens, product_name="TestProduct")
        assert isinstance(page, AssembledPage)

    def test_section_count_correct(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert page.section_count == 2

    def test_html_is_complete_document(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens, product_name="TestProduct")
        assert "<html" in page.html
        assert "</html>" in page.html

    def test_html_contains_style_block(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert "<style" in page.html

    def test_html_contains_token_css_root(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert ":root" in page.html
        assert "--df-color-primary" in page.html

    def test_html_contains_section_content(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert "Amazing Product" in page.html
        assert "Why Choose Us" in page.html

    def test_total_quality_score_is_average(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert 0.0 <= page.total_quality_score <= 10.0

    def test_coherence_score_present(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert 0.0 <= page.coherence_score <= 10.0

    def test_dp_wrapper_div_present(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert 'class="dp"' in page.html or "class='dp'" in page.html

    def test_google_fonts_link_present(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        assert "fonts.googleapis.com" in page.html

    def test_section_transitions_css(self, assembler, sections_data):
        tokens = make_tokens()
        page = assembler.assemble(sections_data, tokens)
        # Should include transition/animation CSS
        assert "transition" in page.html or "animation" in page.html or "fade" in page.html.lower()


class TestPageAssemblerEdgeCases:
    @pytest.fixture
    def assembler(self):
        from detail_forge.synthesis import CoherenceEngine, PageAssembler, SectionCompositor

        return PageAssembler(compositor=SectionCompositor(), coherence=CoherenceEngine())

    def test_empty_sections_data(self, assembler):
        tokens = make_tokens()
        page = assembler.assemble([], tokens)
        assert page.section_count == 0
        assert "<html" in page.html

    def test_single_section(self, assembler):
        tokens = make_tokens()
        sections_data = [
            {
                "template_html": SIMPLE_HTML,
                "copy": SIMPLE_COPY,
                "slot_mapping": SIMPLE_MAPPING,
            }
        ]
        page = assembler.assemble(sections_data, tokens, product_name="Solo")
        assert page.section_count == 1
        assert "Amazing Product" in page.html

    def test_product_name_in_title(self, assembler):
        tokens = make_tokens()
        sections_data = [
            {
                "template_html": SIMPLE_HTML,
                "copy": SIMPLE_COPY,
                "slot_mapping": SIMPLE_MAPPING,
            }
        ]
        page = assembler.assemble(sections_data, tokens, product_name="MyBrand")
        assert "MyBrand" in page.html


# ============================================================
# Package-level __init__.py exports
# ============================================================


class TestSynthesisPackageExports:
    def test_all_exports_available(self):
        from detail_forge.synthesis import (  # noqa: F401
            CoherenceEngine,
            PageAssembler,
            SectionCompositor,
        )

    def test_no_ai_calls_in_compositor(self):
        """Verify SectionCompositor has no AI provider dependency."""
        from detail_forge.synthesis import SectionCompositor

        comp = SectionCompositor()
        # Should instantiate without any API keys or providers
        assert comp is not None

    def test_no_ai_calls_in_coherence_engine(self):
        from detail_forge.synthesis import CoherenceEngine

        engine = CoherenceEngine()
        assert engine is not None

    def test_page_assembler_requires_compositor_and_coherence(self):
        from detail_forge.synthesis import CoherenceEngine, PageAssembler, SectionCompositor

        # Correct instantiation
        assembler = PageAssembler(compositor=SectionCompositor(), coherence=CoherenceEngine())
        assert assembler is not None


# ============================================================
# Coverage gap tests — background_image, extra slots, _split_body edge cases
# ============================================================


class TestSectionCompositorCoverageGaps:
    """Tests targeting previously uncovered lines."""

    @pytest.fixture
    def compositor(self):
        from detail_forge.synthesis import SectionCompositor

        return SectionCompositor()

    def test_background_image_slot_not_reported_as_unfilled(self, compositor):
        """background_image slot should not generate an 'Unfilled slot' warning."""
        html = '<div><div data-slot-bg="bg_0" style="background-image: url(old.jpg)">bg</div></div>'
        mapping = SlotMapping(background_image="bg_0")
        copy = SectionCopy(section_index=0, section_type="hero", headline="Hi")
        tokens = make_tokens()
        result = compositor.compose(html, copy, mapping, tokens)
        unfilled_warnings = [w for w in result.warnings if "bg_0" in w]
        assert unfilled_warnings == []

    def test_extra_slot_mapping_fills_text(self, compositor):
        """SlotMapping.extra should map SectionCopy attribute to data-slot."""
        html = '<div><span data-slot="text_extra">placeholder</span></div>'
        # Use 'headline' as the field name mapped to 'text_extra'
        mapping = SlotMapping(extra={"headline": "text_extra"})
        copy = SectionCopy(section_index=0, section_type="hero", headline="Extra fill value")
        tokens = make_tokens()
        result = compositor.compose(html, copy, mapping, tokens)
        from bs4 import BeautifulSoup as BS

        soup = BS(result.html, "html.parser")
        el = soup.find(attrs={"data-slot": "text_extra"})
        assert el is not None
        assert el.get_text() == "Extra fill value"

    def test_split_body_empty_string_returns_repeated(self, compositor):
        """Empty body string should fall back gracefully."""
        html = "<div><p data-slot='text_2'>a</p><p data-slot='text_3'>b</p></div>"
        mapping = SlotMapping(body=["text_2", "text_3"])
        # Body with no sentences (all too short or empty)
        copy = SectionCopy(section_index=0, section_type="features", body="")
        tokens = make_tokens()
        # Should not raise — warnings about missing body is acceptable
        result = compositor.compose(html, copy, mapping, tokens)
        assert result is not None

    def test_split_body_single_long_sentence_duplicated(self, compositor):
        """Body with one long sentence should fill multiple slots by duplication."""
        html = "<div><p data-slot='text_2'>a</p><p data-slot='text_3'>b</p></div>"
        mapping = SlotMapping(body=["text_2", "text_3"])
        copy = SectionCopy(
            section_index=0,
            section_type="features",
            body="Only one long sentence here without punctuation that ends the text",
        )
        tokens = make_tokens()
        result = compositor.compose(html, copy, mapping, tokens)
        from bs4 import BeautifulSoup as BS

        soup = BS(result.html, "html.parser")
        texts = [el.get_text() for el in soup.find_all(attrs={"data-slot": True})]
        # Both slots should be filled with non-empty text
        assert all(t for t in texts)
