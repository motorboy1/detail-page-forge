"""Snapshot/unit tests for html_renderer.py — T-1.2.5."""

from __future__ import annotations

import pytest

from detail_forge.copywriter.generator import SectionCopy
from detail_forge.designer.html_renderer import (
    GLOBAL_CSS,
    SECTION_RENDERERS,
    HtmlRenderer,
    RenderedPage,
    RenderedSection,
    _detect_mode,
)

# ── _detect_mode ─────────────────────────────────────────────────────────────


class TestDetectMode:
    def test_dark_mode_when_28_present(self):
        assert _detect_mode({28}) == "dark"

    def test_dark_mode_when_50_present_without_3(self):
        assert _detect_mode({50}) == "dark"

    def test_not_dark_when_50_and_3_both_present(self):
        # 50 in p and 3 not in p → dark; but if 3 is present, check other modes
        result = _detect_mode({50, 3})
        assert result != "dark"

    def test_minimal_mode_when_3_alone(self):
        assert _detect_mode({3}) == "minimal"

    def test_minimal_mode_excludes_28_and_36(self):
        # 3 present but 28 also present → dark wins
        assert _detect_mode({3, 28}) == "dark"
        # 3 present but 36 also present → trendy wins
        result = _detect_mode({3, 36})
        assert result == "trendy"

    def test_trendy_mode_when_36_present(self):
        assert _detect_mode({36}) == "trendy"

    def test_trendy_mode_with_33_and_22(self):
        assert _detect_mode({33, 22}) == "trendy"

    def test_trendy_mode_with_38_and_29(self):
        assert _detect_mode({38, 29}) == "trendy"

    def test_vintage_mode_when_47_present(self):
        assert _detect_mode({47}) == "vintage"

    def test_standard_mode_as_default(self):
        assert _detect_mode({1, 4, 15}) == "standard"

    def test_standard_mode_for_empty_set(self):
        assert _detect_mode(set()) == "standard"

    @pytest.mark.parametrize(
        "principles,expected",
        [
            ({28}, "dark"),
            ({3}, "minimal"),
            ({36}, "trendy"),
            ({47}, "vintage"),
            ({1, 15}, "standard"),
            ({50}, "dark"),
            ({33, 22}, "trendy"),
        ],
    )
    def test_mode_parametrized(self, principles, expected):
        assert _detect_mode(principles) == expected


# ── SECTION_RENDERERS completeness ──────────────────────────────────────────


class TestSectionRenderers:
    EXPECTED_SECTIONS = {
        "hero",
        "features",
        "benefits",
        "testimonials",
        "specs",
        "cta",
        "guarantee",
        "social_proof",
    }

    def test_all_8_sections_registered(self):
        assert set(SECTION_RENDERERS.keys()) == self.EXPECTED_SECTIONS

    def test_all_renderers_are_callable(self):
        for name, fn in SECTION_RENDERERS.items():
            assert callable(fn), f"Renderer for {name} is not callable"


# ── Section rendering helpers ────────────────────────────────────────────────


def _make_copy(section_type: str) -> SectionCopy:
    return SectionCopy(
        section_index=0,
        section_type=section_type,
        headline="테스트 헤드라인",
        subheadline="테스트 서브헤드",
        body="테스트 본문입니다. 충분히 긴 내용이 있습니다.",
        cta_text="테스트 CTA",
    )


# ── HtmlRenderer.render_section per theme x section ─────────────────────────

THEMES = ["standard", "dark", "minimal", "trendy", "vintage"]
SECTIONS = [
    "hero",
    "features",
    "benefits",
    "testimonials",
    "specs",
    "cta",
    "guarantee",
    "social_proof",
]

THEME_PRINCIPLES = {
    "standard": [1, 4, 15],
    "dark": [28, 20, 15],
    "minimal": [3, 11, 1],
    "trendy": [36, 29, 38],
    "vintage": [47, 33, 29],
}


