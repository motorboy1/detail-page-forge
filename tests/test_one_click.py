"""Tests for ThemeGenerator and OneClickGenerator — M-2.3.

TDD Specification: RED-GREEN-REFACTOR cycle.
Tests are written BEFORE implementation (RED phase).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from detail_forge.copywriter.generator import ProductInfo, SectionCopy
from detail_forge.templates.models import SlotMapping, TemplateMetadata
from detail_forge.templates.store import TemplateStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_store(tmp_path: Path) -> TemplateStore:
    """Create a real TemplateStore with two test templates."""
    store = TemplateStore(base_dir=tmp_path / "templates")

    # Template 1 — hero section
    meta1 = TemplateMetadata(
        id="hero-01",
        name="Hero Section",
        section_type="hero",
        d1000_principles=[3, 21],
        category="beauty",
    )
    html1 = (
        "<section>"
        '<h1 data-slot="text_0">Headline</h1>'
        '<p data-slot="text_1">Sub</p>'
        '<p data-slot="text_2">Body text</p>'
        '<img data-slot="img_0" src="placeholder.jpg" alt="product">'
        "</section>"
    )
    slots1 = {"text_0": "Headline", "text_1": "Sub", "text_2": "Body text", "img_0": ""}
    mapping1 = SlotMapping(
        headline="text_0", subheadline="text_1", body=["text_2"], product_image="img_0"
    )
    store.add_template(meta1, html1, slots1, mapping1)

    # Template 2 — features section
    meta2 = TemplateMetadata(
        id="features-01",
        name="Features Section",
        section_type="features",
        d1000_principles=[15],
        category="food",
    )
    html2 = (
        "<section>"
        '<h2 data-slot="text_0">Features</h2>'
        '<p data-slot="text_1">Feature detail</p>'
        "</section>"
    )
    slots2 = {"text_0": "Features", "text_1": "Feature detail"}
    mapping2 = SlotMapping(headline="text_0", subheadline="text_1", body=[])
    store.add_template(meta2, html2, slots2, mapping2)

    return store


@pytest.fixture
def store(tmp_path: Path) -> TemplateStore:
    return _make_store(tmp_path)


@pytest.fixture
def product() -> ProductInfo:
    return ProductInfo(
        name="Hyaluron Serum",
        features=["Deep hydration", "Niacinamide brightening"],
        target_audience="Women 25-40",
        price_range="30,000-50,000",
        usp="48h moisture lock",
    )


@pytest.fixture
def copy_sections() -> list[SectionCopy]:
    return [
        SectionCopy(
            section_index=0,
            section_type="hero",
            headline="피부 속부터 채워주는 수분",
            subheadline="히알루론 세럼",
            body="48시간 수분 유지",
            cta_text="지금 구매하기",
        ),
        SectionCopy(
            section_index=1,
            section_type="features",
            headline="주요 성분",
            subheadline="나이아신아마이드",
            body="미백 + 수분 동시",
            cta_text="",
        ),
    ]


# ===========================================================================
# ThemeGenerator tests
# ===========================================================================


class TestThemeGeneratorGenerate:
    """Tests for ThemeGenerator.generate() — recipe-based theme creation."""

    def test_generate_premium_minimal(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("premium_minimal")

        assert theme.name == "premium_minimal"
        assert theme.mood == "elegant"
        assert "beauty" in theme.category_affinity
        assert theme.tokens is not None

    def test_generate_warm_nature(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("warm_nature")

        assert theme.name == "warm_nature"
        assert theme.mood == "warm"
        assert "food" in theme.category_affinity

    def test_generate_trendy_hip(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("trendy_hip")

        assert theme.mood == "bold"
        assert "electronics" in theme.category_affinity or "fashion" in theme.category_affinity

    def test_generate_dark_luxury(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("dark_luxury")

        assert theme.mood == "cool"
        assert len(theme.principle_ids) >= 2

    def test_generate_classic_trust(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("classic_trust")

        assert theme.mood == "neutral"
        assert "food" in theme.category_affinity or "health" in theme.category_affinity

    def test_generate_organic_flow(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("organic_flow")

        assert theme.mood == "warm"
        assert len(theme.principle_ids) >= 3

    def test_generate_unknown_recipe_raises_value_error(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        with pytest.raises(ValueError, match="Unknown theme recipe"):
            tg.generate("nonexistent_recipe")

    def test_generate_returns_theme_with_tokens_css(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate("premium_minimal")
        css = theme.tokens.to_css()

        # Tokens CSS should be a non-empty :root block
        assert ":root" in css
        assert "--df-" in css

    def test_generate_all_recipes_return_theme(self):
        """All 6 predefined recipes should generate without error."""
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        recipes = tg.list_recipes()
        assert len(recipes) == 6

        for recipe in recipes:
            theme = tg.generate(recipe["name"])
            assert theme.name == recipe["name"]
            assert theme.tokens is not None


class TestThemeGeneratorCustom:
    """Tests for ThemeGenerator.generate_custom()."""

    def test_generate_custom_with_valid_principles(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate_custom(principle_ids=[3, 28], name="my_theme")

        assert theme.name == "my_theme"
        assert theme.principle_ids == [3, 28]
        assert theme.tokens is not None

    def test_generate_custom_empty_principles_returns_default_tokens(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate_custom(principle_ids=[], name="empty")

        # Should still return a valid token set (default)
        assert theme.tokens is not None
        css = theme.tokens.to_css()
        assert ":root" in css

    def test_generate_custom_default_name(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate_custom(principle_ids=[15])

        assert theme.name == "custom"

    def test_generate_custom_has_description(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        theme = tg.generate_custom(principle_ids=[36, 29], name="hip_custom")

        assert isinstance(theme.description, str)
        # Description can be empty for custom themes, but must be a string


class TestThemeGeneratorListRecipes:
    """Tests for ThemeGenerator.list_recipes()."""

    def test_list_recipes_returns_6_items(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        recipes = tg.list_recipes()

        assert len(recipes) == 6

    def test_list_recipes_have_required_keys(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        recipes = tg.list_recipes()

        for recipe in recipes:
            assert "name" in recipe
            assert "mood" in recipe
            assert "description" in recipe
            assert "affinity" in recipe

    def test_list_recipes_names_match_recipe_keys(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        recipes = tg.list_recipes()
        names = {r["name"] for r in recipes}

        assert "premium_minimal" in names
        assert "warm_nature" in names
        assert "trendy_hip" in names
        assert "dark_luxury" in names
        assert "classic_trust" in names
        assert "organic_flow" in names


class TestThemeGeneratorRecommend:
    """Tests for ThemeGenerator.recommend_for_category()."""

    def test_recommend_for_beauty(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        themes = tg.recommend_for_category("beauty")

        assert len(themes) >= 1
        # All returned themes must include 'beauty' in their affinity
        for theme in themes:
            assert "beauty" in theme.category_affinity

    def test_recommend_for_food(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        themes = tg.recommend_for_category("food")

        assert len(themes) >= 1
        for theme in themes:
            assert "food" in theme.category_affinity

    def test_recommend_for_electronics(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        themes = tg.recommend_for_category("electronics")

        assert len(themes) >= 1
        for theme in themes:
            assert "electronics" in theme.category_affinity

    def test_recommend_for_unknown_category_returns_empty(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        themes = tg.recommend_for_category("unknown_xyz")

        assert themes == []

    def test_recommend_returns_theme_objects(self):
        from detail_forge.designer.theme_generator import Theme, ThemeGenerator

        tg = ThemeGenerator()
        themes = tg.recommend_for_category("lifestyle")

        for theme in themes:
            assert isinstance(theme, Theme)


# ===========================================================================
# OneClickGenerator tests
# ===========================================================================


class TestOneClickGeneratorBasic:
    """Tests for OneClickGenerator.generate() basic pipeline."""

    def test_generate_returns_generation_result(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import GenerationResult, OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01", "features-01"],
        )

        assert isinstance(result, GenerationResult)

    def test_generate_assembled_page_has_html(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01", "features-01"],
        )

        assert result.assembled_page.html
        html_out = result.assembled_page.html
        assert "<!DOCTYPE html>" in html_out or "<html" in html_out

    def test_generate_web_html_is_present(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert result.web_html is not None
        assert result.web_html.html

    def test_generate_quality_gate_runs(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert result.quality is not None
        assert result.quality.total_score >= 0.0

    def test_generate_time_ms_is_positive(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert result.generation_time_ms >= 0

    def test_generate_theme_is_set(self, store, product, copy_sections):
        from detail_forge.designer.theme_generator import Theme
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert isinstance(result.theme, Theme)


class TestOneClickGeneratorThemeSelection:
    """Tests for theme selection logic in OneClickGenerator."""

    def test_default_theme_when_no_theme_provided(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        # Should use 'classic_trust' recipe as default
        assert result.theme.name == "classic_trust"

    def test_explicit_theme_is_used(self, store, product, copy_sections):
        from detail_forge.designer.theme_generator import ThemeGenerator
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        tg = ThemeGenerator()
        theme = tg.generate("premium_minimal")

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
            theme=theme,
        )

        assert result.theme.name == "premium_minimal"

    def test_custom_principle_ids_creates_theme(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
            principle_ids=[3, 28],
        )

        # Theme should be auto-created from principle IDs
        assert result.theme is not None
        assert result.theme.principle_ids == [3, 28]

    def test_theme_takes_priority_over_principle_ids(self, store, product, copy_sections):
        from detail_forge.designer.theme_generator import ThemeGenerator
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        tg = ThemeGenerator()
        explicit_theme = tg.generate("warm_nature")

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
            theme=explicit_theme,
            principle_ids=[3, 28],  # should be ignored when theme is provided
        )

        assert result.theme.name == "warm_nature"


class TestOneClickGeneratorNaver:
    """Tests for Naver rendering toggle in OneClickGenerator."""

    def test_include_naver_true_produces_naver_html(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
            include_naver=True,
        )

        assert result.naver_html is not None
        assert result.naver_html.html

    def test_include_naver_false_skips_naver_rendering(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
            include_naver=False,
        )

        assert result.naver_html is None


class TestOneClickGeneratorEdgeCases:
    """Tests for edge cases in OneClickGenerator.generate()."""

    def test_single_template_id(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert result.assembled_page.section_count >= 0

    def test_mismatched_copy_template_counts_handled_gracefully(self, store, product):
        """More templates than copy sections should not crash."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        # Only 1 copy section but 2 template IDs
        single_copy = [
            SectionCopy(
                section_index=0,
                section_type="hero",
                headline="Title",
                subheadline="Sub",
                body="Body",
                cta_text="Buy",
            )
        ]

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=single_copy,
            template_ids=["hero-01", "features-01"],
        )

        # Should succeed without exception
        assert result is not None

    def test_more_copy_than_templates_handled_gracefully(self, store, product, copy_sections):
        """More copy sections than templates should use only available templates."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,  # 2 copy sections
            template_ids=["hero-01"],  # only 1 template
        )

        assert result is not None

    def test_empty_template_ids_returns_minimal_result(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=[],
        )

        assert result is not None
        assert result.assembled_page.section_count == 0

    def test_dependency_injection_compositor_and_coherence(self, store, product, copy_sections):
        """OneClickGenerator accepts custom compositor and coherence via DI."""
        from detail_forge.synthesis.coherence_engine import CoherenceEngine
        from detail_forge.synthesis.one_click_generator import OneClickGenerator
        from detail_forge.synthesis.section_compositor import SectionCompositor

        compositor = SectionCompositor()
        coherence = CoherenceEngine()

        gen = OneClickGenerator(
            template_store=store,
            compositor=compositor,
            coherence=coherence,
        )
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert result is not None


# ===========================================================================
# Coverage gap: _infer_mood branches + FileNotFoundError path
# ===========================================================================


class TestThemeGeneratorMoodInference:
    """Tests for _infer_mood() internal heuristic via generate_custom()."""

    def test_elegant_mood_from_minimal_principles(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        # Principles 3 and 21 map to 'elegant'
        theme = tg.generate_custom(principle_ids=[3, 21], name="elegant_test")
        assert theme.mood == "elegant"

    def test_bold_mood_from_trendy_principles(self):
        from detail_forge.designer.theme_generator import ThemeGenerator

        tg = ThemeGenerator()
        # Principle 36 alone maps to 'bold'
        theme = tg.generate_custom(principle_ids=[36], name="bold_test")
        assert theme.mood == "bold"


class TestOneClickGeneratorMissingTemplate:
    """Tests for graceful handling of missing template IDs."""

    def test_invalid_template_id_is_skipped(self, store, product, copy_sections):
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        # "nonexistent" does not exist — should be skipped, not raise
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01", "nonexistent"],
        )

        # Only hero-01 contributed to the result
        assert result is not None
        assert result.assembled_page.section_count == 1


# ===========================================================================
# New tests for warnings field in GenerationResult
# ===========================================================================


class TestGenerationResultWarnings:
    """GenerationResult must expose a warnings field."""

    def test_generation_result_has_warnings_field(self, store, product, copy_sections):
        """GenerationResult dataclass must have a warnings list field."""
        from detail_forge.synthesis.one_click_generator import GenerationResult, OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01"],
        )

        assert isinstance(result, GenerationResult)
        assert hasattr(result, "warnings")
        assert isinstance(result.warnings, list)

    def test_no_warnings_when_all_templates_found(self, store, product, copy_sections):
        """When all template IDs exist, warnings list must be empty."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01", "features-01"],
        )

        assert result.warnings == []

    def test_missing_template_produces_warning(self, store, product, copy_sections):
        """A non-existent template ID must produce a warning instead of silently skipping."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["hero-01", "does-not-exist"],
        )

        # One template found, one skipped with a warning
        assert len(result.warnings) == 1
        assert "does-not-exist" in result.warnings[0]

    def test_all_missing_templates_produce_warnings(self, store, product, copy_sections):
        """Each missing template ID must produce its own warning entry."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=["ghost-01", "phantom-02"],
        )

        assert len(result.warnings) == 2
        assert any("ghost-01" in w for w in result.warnings)
        assert any("phantom-02" in w for w in result.warnings)

    def test_empty_template_ids_no_warnings(self, store, product, copy_sections):
        """Empty template list should produce zero warnings."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=[],
        )

        assert result.warnings == []
