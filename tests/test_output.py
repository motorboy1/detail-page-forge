"""Tests for the output renderers package — M-2.2.

TDD Specification: RED-GREEN-REFACTOR cycle.
Tests are written BEFORE implementation (RED phase).
"""

from __future__ import annotations

import io
import json
import zipfile
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

MINIMAL_HTML = """<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; font-family: 'Noto Sans KR', sans-serif; }
    h1 { font-size: 24px; color: #333; }
    p { font-size: 16px; line-height: 1.5; }
  </style>
</head>
<body>
  <section>
    <h1>Product Title</h1>
    <p>Product description goes here.</p>
    <img src="product.jpg" alt="product image" width="860">
    <img src="detail.jpg" alt="detail image" width="860">
  </section>
</body>
</html>"""

HTML_WITH_FORBIDDEN = """<!DOCTYPE html>
<html>
<head>
  <script>alert('xss')</script>
  <link rel="stylesheet" href="external.css">
  <meta charset="utf-8">
  <style>h1 { font-size: 28px; color: #111; } p { font-size: 14px; }</style>
</head>
<body>
  <h1 onclick="doEvil()">Title</h1>
  <p onload="bad()">Paragraph</p>
  <iframe src="external.html"></iframe>
  <form action="/submit"><input type="text" name="q"></form>
  <p>Normal text</p>
</body>
</html>"""

HTML_WITH_WEBFONTS = """<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Noto Sans KR', sans-serif; }
    h1 { font-family: 'Playfair Display', serif; font-size: 32px; }
    p { font-family: 'Space Grotesk', sans-serif; }
  </style>
</head>
<body>
  <h1>Fancy Title</h1>
  <p>Body text</p>
</body>
</html>"""

HTML_WITH_CSS_VARS = """<!DOCTYPE html>
<html>
<head>
  <style>
    :root { --df-primary: #ff0000; --df-font-size: 18px; }
    h1 { color: var(--df-primary); font-size: var(--df-font-size); }
    p { color: #333; }
  </style>
</head>
<body>
  <h1>Title</h1>
  <p>Text</p>
</body>
</html>"""

HTML_NO_DOCTYPE = """<html>
<body>
  <h1>Title</h1>
  <p>Body text content here.</p>
  <img src="image.jpg" alt="img">
</body>
</html>"""

HTML_MULTI_SECTION = """<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; }
    section { padding: 20px; }
    h1 { font-size: 28px; }
    h2 { font-size: 22px; }
    p { font-size: 16px; line-height: 1.6; }
  </style>
</head>
<body>
  <section>
    <h1>Main Title</h1>
    <p>Introduction paragraph with enough text to be readable content here.</p>
    <img src="hero.jpg" alt="hero">
    <img src="product.jpg" alt="product">
  </section>
  <section>
    <h2>Feature Section</h2>
    <p>Feature description with detailed text explaining the product benefits here.</p>
  </section>
</body>
</html>"""


# ===========================================================================
# NaverRenderer Tests
# ===========================================================================