class TestHtmlRendererPerThemeAndSection:
    @pytest.mark.parametrize("section_type", SECTIONS)
    def test_each_section_renders_html_standard(self, section_type):
        renderer = HtmlRenderer(selected_principles=[1, 4, 15])
        copy = _make_copy(section_type)
        result = renderer.render_section(copy)
        assert isinstance(result, RenderedSection)
        assert isinstance(result.html, str)
        assert len(result.html) > 0

    @pytest.mark.parametrize("section_type", SECTIONS)
    def test_each_section_renders_css_standard(self, section_type):
        renderer = HtmlRenderer(selected_principles=[1, 4, 15])
        copy = _make_copy(section_type)
        result = renderer.render_section(copy)
        assert isinstance(result.css, str)

    @pytest.mark.parametrize("theme,principles", THEME_PRINCIPLES.items())
    def test_hero_renders_for_each_theme(self, theme, principles):
        renderer = HtmlRenderer(selected_principles=principles)
        assert renderer.mode == theme, f"Expected {theme} mode but got {renderer.mode}"
        copy = _make_copy("hero")
        result = renderer.render_section(copy)
        assert isinstance(result.html, str)
        assert len(result.html) > 50

    @pytest.mark.parametrize("theme,principles", THEME_PRINCIPLES.items())
    def test_features_renders_for_each_theme(self, theme, principles):
        renderer = HtmlRenderer(selected_principles=principles)
        copy = _make_copy("features")
        result = renderer.render_section(copy)
        assert len(result.html) > 0

    def test_rendered_section_preserves_metadata(self):
        renderer = HtmlRenderer()
        copy = _make_copy("hero")
        copy.section_index = 5
        result = renderer.render_section(copy)
        assert result.section_index == 5
        assert result.section_type == "hero"
        assert result.copy is copy


# ── RenderedPage structure ───────────────────────────────────────────────────


class TestRenderedPage:
    def test_to_full_html_returns_valid_html(self):
        renderer = HtmlRenderer(selected_principles=[1, 15])
        sections = [_make_copy(s) for s in ["hero", "features", "cta"]]
        page = renderer.render_all(sections, product_name="테스트 제품")
        html = page.to_full_html(product_name="테스트 제품")
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "테스트 제품" in html
        assert "</html>" in html

    def test_render_all_returns_rendered_page(self):
        renderer = HtmlRenderer()
        sections = [_make_copy("hero")]
        result = renderer.render_all(sections)
        assert isinstance(result, RenderedPage)
        assert len(result.sections) == 1

    def test_render_all_global_css_contains_base_css(self):
        renderer = HtmlRenderer()
        sections = [_make_copy("hero")]
        page = renderer.render_all(sections)
        # render_all prepends theme CSS vars, but must include GLOBAL_CSS content
        assert GLOBAL_CSS in page.global_css or ".dp" in page.global_css

    def test_render_all_calls_progress_callback(self):
        renderer = HtmlRenderer()
        sections = [_make_copy("hero"), _make_copy("cta")]
        calls = []
        renderer.render_all(sections, progress_callback=lambda i, n: calls.append((i, n)))
        assert len(calls) == 2

    def test_full_html_contains_section_html(self):
        renderer = HtmlRenderer(selected_principles=[1])
        sections = [_make_copy("hero")]
        page = renderer.render_all(sections)
        html = page.to_full_html()
        # The section html should be in the full html
        assert page.sections[0].html in html


# ── HtmlRenderer initialization ──────────────────────────────────────────────


class TestHtmlRendererInit:
    def test_default_mode_is_standard(self):
        renderer = HtmlRenderer()
        assert renderer.mode == "standard"

    def test_principles_stored_as_set(self):
        renderer = HtmlRenderer(selected_principles=[1, 3, 15])
        assert renderer.principles == {1, 3, 15}

    def test_empty_principles_defaults_standard(self):
        renderer = HtmlRenderer(selected_principles=[])
        assert renderer.mode == "standard"

    def test_product_photos_stored(self):
        photos = ["https://example.com/photo.jpg"]
        renderer = HtmlRenderer(product_photos=photos)
        assert renderer.product_photos == photos

    def test_default_product_photos_is_empty_list(self):
        renderer = HtmlRenderer()
        assert renderer.product_photos == []

    @pytest.mark.parametrize(
        "principles,expected_mode",
        [
            ([28], "dark"),
            ([3], "minimal"),
            ([36], "trendy"),
            ([47], "vintage"),
            ([1, 15], "standard"),
        ],
    )
    def test_mode_detection_on_init(self, principles, expected_mode):
        renderer = HtmlRenderer(selected_principles=principles)
        assert renderer.mode == expected_mode

    def test_meta_contains_mode_and_principles(self):
        renderer = HtmlRenderer(selected_principles=[28, 15])
        assert renderer.meta["mode"] == "dark"
        assert 28 in renderer.meta["principles"]


# ── GLOBAL_CSS sanity ────────────────────────────────────────────────────────


class TestGlobalCss:
    def test_global_css_is_non_empty(self):
        assert len(GLOBAL_CSS) > 0

    def test_global_css_contains_dp_class(self):
        assert ".dp" in GLOBAL_CSS

    def test_global_css_contains_media_query(self):
        assert "@media" in GLOBAL_CSS
