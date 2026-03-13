"""Tests for DesignToken system - TDD RED phase.

Tests are written BEFORE implementation to define expected behavior.
"""

from __future__ import annotations

import pytest

# ─── T-1.1.1: DesignToken data models ────────────────────────────


class TestDesignTokenModels:
    """Tests for DesignToken data model structure."""

    def test_design_token_has_name_and_value(self):
        """A DesignToken must have a css_name and css_value."""
        from detail_forge.designer.design_tokens import DesignToken

        token = DesignToken(css_name="--df-color-primary", css_value="#e74c3c")
        assert token.css_name == "--df-color-primary"
        assert token.css_value == "#e74c3c"

    def test_design_token_has_category(self):
        """A DesignToken must have a category (color, typography, spacing, effect)."""
        from detail_forge.designer.design_tokens import DesignToken

        token = DesignToken(
            css_name="--df-font-heading",
            css_value="'Playfair Display', serif",
            category="typography",
        )
        assert token.category == "typography"

    def test_design_token_set_contains_tokens(self):
        """A DesignTokenSet must contain a collection of DesignToken instances."""
        from detail_forge.designer.design_tokens import DesignToken, DesignTokenSet

        tokens = [
            DesignToken(css_name="--df-color-primary", css_value="#e74c3c", category="color"),
            DesignToken(css_name="--df-font-heading", css_value="serif", category="typography"),
        ]
        token_set = DesignTokenSet(tokens=tokens)
        assert len(token_set.tokens) == 2

    def test_design_token_set_to_css_generates_root(self):
        """DesignTokenSet.to_css() must generate a :root block with CSS Custom Properties."""
        from detail_forge.designer.design_tokens import DesignToken, DesignTokenSet

        tokens = [
            DesignToken(css_name="--df-color-primary", css_value="#e74c3c", category="color"),
        ]
        token_set = DesignTokenSet(tokens=tokens)
        css_output = token_set.to_css()

        assert ":root" in css_output
        assert "--df-color-primary" in css_output
        assert "#e74c3c" in css_output

    def test_design_token_set_to_css_format(self):
        """to_css() must produce valid CSS property declarations."""
        from detail_forge.designer.design_tokens import DesignToken, DesignTokenSet

        tokens = [
            DesignToken(css_name="--df-color-primary", css_value="#e74c3c", category="color"),
            DesignToken(css_name="--df-font-heading", css_value="serif", category="typography"),
        ]
        token_set = DesignTokenSet(tokens=tokens)
        css_output = token_set.to_css()

        assert "--df-color-primary: #e74c3c;" in css_output
        assert "--df-font-heading: serif;" in css_output


# ─── T-1.1.2: D1000 principles -> CSS Custom Properties mapping ────


