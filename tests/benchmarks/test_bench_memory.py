"""Memory profiling benchmarks for detail-page-forge.

REQ-PB-003 targets:
  - OneClickGenerator pipeline  < 100MB peak
  - TemplateStore with 50+ templates  < 200MB

Uses tracemalloc via detail_forge.utils.profiling — no third-party deps.
"""

from __future__ import annotations

import pytest

from detail_forge.utils.profiling import MemoryProfiler, measure_peak_memory_mb

# Memory targets
_TARGET_ONE_CLICK_MB = 100.0
_TARGET_STORE_50_MB = 200.0


# ---------------------------------------------------------------------------
# OneClickGenerator memory benchmark
# ---------------------------------------------------------------------------


class TestMemoryOneClickGenerator:
    """REQ-PB-003: OneClickGenerator pipeline < 100MB peak."""

    def test_pipeline_peak_memory(
        self, bench_store, bench_product, bench_copy_sections, bench_template_ids
    ):
        """OneClickGenerator.generate() should use less than 100MB peak memory."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=bench_store)

        peak_mb = measure_peak_memory_mb(
            gen.generate,
            product=bench_product,
            copy_sections=bench_copy_sections,
            template_ids=bench_template_ids,
            include_naver=True,
        )

        assert peak_mb < _TARGET_ONE_CLICK_MB, (
            f"OneClickGenerator pipeline peak memory {peak_mb:.1f}MB "
            f"exceeds target {_TARGET_ONE_CLICK_MB}MB"
        )

    def test_pipeline_memory_context_manager(
        self, bench_store, bench_product, bench_copy_sections, bench_template_ids
    ):
        """Verify MemoryProfiler context manager works correctly."""
        from detail_forge.synthesis.one_click_generator import OneClickGenerator

        gen = OneClickGenerator(template_store=bench_store)

        with MemoryProfiler() as prof:
            gen.generate(
                product=bench_product,
                copy_sections=bench_copy_sections,
                template_ids=bench_template_ids,
                include_naver=True,
            )

        assert prof.peak_mb >= 0, "Peak memory should be non-negative"
        assert prof.peak_mb < _TARGET_ONE_CLICK_MB, (
            f"OneClickGenerator pipeline (context manager) peak {prof.peak_mb:.1f}MB "
            f"exceeds target {_TARGET_ONE_CLICK_MB}MB"
        )


# ---------------------------------------------------------------------------
# TemplateStore memory benchmark (50+ templates)
# ---------------------------------------------------------------------------


class TestMemoryTemplateStore:
    """REQ-PB-003: TemplateStore with 50+ templates < 200MB."""

    @pytest.fixture(scope="class")
    def store_with_50_templates(self, tmp_path_factory):
        """Build a TemplateStore with 50 templates for memory testing."""
        from detail_forge.templates.models import SlotMapping, TemplateMetadata
        from detail_forge.templates.store import TemplateStore

        store_dir = tmp_path_factory.mktemp("store_50_templates")
        store = TemplateStore(base_dir=store_dir)

        hero_html = """
        <section class="hero">
          <h1 data-slot="text_0">Headline</h1>
          <h2 data-slot="text_1">Subheadline</h2>
          <p data-slot="text_2">Body text.</p>
          <a data-slot="text_3" href="#">CTA</a>
        </section>
        """
        slot_mapping = SlotMapping(
            headline="text_0",
            subheadline="text_1",
            body=["text_2"],
            cta_text="text_3",
        )

        section_types = ["hero", "features", "benefits", "social_proof", "cta"]

        for i in range(50):
            section_type = section_types[i % len(section_types)]
            meta = TemplateMetadata(
                id=f"template-{i:03d}",
                name=f"Template {i:03d}",
                section_type=section_type,
                d1000_principles=[(i % 50) + 1, ((i + 5) % 50) + 1],
                category="beauty",
                source_url=f"https://example.com/template-{i}",
                ssim_score=0.85 + (i % 10) * 0.01,
                slot_count=4,
                tags=[section_type, "test"],
            )
            store.add_template(
                metadata=meta,
                html=hero_html,
                slots={"text_0": "headline", "text_1": "subheadline", "text_2": "body", "text_3": "cta"},
                slot_mapping=slot_mapping,
            )

        return store

    def test_store_50_templates_memory(self, store_with_50_templates):
        """Loading 50+ templates into TemplateStore should use < 200MB peak memory."""

        def load_all_templates():
            templates = store_with_50_templates.list_templates()
            # Also get each template to simulate realistic usage
            for meta in templates[:10]:  # Sample 10 to simulate reads
                store_with_50_templates.get_template(meta.id)
            return templates

        peak_mb = measure_peak_memory_mb(load_all_templates)

        assert peak_mb < _TARGET_STORE_50_MB, (
            f"TemplateStore (50 templates) peak memory {peak_mb:.1f}MB "
            f"exceeds target {_TARGET_STORE_50_MB}MB"
        )

    def test_store_index_memory(self, store_with_50_templates):
        """TemplateStore.load_index() with 50 templates should be lightweight."""
        peak_mb = measure_peak_memory_mb(store_with_50_templates.load_index)

        # Index loading should be very lean
        assert peak_mb < 50.0, (
            f"TemplateStore.load_index() peak memory {peak_mb:.1f}MB "
            f"exceeds 50MB threshold"
        )


# ---------------------------------------------------------------------------
# Profiling utility unit tests
# ---------------------------------------------------------------------------


class TestProfilingUtility:
    """Unit tests for detail_forge.utils.profiling module."""

    def test_measure_peak_memory_returns_positive(self):
        """measure_peak_memory_mb should return a non-negative float."""
        peak = measure_peak_memory_mb(list, range(1000))
        assert isinstance(peak, float)
        assert peak >= 0.0

    def test_measure_peak_memory_large_allocation(self):
        """Large allocation should produce higher peak than small allocation."""
        small_peak = measure_peak_memory_mb(list, range(100))
        large_peak = measure_peak_memory_mb(list, range(100_000))

        # Large allocation must produce measurably higher peak
        assert large_peak > small_peak

    def test_memory_profiler_context_manager(self):
        """MemoryProfiler context manager should capture peak correctly."""
        with MemoryProfiler() as prof:
            data = list(range(10_000))
            del data

        assert prof.peak_mb >= 0.0
        assert isinstance(prof.peak_mb, float)

    def test_memory_profiler_peak_is_mb(self):
        """MemoryProfiler.peak_mb should report in megabytes, not bytes."""
        # Allocate ~1MB
        mb_in_bytes = 1024 * 1024
        data_size = mb_in_bytes // 8  # 8 bytes per int64

        with MemoryProfiler() as prof:
            data = list(range(data_size))
            del data

        # Should be in the range of 0.01 MB to 500 MB (sanity check for MB not bytes)
        assert 0.01 < prof.peak_mb < 500, (
            f"peak_mb={prof.peak_mb} looks like it might not be in MB units"
        )
