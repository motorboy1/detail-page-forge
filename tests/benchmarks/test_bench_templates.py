"""Performance benchmarks for templates package.

REQ-PB-002 targets:
  - TemplateStore.get_template()    < 5ms
  - TemplateSearcher.search()       < 20ms

All benchmarks use a session-scoped temp store — no real filesystem overhead.
Configuration: 5 warmup rounds, 10 measurement rounds (from pyproject.toml).
"""

from __future__ import annotations

# Targets in seconds
_TARGET_STORE_GET_S = 0.005
_TARGET_SEARCHER_SEARCH_S = 0.020


# ---------------------------------------------------------------------------
# TemplateStore benchmarks
# ---------------------------------------------------------------------------


class TestBenchTemplateStore:
    """REQ-PB-002: TemplateStore.get_template() < 5ms."""

    def test_get_template_performance(self, benchmark, bench_store):
        """TemplateStore.get_template() should complete within 5ms."""
        result = benchmark.pedantic(
            bench_store.get_template,
            args=("bench-hero-01",),
            warmup_rounds=5,
            rounds=10,
        )

        meta, html, slots, mapping = result
        assert meta.id == "bench-hero-01"
        assert html
        assert slots
        assert mapping is not None

    def test_list_templates_performance(self, benchmark, bench_store):
        """TemplateStore.list_templates() should be fast (under 5ms)."""
        result = benchmark.pedantic(
            bench_store.list_templates,
            warmup_rounds=5,
            rounds=10,
        )

        assert isinstance(result, list)
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# TemplateSearcher benchmarks
# ---------------------------------------------------------------------------


class TestBenchTemplateSearcher:
    """REQ-PB-002: TemplateSearcher.search() < 20ms."""

    def test_search_by_section_type_performance(self, benchmark, bench_store):
        """TemplateSearcher.search(section_type=...) should complete within 20ms."""
        from detail_forge.templates.search import TemplateSearcher

        searcher = TemplateSearcher(store=bench_store)

        result = benchmark.pedantic(
            searcher.search,
            kwargs={"section_type": "hero"},
            warmup_rounds=5,
            rounds=10,
        )

        assert isinstance(result, list)

    def test_search_by_principles_performance(self, benchmark, bench_store):
        """TemplateSearcher.search(d1000_principles=...) should complete within 20ms."""
        from detail_forge.templates.search import TemplateSearcher

        searcher = TemplateSearcher(store=bench_store)

        result = benchmark.pedantic(
            searcher.search,
            kwargs={"d1000_principles": [1, 3, 15, 21]},
            warmup_rounds=5,
            rounds=10,
        )

        assert isinstance(result, list)

    def test_search_all_performance(self, benchmark, bench_store):
        """TemplateSearcher.search() with no filters should complete within 20ms."""
        from detail_forge.templates.search import TemplateSearcher

        searcher = TemplateSearcher(store=bench_store)

        result = benchmark.pedantic(
            searcher.search,
            warmup_rounds=5,
            rounds=10,
        )

        assert isinstance(result, list)
        assert len(result) >= 2

    def test_recommend_performance(self, benchmark, bench_store):
        """TemplateSearcher.recommend() should complete within 20ms."""
        from detail_forge.templates.search import TemplateSearcher

        searcher = TemplateSearcher(store=bench_store)

        result = benchmark.pedantic(
            searcher.recommend,
            kwargs={"selected_principles": [1, 15, 21], "category": "beauty"},
            warmup_rounds=5,
            rounds=10,
        )

        assert isinstance(result, list)