class TestPrincipleToCSSMapping:
    """Tests for D1000 principle ID -> CSS token mapping."""

    def test_from_principles_returns_token_set(self):
        """DesignTokenSet.from_principles() must return a DesignTokenSet."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15, 21, 3])
        assert isinstance(result, DesignTokenSet)

    def test_from_principles_generates_color_primary(self):
        """Principle 15 (6:3:1 color formula) must generate --df-color-primary."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15])
        css = result.to_css()
        assert "--df-color-primary" in css

    def test_from_principles_generates_font_heading(self):
        """Principles must generate --df-font-heading token."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([21])
        css = result.to_css()
        assert "--df-font-heading" in css

    def test_from_principles_generates_spacing_section(self):
        """Principles must generate --df-spacing-section token."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([3])
        css = result.to_css()
        assert "--df-spacing-section" in css

    def test_from_principles_all_required_tokens_present(self):
        """AC-DT-001: Given IDs [15, 21, 3], must generate all required token categories."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15, 21, 3])
        css = result.to_css()

        assert "--df-color-primary" in css
        assert "--df-font-heading" in css
        assert "--df-spacing-section" in css

    def test_from_principles_dark_metal_effect(self):
        """Principle 28 (metal texture) must generate dark metallic color tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([28])
        css = result.to_css()

        assert "--df-color-primary" in css
        color_token = next((t for t in result.tokens if t.css_name == "--df-color-primary"), None)
        assert color_token is not None
        assert color_token.css_value != "#e74c3c"

    def test_from_principles_gradient_effect_token(self):
        """Principle 36 (blur background) must generate --df-gradient-mesh token."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([36])
        css = result.to_css()
        assert "--df-gradient-mesh" in css

    def test_from_principles_shadow_token(self):
        """Principles related to depth must generate --df-shadow-* tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([39])
        css = result.to_css()
        assert "--df-shadow-" in css

    def test_token_has_css_name_prefix(self):
        """All generated CSS custom property names must start with --df-."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15, 21, 3, 28, 36])
        for token in result.tokens:
            assert token.css_name.startswith("--df-"), (
                f"Token '{token.css_name}' does not start with '--df-'"
            )


# ─── T-1.1.3: Category profile -> token preset ─────────────────────


class TestCategoryTokenPresets:
    """Tests for category-based token preset generation."""

    def test_beauty_category_uses_correct_principles(self):
        """AC-DT-002: Given 'beauty', preset must use key_principles [36, 6, 21, 48, 49]."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_category("beauty")
        assert isinstance(result, DesignTokenSet)
        css = result.to_css()
        assert "--df-gradient-mesh" in css

    def test_electronics_category_produces_dark_tokens(self):
        """Electronics category (principles 28, 3, 50) must produce metallic/dark tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_category("electronics")
        css = result.to_css()
        assert "--df-color-primary" in css
        color_token = next((t for t in result.tokens if t.css_name == "--df-color-primary"), None)
        assert color_token is not None

    def test_food_category_produces_warm_tokens(self):
        """Food category must produce warm natural color tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_category("food")
        css = result.to_css()
        assert "--df-color-primary" in css

    def test_all_6_categories_supported(self):
        """All 6 categories must produce valid token sets without error."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        categories = ["food", "electronics", "fashion", "beauty", "health", "lifestyle"]
        for cat in categories:
            result = DesignTokenSet.from_category(cat)
            assert isinstance(result, DesignTokenSet), (
                f"Category '{cat}' did not return DesignTokenSet"
            )
            assert len(result.tokens) > 0, f"Category '{cat}' produced empty token set"

    def test_invalid_category_raises_error(self):
        """An unknown category must raise ValueError."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        with pytest.raises(ValueError, match="Unknown category"):
            DesignTokenSet.from_category("unknown_category")


# ─── T-1.1.4: Style keyword -> token preset ────────────────────────


class TestStyleKeywordPresets:
    """Tests for style keyword -> token preset mapping."""

    def test_premium_keyword_extracts_correct_principle_ids(self):
        """AC-DT-002: '프리미엄' must extract principle IDs [28, 20, 3, 15, 50]."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_keyword("프리미엄")
        assert isinstance(result, DesignTokenSet)
        css = result.to_css()
        assert "--df-color-primary" in css

    def test_trendy_keyword_produces_gradient_tokens(self):
        """'트렌디' keyword (principle 36) must produce gradient/mesh tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_keyword("트렌디")
        css = result.to_css()
        assert "--df-gradient-mesh" in css

    def test_minimal_keyword_produces_whitespace_tokens(self):
        """'미니멀' keyword (principle 3) must produce large spacing tokens."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_keyword("미니멀")
        css = result.to_css()
        assert "--df-spacing-section" in css
        spacing_token = next(
            (t for t in result.tokens if t.css_name == "--df-spacing-section"), None
        )
        assert spacing_token is not None

    def test_unknown_keyword_uses_default_tokens(self):
        """An unknown keyword must produce default token set without raising."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_keyword("존재하지않는키워드")
        assert isinstance(result, DesignTokenSet)
        assert len(result.tokens) > 0


# ─── T-1.1.5: html_renderer uses token references ─────────────────


