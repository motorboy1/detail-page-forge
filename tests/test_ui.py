"""Tests for ui/app.py — import checks, session state, and engine integration."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on path (mirrors what ui/app.py does)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# 1. Import checks
# ---------------------------------------------------------------------------

class TestImports:
    """Verify all synthesis engine modules used by the UI can be imported."""

    def test_template_store_import(self):
        from detail_forge.templates.store import TemplateStore
        assert TemplateStore is not None

    def test_template_searcher_import(self):
        from detail_forge.templates.search import TemplateSearcher
        assert TemplateSearcher is not None

    def test_one_click_generator_import(self):
        from detail_forge.synthesis.one_click_generator import GenerationResult, OneClickGenerator
        assert OneClickGenerator is not None
        assert GenerationResult is not None

    def test_product_info_import(self):
        from detail_forge.copywriter.generator import ProductInfo, SectionCopy
        assert ProductInfo is not None
        assert SectionCopy is not None

    def test_theme_generator_import(self):
        from detail_forge.designer.theme_generator import Theme, ThemeGenerator
        assert ThemeGenerator is not None
        assert Theme is not None

    def test_design_tokens_import(self):
        from detail_forge.designer.design_tokens import DesignTokenSet
        assert DesignTokenSet is not None

    def test_d1000_constants_import(self):
        from detail_forge.designer.d1000_principles import (
            CATEGORY_PROFILES,
            D1000_GUIDE,
            STYLE_KEYWORDS,
            STYLE_PRESETS,
        )
        assert STYLE_PRESETS is not None
        assert CATEGORY_PROFILES is not None
        assert STYLE_KEYWORDS is not None
        assert D1000_GUIDE is not None

    def test_web_renderer_import(self):
        from detail_forge.output.web_renderer import WebRenderer
        assert WebRenderer is not None

    def test_naver_renderer_import(self):
        from detail_forge.output.naver_renderer import NaverRenderer
        assert NaverRenderer is not None

    def test_quality_gate_import(self):
        from detail_forge.output.quality_gate import QualityGate
        assert QualityGate is not None

    def test_export_manager_import(self):
        from detail_forge.output.export_manager import ExportManager
        assert ExportManager is not None


# ---------------------------------------------------------------------------
# 2. ThemeGenerator recipe names
# ---------------------------------------------------------------------------

class TestThemeGeneratorRecipes:
    """Verify ThemeGenerator.list_recipes() returns expected data for the UI."""

    def test_list_recipes_returns_list(self):
        from detail_forge.designer.theme_generator import ThemeGenerator
        gen = ThemeGenerator()
        recipes = gen.list_recipes()
        assert isinstance(recipes, list)
        assert len(recipes) > 0

    def test_all_expected_recipes_present(self):
        from detail_forge.designer.theme_generator import ThemeGenerator
        gen = ThemeGenerator()
        names = {r["name"] for r in gen.list_recipes()}
        expected = {
            "premium_minimal", "warm_nature", "trendy_hip",
            "dark_luxury", "classic_trust", "organic_flow",
        }
        assert expected.issubset(names), f"Missing recipes: {expected - names}"

    def test_recipe_has_required_keys(self):
        from detail_forge.designer.theme_generator import ThemeGenerator
        gen = ThemeGenerator()
        for recipe in gen.list_recipes():
            assert "name" in recipe
            assert "mood" in recipe
            assert "description" in recipe
            assert "affinity" in recipe

    def test_generate_recipe_returns_theme(self):
        from detail_forge.designer.theme_generator import Theme, ThemeGenerator
        gen = ThemeGenerator()
        theme = gen.generate("classic_trust")
        assert isinstance(theme, Theme)
        assert theme.name == "classic_trust"
        assert theme.tokens is not None

    def test_generate_custom_theme(self):
        from detail_forge.designer.theme_generator import Theme, ThemeGenerator
        gen = ThemeGenerator()
        theme = gen.generate_custom(principle_ids=[3, 15, 21])
        assert isinstance(theme, Theme)
        assert theme.principle_ids == [3, 15, 21]


# ---------------------------------------------------------------------------
# 3. STYLE_PRESETS keys
# ---------------------------------------------------------------------------

class TestStylePresets:
    """Verify STYLE_PRESETS is a dict with string keys and list-of-int values."""

    def test_style_presets_is_dict(self):
        from detail_forge.designer.d1000_principles import STYLE_PRESETS
        assert isinstance(STYLE_PRESETS, dict)

    def test_style_presets_non_empty(self):
        from detail_forge.designer.d1000_principles import STYLE_PRESETS
        assert len(STYLE_PRESETS) >= 4

    def test_style_presets_values_are_int_lists(self):
        from detail_forge.designer.d1000_principles import STYLE_PRESETS
        for key, val in STYLE_PRESETS.items():
            assert isinstance(key, str), f"Key '{key}' should be a string"
            assert isinstance(val, list), f"Value for '{key}' should be a list"
            assert all(isinstance(i, int) for i in val), (
                f"All values in preset '{key}' should be ints"
            )

    def test_expected_preset_names_present(self):
        from detail_forge.designer.d1000_principles import STYLE_PRESETS
        expected = {"고급 미니멀", "따뜻한 자연", "트렌디 힙", "전문 신뢰"}
        present = set(STYLE_PRESETS.keys())
        assert expected.issubset(present), f"Missing presets: {expected - present}"


# ---------------------------------------------------------------------------
# 4. D1000_GUIDE structure
# ---------------------------------------------------------------------------

class TestD1000Guide:
    """Verify D1000_GUIDE entries have the structure the UI expects."""

    def test_d1000_guide_has_50_entries(self):
        from detail_forge.designer.d1000_principles import D1000_GUIDE
        assert len(D1000_GUIDE) == 50

    def test_d1000_guide_entries_have_required_keys(self):
        from detail_forge.designer.d1000_principles import D1000_GUIDE
        for entry in D1000_GUIDE:
            assert "id" in entry, f"Entry missing 'id': {entry}"
            assert "name" in entry, f"Entry missing 'name': {entry}"

    def test_d1000_guide_ids_unique(self):
        from detail_forge.designer.d1000_principles import D1000_GUIDE
        ids = [e["id"] for e in D1000_GUIDE]
        assert len(ids) == len(set(ids)), "D1000_GUIDE has duplicate IDs"

    def test_d1000_guide_ids_in_range(self):
        from detail_forge.designer.d1000_principles import D1000_GUIDE
        for entry in D1000_GUIDE:
            assert 1 <= entry["id"] <= 50, f"ID {entry['id']} out of range 1-50"


# ---------------------------------------------------------------------------
# 5. TemplateStore initialisation
# ---------------------------------------------------------------------------

class TestTemplateStore:
    """Verify TemplateStore can be initialised and the base_dir is created."""

    def test_template_store_init_default(self):
        from detail_forge.templates.store import TemplateStore
        store = TemplateStore()
        assert store.base_dir.exists()

    def test_template_store_list_templates(self):
        from detail_forge.templates.store import TemplateStore
        store = TemplateStore()
        templates = store.list_templates()
        assert isinstance(templates, list)

    def test_template_searcher_search_returns_list(self):
        from detail_forge.templates.search import TemplateSearcher
        from detail_forge.templates.store import TemplateStore
        store = TemplateStore()
        searcher = TemplateSearcher(store)
        results = searcher.search(limit=10)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# 6. QualityGate basic evaluation
# ---------------------------------------------------------------------------

class TestQualityGate:
    """Smoke test for QualityGate.evaluate()."""

    _SIMPLE_HTML = """
    <!DOCTYPE html>
    <html lang="ko">
    <head><title>Test</title></head>
    <body>
      <section>
        <h1>헤드라인</h1>
        <p>본문 텍스트입니다. 충분한 내용이 포함되어 있습니다.</p>
      </section>
    </body>
    </html>
    """

    def test_quality_gate_returns_output_quality(self):
        from detail_forge.output.quality_gate import OutputQuality, QualityGate
        gate = QualityGate()
        result = gate.evaluate(self._SIMPLE_HTML, platform="web")
        assert isinstance(result, OutputQuality)

    def test_quality_gate_has_dimensions(self):
        from detail_forge.output.quality_gate import QualityGate
        gate = QualityGate()
        result = gate.evaluate(self._SIMPLE_HTML, platform="web")
        assert len(result.dimensions) == 5

    def test_quality_gate_total_score_range(self):
        from detail_forge.output.quality_gate import QualityGate
        gate = QualityGate()
        result = gate.evaluate(self._SIMPLE_HTML, platform="web")
        assert 0.0 <= result.total_score <= 10.0


# ---------------------------------------------------------------------------
# 7. ExportManager basic ZIP creation
# ---------------------------------------------------------------------------

class TestExportManager:
    """Verify ExportManager.export() produces a valid ZIP."""

    def test_export_returns_package(self):
        from detail_forge.output.export_manager import ExportManager, ExportPackage
        manager = ExportManager()
        pkg = manager.export(
            product_name="테스트 상품",
            web_html="<html><body>test</body></html>",
        )
        assert isinstance(pkg, ExportPackage)
        assert len(pkg.zip_bytes) > 0

    def test_export_zip_is_valid(self):
        import io
        import zipfile

        from detail_forge.output.export_manager import ExportManager
        manager = ExportManager()
        pkg = manager.export(
            product_name="테스트 상품",
            web_html="<html><body>test</body></html>",
            naver_html="<html><body>naver</body></html>",
        )
        with zipfile.ZipFile(io.BytesIO(pkg.zip_bytes)) as zf:
            names = zf.namelist()
        assert any("web" in n for n in names)
        assert any("naver" in n for n in names)
        assert any("metadata" in n for n in names)
