"""Performance benchmarks for output package.

REQ-PB-002 targets:
  - NaverRenderer.render()   < 200ms
  - WebRenderer.render()     < 200ms
  - QualityGate.evaluate()   < 100ms

All benchmarks use pre-assembled HTML — no real AI calls.
Configuration: 5 warmup rounds, 10 measurement rounds (from pyproject.toml).
"""

from __future__ import annotations

# Targets in seconds
_TARGET_NAVER_S = 0.200
_TARGET_WEB_S = 0.200
_TARGET_QUALITY_S = 0.100


# ---------------------------------------------------------------------------
# NaverRenderer benchmarks
# ---------------------------------------------------------------------------


class TestBenchNaverRenderer:
    """REQ-PB-002: NaverRenderer.render() < 200ms."""

    def test_render_performance(self, benchmark, bench_assembled_html):
        """NaverRenderer.render() should complete within 200ms."""
        from detail_forge.output.naver_renderer import NaverRenderer

        renderer = NaverRenderer()

        result = benchmark.pedantic(
            renderer.render,
            kwargs={"html": bench_assembled_html},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.html
        assert result.size_bytes > 0


# ---------------------------------------------------------------------------
# WebRenderer benchmarks
# ---------------------------------------------------------------------------


class TestBenchWebRenderer:
    """REQ-PB-002: WebRenderer.render() < 200ms."""

    def test_render_performance(self, benchmark, bench_assembled_html, bench_product):
        """WebRenderer.render() should complete within 200ms."""
        from detail_forge.output.web_renderer import WebRenderer

        renderer = WebRenderer()

        result = benchmark.pedantic(
            renderer.render,
            kwargs={"html": bench_assembled_html, "product_name": bench_product.name},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.html
        assert result.viewport_meta


# ---------------------------------------------------------------------------
# QualityGate benchmarks
# ---------------------------------------------------------------------------


class TestBenchQualityGate:
    """REQ-PB-002: QualityGate.evaluate() < 100ms."""

    def test_evaluate_performance(self, benchmark, bench_assembled_html):
        """QualityGate.evaluate() should complete within 100ms."""
        from detail_forge.output.quality_gate import QualityGate

        gate = QualityGate()

        result = benchmark.pedantic(
            gate.evaluate,
            kwargs={"html": bench_assembled_html, "platform": "web"},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert len(result.dimensions) == 5
        assert 0 <= result.total_score <= 10

    def test_evaluate_naver_performance(self, benchmark, bench_assembled_html):
        """QualityGate.evaluate() for naver platform should complete within 100ms."""
        from detail_forge.output.quality_gate import QualityGate

        gate = QualityGate()

        result = benchmark.pedantic(
            gate.evaluate,
            kwargs={"html": bench_assembled_html, "platform": "naver"},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.platform == "naver"