class TestHtmlRendererTokenIntegration:
    """Tests verifying html_renderer.py uses CSS custom properties."""

    def _make_section_copy(self, section_type="hero"):
        """Create a minimal SectionCopy for testing."""
        from detail_forge.copywriter.generator import SectionCopy

        return SectionCopy(
            section_index=0,
            section_type=section_type,
            headline="Test Headline",
            subheadline="Test Sub",
            body="Test body text. Another sentence. More content here.",
            cta_text="Buy Now",
        )

    def test_render_all_includes_root_block_with_tokens(self):
        """render_all() must include :root block with CSS custom properties."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[15, 21, 3])
        copy = self._make_section_copy("hero")
        page = renderer.render_all([copy], product_name="Test Product")
        full_html = page.to_full_html("Test Product")

        assert ":root" in full_html
        assert "--df-color-primary" in full_html

    def test_render_all_hero_uses_var_references(self):
        """Hero section CSS must use var(--df-color-*) references."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[15, 21, 3])
        copy = self._make_section_copy("hero")
        page = renderer.render_all([copy], product_name="Test Product")

        all_css = page.global_css + "\n".join(s.css for s in page.sections)
        assert "var(--df-" in all_css

    def test_render_all_global_css_has_root_with_tokens(self):
        """global_css must contain the :root block from DesignTokenSet."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[15, 21, 3])
        copy = self._make_section_copy("hero")
        page = renderer.render_all([copy], product_name="Test Product")

        assert ":root" in page.global_css


# ─── T-1.1.6: 5 theme modes render identically ────────────────────


class TestThemePreservation:
    """Tests verifying all 5 theme modes produce valid HTML with the token system."""

    def _make_copies(self):
        """Create a set of section copies for testing."""
        from detail_forge.copywriter.generator import SectionCopy

        sections = []
        for i, st in enumerate(["hero", "features"]):
            sections.append(
                SectionCopy(
                    section_index=i,
                    section_type=st,
                    headline="Test Headline",
                    subheadline="Test Sub",
                    body="Test body sentence one. Test body sentence two. Test sentence three.",
                    cta_text="Buy Now",
                )
            )
        return sections

    def test_standard_theme_renders_without_error(self):
        """Standard theme must render valid HTML without error."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[15, 21])
        page = renderer.render_all(self._make_copies(), product_name="Product")
        assert page.to_full_html("Product")

    def test_dark_theme_renders_without_error(self):
        """Dark theme (principle 28) must render valid HTML."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[28])
        page = renderer.render_all(self._make_copies(), product_name="Product")
        html = page.to_full_html("Product")
        assert html
        assert "<!DOCTYPE html>" in html

    def test_minimal_theme_renders_without_error(self):
        """Minimal theme (principle 3) must render valid HTML."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[3])
        page = renderer.render_all(self._make_copies(), product_name="Product")
        html = page.to_full_html("Product")
        assert html
        assert "<!DOCTYPE html>" in html

    def test_trendy_theme_renders_without_error(self):
        """Trendy theme (principle 36) must render valid HTML."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[36])
        page = renderer.render_all(self._make_copies(), product_name="Product")
        html = page.to_full_html("Product")
        assert html
        assert "<!DOCTYPE html>" in html

    def test_vintage_theme_renders_without_error(self):
        """Vintage theme (principle 47) must render valid HTML."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        renderer = HtmlRenderer(selected_principles=[47])
        page = renderer.render_all(self._make_copies(), product_name="Product")
        html = page.to_full_html("Product")
        assert html
        assert "<!DOCTYPE html>" in html

    def test_all_themes_have_root_token_block(self):
        """All 5 themes must include :root block with CSS custom properties."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        theme_principles = {
            "standard": [15, 21],
            "dark": [28],
            "minimal": [3],
            "trendy": [36],
            "vintage": [47],
        }
        for theme_name, principles in theme_principles.items():
            renderer = HtmlRenderer(selected_principles=principles)
            page = renderer.render_all(self._make_copies(), product_name="Product")
            html = page.to_full_html("Product")
            assert ":root" in html, f"Theme '{theme_name}' missing :root block"
            assert "--df-color-primary" in html, (
                f"Theme '{theme_name}' missing --df-color-primary token"
            )

    def test_all_themes_have_section_html(self):
        """All 5 themes must produce non-empty section HTML."""
        from detail_forge.designer.html_renderer import HtmlRenderer

        theme_principles = {
            "standard": [15, 21],
            "dark": [28],
            "minimal": [3],
            "trendy": [36],
            "vintage": [47],
        }
        for theme_name, principles in theme_principles.items():
            renderer = HtmlRenderer(selected_principles=principles)
            page = renderer.render_all(self._make_copies(), product_name="Product")
            assert len(page.sections) == 2, f"Theme '{theme_name}' section count wrong"
            for section in page.sections:
                assert section.html, f"Theme '{theme_name}' has empty section HTML"


# ─── T-1.1.7: Comprehensive unit tests ────────────────────────────


class TestDesignTokenSetComprehensive:
    """Comprehensive unit tests for DesignTokenSet."""

    def test_token_set_is_empty_by_default(self):
        """An empty DesignTokenSet should produce :root {} with no properties."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        empty = DesignTokenSet(tokens=[])
        css = empty.to_css()
        assert ":root" in css

    def test_from_principles_empty_list_produces_defaults(self):
        """from_principles([]) must produce default tokens (not empty)."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([])
        assert isinstance(result, DesignTokenSet)
        assert len(result.tokens) > 0

    def test_font_body_token_always_present(self):
        """--df-font-body must always be included regardless of principles."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([1, 2, 3])
        css = result.to_css()
        assert "--df-font-body" in css

    def test_color_accent_token_present(self):
        """--df-color-accent must be present in all token sets."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15])
        css = result.to_css()
        assert "--df-color-accent" in css

    def test_color_bg_token_present(self):
        """--df-color-bg must be present in all token sets."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([3])
        css = result.to_css()
        assert "--df-color-bg" in css

    def test_spacing_element_token_present(self):
        """--df-spacing-element must be present in all token sets."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([1])
        css = result.to_css()
        assert "--df-spacing-element" in css

    def test_tokens_are_unique_by_css_name(self):
        """No two tokens in a DesignTokenSet should have the same css_name."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15, 21, 3, 28, 36, 47])
        names = [t.css_name for t in result.tokens]
        assert len(names) == len(set(names)), "Duplicate token names found"

    def test_style_preset_고급_미니멀_works(self):
        """STYLE_PRESETS '고급 미니멀' must produce valid token set."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_preset("고급 미니멀")
        assert isinstance(result, DesignTokenSet)
        css = result.to_css()
        assert "--df-color-primary" in css

    def test_style_preset_트렌디_힙_works(self):
        """STYLE_PRESETS '트렌디 힙' must produce gradient token."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_style_preset("트렌디 힙")
        css = result.to_css()
        assert "--df-gradient-mesh" in css

    def test_invalid_style_preset_raises_error(self):
        """Unknown style preset must raise ValueError."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        with pytest.raises(ValueError, match="Unknown style preset"):
            DesignTokenSet.from_style_preset("존재하지않는프리셋")

    def test_get_token_by_name(self):
        """DesignTokenSet.get_token() must return the correct token by css_name."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15])
        token = result.get_token("--df-color-primary")
        assert token is not None
        assert token.css_name == "--df-color-primary"

    def test_get_token_by_name_missing_returns_none(self):
        """DesignTokenSet.get_token() must return None for unknown names."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15])
        token = result.get_token("--df-nonexistent")
        assert token is None

    def test_tokens_by_category_returns_filtered_list(self):
        """DesignTokenSet.tokens_by_category() must return only tokens of given category."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15, 21, 3])
        color_tokens = result.tokens_by_category("color")
        for t in color_tokens:
            assert t.category == "color"

    def test_merge_two_token_sets(self):
        """Two DesignTokenSets merged must contain tokens from both."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        set1 = DesignTokenSet.from_principles([15])
        set2 = DesignTokenSet.from_principles([28])
        merged = set1.merge(set2)

        assert isinstance(merged, DesignTokenSet)
        assert len(merged.tokens) > 0

    def test_blur_token_present_for_principle_39(self):
        """Principle 39 (unexpected blur) must generate --df-blur-* token."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([39])
        css = result.to_css()
        assert "--df-blur-" in css

    def test_font_size_tokens_present(self):
        """--df-font-size-* tokens must be present in all token sets."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = DesignTokenSet.from_principles([15])
        css = result.to_css()
        assert "--df-font-size-" in css