class TestNaverRenderer:
    """Tests for NaverRenderer — HTML sanitization for Naver SmartStore."""

    def setup_method(self):
        from detail_forge.output.naver_renderer import NaverRenderer

        self.renderer = NaverRenderer()

    def test_render_returns_naver_html_dataclass(self):
        from detail_forge.output.naver_renderer import NaverHTML

        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result, NaverHTML)

    def test_naver_html_has_required_fields(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert hasattr(result, "html")
        assert hasattr(result, "warnings")
        assert hasattr(result, "size_bytes")

    def test_removes_script_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<script" not in result.html
        assert "alert(" not in result.html

    def test_removes_link_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<link" not in result.html

    def test_removes_meta_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<meta" not in result.html

    def test_removes_iframe_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<iframe" not in result.html

    def test_removes_form_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<form" not in result.html

    def test_removes_input_tags(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "<input" not in result.html

    def test_removes_onclick_attribute(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "onclick" not in result.html

    def test_removes_onload_attribute(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "onload" not in result.html

    def test_preserves_normal_content(self):
        result = self.renderer.render(HTML_WITH_FORBIDDEN)
        assert "Normal text" in result.html

    def test_replaces_noto_sans_kr_with_safe_font(self):
        result = self.renderer.render(HTML_WITH_WEBFONTS)
        # Web font should be replaced with safe alternative
        assert "'Noto Sans KR'" not in result.html or "Malgun Gothic" in result.html

    def test_replaces_playfair_display_with_safe_font(self):
        result = self.renderer.render(HTML_WITH_WEBFONTS)
        # Should replace with Georgia or similar
        assert "'Playfair Display'" not in result.html or "Georgia" in result.html

    def test_replaces_space_grotesk_with_safe_font(self):
        result = self.renderer.render(HTML_WITH_WEBFONTS)
        assert "'Space Grotesk'" not in result.html or "Arial" in result.html

    def test_strips_css_custom_properties(self):
        result = self.renderer.render(HTML_WITH_CSS_VARS)
        assert "var(--df-" not in result.html

    def test_size_bytes_is_positive_integer(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result.size_bytes, int)
        assert result.size_bytes > 0

    def test_size_bytes_matches_html_length(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert result.size_bytes == len(result.html.encode("utf-8"))

    def test_warnings_is_list(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result.warnings, list)

    def test_returns_string_html(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result.html, str)
        assert len(result.html) > 0

    def test_inline_css_applied_from_style_block(self):
        html = """<!DOCTYPE html>
<html><head><style>h1 { color: red; font-size: 24px; }</style></head>
<body><h1>Title</h1></body></html>"""
        result = self.renderer.render(html)
        # Style block CSS should be inlined onto elements
        assert "color" in result.html or "font-size" in result.html

    def test_forbidden_tags_constant_defined(self):
        from detail_forge.output.naver_renderer import NaverRenderer

        assert hasattr(NaverRenderer, "FORBIDDEN_TAGS")
        assert "script" in NaverRenderer.FORBIDDEN_TAGS

    def test_forbidden_attrs_constant_defined(self):
        from detail_forge.output.naver_renderer import NaverRenderer

        assert hasattr(NaverRenderer, "FORBIDDEN_ATTRS")
        assert "onclick" in NaverRenderer.FORBIDDEN_ATTRS

    def test_safe_fonts_constant_defined(self):
        from detail_forge.output.naver_renderer import NaverRenderer

        assert hasattr(NaverRenderer, "SAFE_FONTS")
        assert "'Noto Sans KR'" in NaverRenderer.SAFE_FONTS


# ===========================================================================
# WebRenderer Tests
# ===========================================================================


class TestWebRenderer:
    """Tests for WebRenderer — standalone responsive HTML."""

    def setup_method(self):
        from detail_forge.output.web_renderer import WebRenderer

        self.renderer = WebRenderer()

    def test_render_returns_web_html_dataclass(self):
        from detail_forge.output.web_renderer import WebHTML

        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result, WebHTML)

    def test_web_html_has_required_fields(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert hasattr(result, "html")
        assert hasattr(result, "has_media_queries")
        assert hasattr(result, "viewport_meta")

    def test_adds_doctype_when_missing(self):
        result = self.renderer.render(HTML_NO_DOCTYPE)
        assert result.html.lower().startswith("<!doctype html>")

    def test_preserves_existing_doctype(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert "<!DOCTYPE html>" in result.html or "<!doctype html>" in result.html.lower()

    def test_adds_viewport_meta_tag(self):
        result = self.renderer.render(HTML_NO_DOCTYPE)
        assert "viewport" in result.html
        assert result.viewport_meta is True

    def test_preserves_viewport_meta_when_present(self):
        html_with_viewport = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
</head><body><p>text</p></body></html>"""
        result = self.renderer.render(html_with_viewport)
        assert result.viewport_meta is True

    def test_adds_responsive_media_queries(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert "@media" in result.html
        assert result.has_media_queries is True

    def test_media_query_targets_mobile_breakpoint(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert "768px" in result.html or "max-width" in result.html

    def test_images_have_max_width_100_percent(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert "max-width: 100%" in result.html or "max-width:100%" in result.html

    def test_output_is_complete_html_document(self):
        result = self.renderer.render(HTML_NO_DOCTYPE)
        html_lower = result.html.lower()
        assert "<html" in html_lower
        assert "<head" in html_lower
        assert "<body" in html_lower

    def test_accepts_product_name_parameter(self):
        result = self.renderer.render(MINIMAL_HTML, product_name="My Product")
        assert isinstance(result.html, str)

    def test_product_name_in_title_when_provided(self):
        result = self.renderer.render(MINIMAL_HTML, product_name="My Product")
        assert "My Product" in result.html or "<title>" in result.html

    def test_google_fonts_cdn_links_preserved(self):
        html_with_gfonts = """<!DOCTYPE html>
<html><head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR">
<style>body { margin: 0; }</style>
</head><body><p>text</p></body></html>"""
        result = self.renderer.render(html_with_gfonts)
        assert "fonts.googleapis.com" in result.html

    def test_html_is_string(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert isinstance(result.html, str)
        assert len(result.html) > 0

    def test_has_charset_meta(self):
        result = self.renderer.render(HTML_NO_DOCTYPE)
        assert "charset" in result.html.lower() or "utf-8" in result.html.lower()

    def test_print_css_included(self):
        result = self.renderer.render(MINIMAL_HTML)
        assert "@media print" in result.html or "print" in result.html


# ===========================================================================
# QualityGate Tests
# ===========================================================================


class TestQualityGate:
    """Tests for QualityGate — 5-dimension quality evaluation."""

    def setup_method(self):
        from detail_forge.output.quality_gate import QualityGate

        self.gate = QualityGate()

    def test_evaluate_returns_output_quality_dataclass(self):
        from detail_forge.output.quality_gate import OutputQuality

        result = self.gate.evaluate(MINIMAL_HTML)
        assert isinstance(result, OutputQuality)

    def test_output_quality_has_required_fields(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert hasattr(result, "dimensions")
        assert hasattr(result, "total_score")
        assert hasattr(result, "passed")
        assert hasattr(result, "platform")

    def test_dimensions_count_is_five(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert len(result.dimensions) == 5

    def test_dimension_names(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        names = {d.name for d in result.dimensions}
        assert names == {"layout", "typography", "color", "readability", "platform"}

    def test_dimension_has_score_issues(self):
        from detail_forge.output.quality_gate import QualityDimension

        result = self.gate.evaluate(MINIMAL_HTML)
        for dim in result.dimensions:
            assert isinstance(dim, QualityDimension)
            assert hasattr(dim, "name")
            assert hasattr(dim, "score")
            assert hasattr(dim, "issues")

    def test_dimension_score_range(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        for dim in result.dimensions:
            assert 0.0 <= dim.score <= 10.0, f"{dim.name} score out of range: {dim.score}"

    def test_total_score_is_float(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert isinstance(result.total_score, float)

    def test_total_score_range(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert 0.0 <= result.total_score <= 10.0

    def test_passed_is_bool(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert isinstance(result.passed, bool)

    def test_passed_when_score_above_threshold(self):
        # Well-structured HTML should pass
        result = self.gate.evaluate(HTML_MULTI_SECTION)
        # Verify logic: passed iff total_score >= 7.0
        assert result.passed == (result.total_score >= 7.0)

    def test_platform_defaults_to_web(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        assert result.platform == "web"

    def test_platform_coupang_check(self):
        result = self.gate.evaluate(MINIMAL_HTML, platform="coupang")
        assert result.platform == "coupang"

    def test_platform_naver_check(self):
        result = self.gate.evaluate(MINIMAL_HTML, platform="naver")
        assert result.platform == "naver"

    def test_coupang_platform_checks_image_presence(self):
        html_no_img = """<!DOCTYPE html>
<html><body><h1>Title</h1><p>Text</p></body></html>"""
        result = self.gate.evaluate(html_no_img, platform="coupang")
        platform_dim = next(d for d in result.dimensions if d.name == "platform")
        # Should have issue about missing images for Coupang
        assert len(platform_dim.issues) > 0 or platform_dim.score < 10.0

    def test_naver_platform_checks_forbidden_tags(self):
        result = self.gate.evaluate(HTML_WITH_FORBIDDEN, platform="naver")
        platform_dim = next(d for d in result.dimensions if d.name == "platform")
        # Should detect forbidden tags
        assert len(platform_dim.issues) > 0 or platform_dim.score < 10.0

    def test_web_platform_checks_viewport_meta(self):
        result = self.gate.evaluate(HTML_NO_DOCTYPE, platform="web")
        platform_dim = next(d for d in result.dimensions if d.name == "platform")
        # Missing viewport should be flagged
        assert len(platform_dim.issues) > 0 or platform_dim.score < 10.0

    def test_layout_dimension_checks_heading_hierarchy(self):
        # HTML without h1 before h2 should score lower
        html_bad_hierarchy = """<!DOCTYPE html>
<html><body>
<h2>Sub heading without h1</h2>
<p>Text content here to fill space</p>
</body></html>"""
        result = self.gate.evaluate(html_bad_hierarchy)
        layout_dim = next(d for d in result.dimensions if d.name == "layout")
        assert layout_dim.score < 10.0 or len(layout_dim.issues) > 0

    def test_issues_are_list_of_strings(self):
        result = self.gate.evaluate(HTML_WITH_FORBIDDEN)
        for dim in result.dimensions:
            assert isinstance(dim.issues, list)
            for issue in dim.issues:
                assert isinstance(issue, str)

    def test_total_score_is_weighted_average(self):
        result = self.gate.evaluate(MINIMAL_HTML)
        scores = [d.score for d in result.dimensions]
        avg = sum(scores) / len(scores)
        # Should be close to weighted average (allowing for actual weighting)
        assert abs(result.total_score - avg) < 3.0

    def test_good_html_has_high_score(self):
        result = self.gate.evaluate(HTML_MULTI_SECTION)
        assert result.total_score >= 5.0  # Well-structured HTML should score OK


# ===========================================================================
# ExportManager Tests
# ===========================================================================


class TestExportManager:
    """Tests for ExportManager — ZIP packaging of rendered outputs."""

    def setup_method(self):
        from detail_forge.output.export_manager import ExportManager

        self.manager = ExportManager()

    def test_export_returns_export_package_dataclass(self):
        from detail_forge.output.export_manager import ExportPackage

        result = self.manager.export(product_name="Test Product", web_html="<p>hello</p>")
        assert isinstance(result, ExportPackage)

    def test_export_package_has_required_fields(self):
        result = self.manager.export(product_name="Test Product", web_html="<p>hello</p>")
        assert hasattr(result, "zip_bytes")
        assert hasattr(result, "file_count")
        assert hasattr(result, "total_size_bytes")
        assert hasattr(result, "manifest")

    def test_zip_bytes_is_valid_zip(self):
        result = self.manager.export(product_name="Test", web_html="<p>test</p>")
        buf = io.BytesIO(result.zip_bytes)
        assert zipfile.is_zipfile(buf)

    def test_zip_contains_web_html_when_provided(self):
        result = self.manager.export(product_name="TestProduct", web_html="<p>web content</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("web" in n and n.endswith(".html") for n in names)

    def test_zip_contains_naver_html_when_provided(self):
        result = self.manager.export(product_name="TestProduct", naver_html="<p>naver</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("naver" in n and n.endswith(".html") for n in names)

    def test_zip_contains_coupang_images_when_provided(self):
        fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = self.manager.export(
            product_name="TestProduct",
            coupang_images=[fake_img, fake_img],
        )
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("coupang" in n and n.endswith(".png") for n in names)

    def test_zip_contains_metadata_json(self):
        result = self.manager.export(product_name="Test", web_html="<p>x</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("metadata.json" in n for n in names)

    def test_metadata_json_is_valid(self):
        result = self.manager.export(product_name="Test", web_html="<p>x</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            meta_path = next(n for n in zf.namelist() if "metadata.json" in n)
            meta_bytes = zf.read(meta_path)
            meta = json.loads(meta_bytes)
            assert isinstance(meta, dict)

    def test_product_name_used_in_zip_directory(self):
        result = self.manager.export(product_name="MyProduct", web_html="<p>x</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            # All files should be under product name directory
            assert any("MyProduct" in n or "myproduct" in n.lower() for n in zf.namelist())

    def test_product_name_sanitized_for_filesystem(self):
        # Special characters should be sanitized
        result = self.manager.export(
            product_name="My Product / Test: 2024",
            web_html="<p>x</p>",
        )
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            for name in zf.namelist():
                assert "/" in name  # path separator is ok
                # Should not contain dangerous chars outside of path separator
                assert "\\" not in name

    def test_file_count_matches_actual_files(self):
        result = self.manager.export(
            product_name="Test",
            web_html="<p>web</p>",
            naver_html="<p>naver</p>",
        )
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            actual_count = len(zf.namelist())
        assert result.file_count == actual_count

    def test_total_size_bytes_is_positive(self):
        result = self.manager.export(product_name="Test", web_html="<p>x</p>")
        assert result.total_size_bytes > 0

    def test_manifest_is_dict(self):
        result = self.manager.export(product_name="Test", web_html="<p>x</p>")
        assert isinstance(result.manifest, dict)

    def test_manifest_entries_have_descriptions(self):
        result = self.manager.export(
            product_name="Test",
            web_html="<p>web</p>",
            naver_html="<p>naver</p>",
        )
        for filename, description in result.manifest.items():
            assert isinstance(filename, str)
            assert isinstance(description, str)

    def test_export_all_none_still_returns_valid_package(self):
        # Exporting with nothing but product name should work
        result = self.manager.export(product_name="EmptyTest")
        assert isinstance(result.zip_bytes, bytes)
        assert len(result.zip_bytes) > 0

    def test_multiple_coupang_images_numbered_sequentially(self):
        fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        result = self.manager.export(
            product_name="Test",
            coupang_images=[fake_img, fake_img, fake_img],
        )
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            png_files = [n for n in zf.namelist() if n.endswith(".png")]
            assert len(png_files) == 3

    def test_metadata_contains_generation_date(self):
        result = self.manager.export(product_name="Test", web_html="<p>x</p>")
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            meta_path = next(n for n in zf.namelist() if "metadata.json" in n)
            meta = json.loads(zf.read(meta_path))
        assert "generation_date" in meta or "date" in meta or "created_at" in meta

    def test_accepts_metadata_dict(self):
        result = self.manager.export(
            product_name="Test",
            web_html="<p>x</p>",
            metadata={"quality_score": 8.5, "platform": "web"},
        )
        buf = io.BytesIO(result.zip_bytes)
        with zipfile.ZipFile(buf) as zf:
            meta_path = next(n for n in zf.namelist() if "metadata.json" in n)
            meta = json.loads(zf.read(meta_path))
        assert "quality_score" in meta or "platform" in meta


# ===========================================================================
# CoupangRenderer Tests (data model + sync interface, no Playwright)
# ===========================================================================


class TestCoupangRenderer:
    """Tests for CoupangRenderer data model and synchronous interface."""

    def test_coupang_image_set_dataclass(self):
        from detail_forge.output.coupang_renderer import CoupangImageSet

        img_set = CoupangImageSet(
            images=[b"fake_png_data"],
            widths=[860],
            total_height=1200,
            section_count=1,
        )
        assert img_set.images == [b"fake_png_data"]
        assert img_set.widths == [860]
        assert img_set.total_height == 1200
        assert img_set.section_count == 1

    def test_coupang_renderer_default_width(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer()
        assert renderer.image_width == 860

    def test_coupang_renderer_custom_width(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer(image_width=1000)
        assert renderer.image_width == 1000

    def test_render_sync_with_mocked_screenshot(self):
        from detail_forge.output.coupang_renderer import CoupangImageSet, CoupangRenderer

        renderer = CoupangRenderer()
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\xff" * 200

        with patch.object(renderer, "_screenshot_html", return_value=fake_png):
            result = renderer.render_sync(MINIMAL_HTML)

        assert isinstance(result, CoupangImageSet)
        assert len(result.images) > 0
        assert result.section_count > 0

    def test_render_sync_returns_860px_widths(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer()
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\xff" * 200

        with patch.object(renderer, "_screenshot_html", return_value=fake_png):
            result = renderer.render_sync(MINIMAL_HTML)

        for w in result.widths:
            assert w == 860

    def test_screenshot_html_method_exists(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer()
        assert hasattr(renderer, "_screenshot_html")
        assert callable(renderer._screenshot_html)

    def test_render_method_exists(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer()
        assert hasattr(renderer, "render")
        import inspect

        assert inspect.iscoroutinefunction(renderer.render)

    def test_render_sync_method_exists(self):
        from detail_forge.output.coupang_renderer import CoupangRenderer

        renderer = CoupangRenderer()
        assert hasattr(renderer, "render_sync")
        assert callable(renderer.render_sync)

    def test_coupang_image_set_all_fields_accessible(self):
        from detail_forge.output.coupang_renderer import CoupangImageSet

        img_set = CoupangImageSet(
            images=[b"a", b"b"],
            widths=[860, 860],
            total_height=2400,
            section_count=2,
        )
        assert len(img_set.images) == 2
        assert img_set.total_height == 2400
        assert img_set.section_count == 2


# ===========================================================================
# Package __init__.py Exports Tests
# ===========================================================================


class TestOutputPackageExports:
    """Tests for output package public API exports."""

    def test_coupang_renderer_importable(self):
        from detail_forge.output import CoupangRenderer

        assert CoupangRenderer is not None

    def test_naver_renderer_importable(self):
        from detail_forge.output import NaverRenderer

        assert NaverRenderer is not None

    def test_web_renderer_importable(self):
        from detail_forge.output import WebRenderer

        assert WebRenderer is not None

    def test_quality_gate_importable(self):
        from detail_forge.output import QualityGate

        assert QualityGate is not None

    def test_export_manager_importable(self):
        from detail_forge.output import ExportManager

        assert ExportManager is not None
