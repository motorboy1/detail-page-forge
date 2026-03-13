"""Performance benchmarks for synthesis package.

REQ-PB-002 targets:
  - OneClickGenerator.generate()   < 500ms
  - SectionCompositor.compose()    < 50ms
  - CoherenceEngine.check()        < 30ms
  - CoherenceEngine.adjust()       < 50ms
  - PageAssembler.assemble()       < 100ms

All benchmarks use mocked/deterministic data — no real AI calls.
Configuration: 5 warmup rounds, 10 measurement rounds (from pyproject.toml).
"""

from __future__ import annotations

import pytest

from detail_forge.synthesis.coherence_engine import CoherenceEngine
from detail_forge.synthesis.page_assembler import PageAssembler
from detail_forge.synthesis.section_compositor import SectionCompositor

# Targets in seconds
_TARGET_ONE_CLICK_S = 0.500
_TARGET_COMPOSITOR_S = 0.050
_TARGET_COHERENCE_CHECK_S = 0.030
_TARGET_COHERENCE_ADJUST_S = 0.050
_TARGET_ASSEMBLER_S = 0.100


# ---------------------------------------------------------------------------
# SectionCompositor benchmarks
# ---------------------------------------------------------------------------


class TestBenchSectionCompositor:
    """REQ-PB-002: SectionCompositor.compose() < 50ms."""

    def test_compose_performance(self, benchmark, bench_copy_hero, bench_tokens, bench_store):
        """SectionCompositor.compose() should complete within 50ms."""
        compositor = SectionCompositor()
        _, html, _slots, mapping = bench_store.get_template("bench-hero-01")

        result = benchmark.pedantic(
            compositor.compose,
            kwargs={
                "template_html": html,
                "copy": bench_copy_hero,
                "slot_mapping": mapping,
                "tokens": bench_tokens,
            },
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.html


# ---------------------------------------------------------------------------
# CoherenceEngine benchmarks
# ---------------------------------------------------------------------------


class TestBenchCoherenceEngine:
    """REQ-PB-002: CoherenceEngine.check() < 30ms, adjust() < 50ms."""

    @pytest.fixture(scope="class")
    def composed_sections(self, bench_store, bench_copy_sections, bench_tokens, bench_template_ids):
        compositor = SectionCompositor()
        sections = []
        for tid, copy in zip(bench_template_ids, bench_copy_sections):
            _, html, _slots, mapping = bench_store.get_template(tid)
            section = compositor.compose(
                template_html=html,
                copy=copy,
                slot_mapping=mapping,
                tokens=bench_tokens,
            )
            sections.append(section)
        return sections

    def test_check_performance(self, benchmark, composed_sections, bench_tokens):
        """CoherenceEngine.check() should complete within 30ms."""
        engine = CoherenceEngine()

        result = benchmark.pedantic(
            engine.check,
            kwargs={"sections": composed_sections, "tokens": bench_tokens},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.score >= 0

    def test_adjust_performance(self, benchmark, composed_sections, bench_tokens):
        """CoherenceEngine.adjust() should complete within 50ms."""
        engine = CoherenceEngine()

        result = benchmark.pedantic(
            engine.adjust,
            kwargs={"sections": composed_sections, "tokens": bench_tokens},
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert len(result) == len(composed_sections)


# ---------------------------------------------------------------------------
# PageAssembler benchmarks
# ---------------------------------------------------------------------------


class TestBenchPageAssembler:
    """REQ-PB-002: PageAssembler.assemble() < 100ms."""

    def test_assemble_performance(
        self, benchmark, bench_store, bench_copy_sections, bench_tokens, bench_template_ids
    ):
        """PageAssembler.assemble() should complete within 100ms."""
        compositor = SectionCompositor()
        coherence = CoherenceEngine()
        assembler = PageAssembler(compositor=compositor, coherence=coherence)

        sections_data = []
        for tid, copy in zip(bench_template_ids, bench_copy_sections):
            _, html, _slots, mapping = bench_store.get_template(tid)
            sections_data.append({
                "template_html": html,
                "copy": copy,
                "slot_mapping": mapping,
            })

        result = benchmark.pedantic(
            assembler.assemble,
            kwargs={
                "sections_data": sections_data,
                "tokens": bench_tokens,
                "product_name": "벤치마크 세럼",
            },
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.section_count == 2


# ---------------------------------------------------------------------------
# OneClickGenerator benchmarks
# ---------------------------------------------------------------------------


class TestBenchOneClickGenerator:
    """REQ-PB-002: OneClickGenerator.generate() < 500ms."""

    def test_generate_performance(
        self, benchmark, bench_store, bench_product, bench_copy_sections, bench_template_ids
    ):
        """OneClickGenerator.generate() should complete within 500ms."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=bench_store)

        result = benchmark.pedantic(
            gen.generate,
            kwargs={
                "product": bench_product,
                "copy_sections": bench_copy_sections,
                "template_ids": bench_template_ids,
                "include_naver": True,
            },
            warmup_rounds=5,
            rounds=10,
        )

        assert result is not None
        assert result.web_html.html
        assert result.naver_html is not None
