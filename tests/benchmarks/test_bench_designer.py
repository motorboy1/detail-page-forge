"""Performance benchmarks for designer package.

REQ-PB-002 targets:
  - ThemeGenerator.generate()          < 30ms
  - DesignTokenSet.from_principles()   < 10ms

All benchmarks are fully deterministic — no AI calls.
Configuration: 5 warmup rounds, 10 measurement rounds (from pyproject.toml).
"""

from __future__ import annotations

# Targets in seconds
_TARGET_THEME_GENERATOR_S = 0.030
_TARGET_DESIGN_TOKENS_S = 0.010


# ---------------------------------------------------------------------------
# ThemeGenerator benchmarks
# ---------------------------------------------------------------------------


class TestBenchThemeGenerator:
    """REQ-PB-002: ThemeGenerator.generate() < 30ms."""

    def test_generate_recipe_performance(self, benchmark):
        """ThemeGenerator.generate() for a named recipe should complete within 30ms."""
        from detail_forge.designer.theme_generator import ThemeGenerator

        gen = ThemeGenerator()

        result = benchmark.pedantic(
            gen.generate,
            args=("classic_trust",),
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.name == "classic_trust"
        assert result.tokens is not None

    def test_generate_premium_minimal_performance(self, benchmark):
        """ThemeGenerator.generate('premium_minimal') should complete within 30ms."""
        from detail_forge.designer.theme_generator import ThemeGenerator

        gen = ThemeGenerator()

        result = benchmark.pedantic(
            gen.generate,
            args=("premium_minimal",),
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.mood == "elegant"

    def test_generate_custom_performance(self, benchmark):
        """ThemeGenerator.generate_custom() should complete within 30ms."""
        from detail_forge.designer.theme_generator import ThemeGenerator

        gen = ThemeGenerator()

        result = benchmark.pedantic(
            gen.generate_custom,
            kwargs={"principle_ids": [3, 15, 21, 28]},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.name == "custom"


# ---------------------------------------------------------------------------
# DesignTokenSet benchmarks
# ---------------------------------------------------------------------------


class TestBenchDesignTokenSet:
    """REQ-PB-002: DesignTokenSet.from_principles() < 10ms."""

    def test_from_principles_performance(self, benchmark):
        """DesignTokenSet.from_principles() should complete within 10ms."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        result = benchmark.pedantic(
            DesignTokenSet.from_principles,
            kwargs={"principle_ids": [1, 3, 15, 21]},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert len(result.tokens) > 0

    def test_from_principles_all_performance(self, benchmark):
        """DesignTokenSet.from_principles() with all 50 principles should complete within 10ms."""
        from detail_forge.designer.design_tokens import DesignTokenSet

        all_ids = list(range(1, 51))

        result = benchmark.pedantic(
            DesignTokenSet.from_principles,
            kwargs={"principle_ids": all_ids},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert len(result.tokens) > 0

    def test_to_css_performance(self, benchmark, bench_tokens):
        """DesignTokenSet.to_css() should be fast (sub-1ms)."""
        result = benchmark.pedantic(
            bench_tokens.to_css,
            warmup_rounds=5,
            rounds=10,
        )

        assert result
        assert "--df-color-primary" in result
        # to_css is a simple string join — must be well under 10ms
