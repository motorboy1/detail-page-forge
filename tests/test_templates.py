"""Unit tests for templates module (models, store, search) — T-1.2.3."""

from __future__ import annotations

import pytest

from detail_forge.templates.models import SlotMapping, TemplateIndex, TemplateMetadata
from detail_forge.templates.search import TemplateSearcher
from detail_forge.templates.store import TemplateStore

# ── TemplateMetadata ─────────────────────────────────────────────────────────


class TestTemplateMetadata:
    def test_default_values(self):
        meta = TemplateMetadata()
        assert meta.id == ""
        assert meta.name == ""
        assert meta.section_type == "full_page"
        assert meta.d1000_principles == []
        assert meta.category == "general"
        assert meta.ssim_score == 0.0
        assert meta.slot_count == 0
        assert meta.tags == []
        assert meta.created_at == ""

    def test_custom_values(self, sample_template_metadata):
        meta = sample_template_metadata
        assert meta.id == "test-hero-01"
        assert meta.section_type == "hero"
        assert meta.category == "beauty"
        assert meta.ssim_score == 0.92

    def test_to_dict_round_trip(self, sample_template_metadata):
        d = sample_template_metadata.to_dict()
        restored = TemplateMetadata.from_dict(d)
        assert restored.id == sample_template_metadata.id
        assert restored.name == sample_template_metadata.name
        assert restored.d1000_principles == sample_template_metadata.d1000_principles
        assert restored.tags == sample_template_metadata.tags
        assert restored.ssim_score == sample_template_metadata.ssim_score

    def test_to_dict_contains_all_fields(self, sample_template_metadata):
        d = sample_template_metadata.to_dict()
        expected_keys = {
            "id",
            "name",
            "section_type",
            "d1000_principles",
            "category",
            "source_url",
            "ssim_score",
            "slot_count",
            "thumbnail_path",
            "tags",
            "created_at",
        }
        assert expected_keys == set(d.keys())

    def test_from_dict_ignores_extra_keys(self):
        d = {"id": "x", "name": "X", "extra_unknown_field": "ignored"}
        meta = TemplateMetadata.from_dict(d)
        assert meta.id == "x"
        assert meta.name == "X"

    def test_d1000_principles_list(self):
        meta = TemplateMetadata(d1000_principles=[1, 3, 15])
        assert meta.d1000_principles == [1, 3, 15]


# ── SlotMapping ──────────────────────────────────────────────────────────────


class TestSlotMapping:
    def test_default_values(self):
        sm = SlotMapping()
        assert sm.headline is None
        assert sm.subheadline is None
        assert sm.body == []
        assert sm.cta_text is None
        assert sm.product_image is None
        assert sm.background_image is None
        assert sm.extra == {}

    def test_custom_values(self, sample_slot_mapping):
        sm = sample_slot_mapping
        assert sm.headline == "text_0"
        assert sm.subheadline == "text_1"
        assert sm.body == ["text_2", "text_3"]
        assert sm.cta_text == "text_4"
        assert sm.product_image == "img_0"

    def test_to_dict_round_trip(self, sample_slot_mapping):
        d = sample_slot_mapping.to_dict()
        restored = SlotMapping.from_dict(d)
        assert restored.headline == sample_slot_mapping.headline
        assert restored.body == sample_slot_mapping.body
        assert restored.cta_text == sample_slot_mapping.cta_text

    def test_to_dict_contains_all_fields(self, sample_slot_mapping):
        d = sample_slot_mapping.to_dict()
        expected_keys = {
            "headline",
            "subheadline",
            "body",
            "cta_text",
            "product_image",
            "background_image",
            "extra",
        }
        assert expected_keys == set(d.keys())

    def test_from_dict_with_missing_keys_uses_defaults(self):
        sm = SlotMapping.from_dict({})
        assert sm.headline is None
        assert sm.body == []

    def test_extra_field_mapping(self):
        sm = SlotMapping(extra={"custom_field": "slot_99"})
        d = sm.to_dict()
        restored = SlotMapping.from_dict(d)
        assert restored.extra == {"custom_field": "slot_99"}


# ── TemplateIndex ────────────────────────────────────────────────────────────


class TestTemplateIndex:
    def test_default_values(self):
        index = TemplateIndex()
        assert index.version == 1
        assert index.templates == []

    def test_to_dict_round_trip(self, sample_template_metadata):
        index = TemplateIndex(templates=[sample_template_metadata])
        d = index.to_dict()
        restored = TemplateIndex.from_dict(d)
        assert len(restored.templates) == 1
        assert restored.templates[0].id == sample_template_metadata.id

    def test_from_dict_empty(self):
        index = TemplateIndex.from_dict({})
        assert index.version == 1
        assert index.templates == []


# ── TemplateStore CRUD ───────────────────────────────────────────────────────


class TestTemplateStoreCRUD:
    def test_store_initializes_directory(self, tmp_template_dir):
        store = TemplateStore(tmp_template_dir)
        assert store.base_dir.exists()

    def test_load_index_returns_empty_on_fresh_store(self, tmp_template_dir):
        store = TemplateStore(tmp_template_dir)
        index = store.load_index()
        assert index.templates == []

    def test_add_template_creates_files(
        self, tmp_template_dir, sample_template_metadata, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        store.add_template(
            metadata=sample_template_metadata,
            html="<section>test</section>",
            slots={"text_0": "headline placeholder"},
            slot_mapping=sample_slot_mapping,
        )
        tdir = tmp_template_dir / sample_template_metadata.id
        assert (tdir / "template.html").exists()
        assert (tdir / "slots.json").exists()
        assert (tdir / "slot_mapping.json").exists()
        assert (tdir / "metadata.json").exists()

    def test_add_template_updates_index(
        self, tmp_template_dir, sample_template_metadata, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        store.add_template(
            metadata=sample_template_metadata,
            html="<section>test</section>",
            slots={},
            slot_mapping=sample_slot_mapping,
        )
        index = store.load_index()
        ids = [t.id for t in index.templates]
        assert sample_template_metadata.id in ids

    def test_get_template_returns_stored_data(
        self, tmp_template_dir, sample_template_metadata, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        html_content = "<section><h1>Test</h1></section>"
        slots_data = {"text_0": "headline placeholder"}
        store.add_template(
            metadata=sample_template_metadata,
            html=html_content,
            slots=slots_data,
            slot_mapping=sample_slot_mapping,
        )
        meta, html, slots, mapping = store.get_template(sample_template_metadata.id)
        assert meta.id == sample_template_metadata.id
        assert html == html_content
        assert slots == slots_data
        assert mapping.headline == sample_slot_mapping.headline

    def test_get_template_raises_for_missing_id(self, tmp_template_dir):
        store = TemplateStore(tmp_template_dir)
        with pytest.raises(FileNotFoundError):
            store.get_template("nonexistent-template-id")

    def test_delete_template_removes_directory(
        self, tmp_template_dir, sample_template_metadata, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        store.add_template(
            metadata=sample_template_metadata,
            html="<section>test</section>",
            slots={},
            slot_mapping=sample_slot_mapping,
        )
        store.delete_template(sample_template_metadata.id)
        tdir = tmp_template_dir / sample_template_metadata.id
        assert not tdir.exists()

    def test_delete_template_removes_from_index(
        self, tmp_template_dir, sample_template_metadata, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        store.add_template(
            metadata=sample_template_metadata,
            html="<section>test</section>",
            slots={},
            slot_mapping=sample_slot_mapping,
        )
        store.delete_template(sample_template_metadata.id)
        index = store.load_index()
        ids = [t.id for t in index.templates]
        assert sample_template_metadata.id not in ids

    def test_delete_nonexistent_template_does_not_raise(self, tmp_template_dir):
        store = TemplateStore(tmp_template_dir)
        # Should not raise
        store.delete_template("nonexistent-id")

    def test_list_templates_returns_all(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        for i in range(3):
            meta = TemplateMetadata(
                id=f"template-{i}",
                name=f"Template {i}",
                section_type="hero",
            )
            store.add_template(meta, "<section></section>", {}, sample_slot_mapping)
        result = store.list_templates()
        assert len(result) == 3

    def test_list_templates_filtered_by_section_type(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        for i, section in enumerate(["hero", "hero", "features"]):
            meta = TemplateMetadata(
                id=f"template-{section}-{i}",
                section_type=section,
            )
            store.add_template(meta, "<section></section>", {}, sample_slot_mapping)
        heroes = store.list_templates(section_type="hero")
        assert len(heroes) == 2
        assert all(t.section_type == "hero" for t in heroes)

    def test_add_template_sets_created_at_if_empty(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        meta = TemplateMetadata(id="t-created-at", created_at="")
        store.add_template(meta, "<section></section>", {}, sample_slot_mapping)
        _, _, _, _ = store.get_template("t-created-at")
        # created_at should have been set
        assert meta.created_at != ""

    def test_add_template_with_thumbnail(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        meta = TemplateMetadata(id="t-thumbnail")
        thumbnail_bytes = b"\xff\xd8\xff" + b"\x00" * 100  # minimal jpg-like bytes
        store.add_template(
            meta, "<section></section>", {}, sample_slot_mapping, thumbnail_bytes=thumbnail_bytes
        )
        thumb_file = tmp_template_dir / "t-thumbnail" / "thumbnail.jpg"
        assert thumb_file.exists()

    def test_add_template_overwrites_existing(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        meta = TemplateMetadata(id="t-overwrite", name="Original")
        store.add_template(meta, "<section>v1</section>", {}, sample_slot_mapping)
        meta2 = TemplateMetadata(id="t-overwrite", name="Updated")
        store.add_template(meta2, "<section>v2</section>", {}, sample_slot_mapping)
        index = store.load_index()
        matching = [t for t in index.templates if t.id == "t-overwrite"]
        # Should not duplicate
        assert len(matching) == 1


# ── TemplateSearcher ─────────────────────────────────────────────────────────


class TestTemplateSearcher:
    @pytest.fixture
    def populated_store(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        templates = [
            TemplateMetadata(
                id="t1",
                section_type="hero",
                category="beauty",
                d1000_principles=[1, 3, 15],
                tags=["minimal"],
                ssim_score=0.95,
            ),
            TemplateMetadata(
                id="t2",
                section_type="hero",
                category="food",
                d1000_principles=[27, 24, 21],
                tags=["warm"],
                ssim_score=0.88,
            ),
            TemplateMetadata(
                id="t3",
                section_type="features",
                category="beauty",
                d1000_principles=[5, 13, 42],
                tags=["trendy"],
                ssim_score=0.75,
            ),
            TemplateMetadata(
                id="t4",
                section_type="cta",
                category="electronics",
                d1000_principles=[22, 3, 14],
                tags=["bold"],
                ssim_score=0.60,
            ),
        ]
        for t in templates:
            store.add_template(t, "<section></section>", {}, sample_slot_mapping)
        return store

    def test_search_returns_all_without_filters(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search()
        assert len(results) == 4

    def test_search_filters_by_section_type(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(section_type="hero")
        assert len(results) == 2
        assert all(t.section_type == "hero" for t in results)

    def test_search_filters_by_category(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(category="beauty")
        assert len(results) == 2
        assert all(t.category == "beauty" for t in results)

    def test_search_filters_by_min_ssim(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(min_ssim=0.85)
        assert all(t.ssim_score >= 0.85 for t in results)

    def test_search_filters_by_tags(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(tags=["minimal"])
        assert any(t.id == "t1" for t in results)

    def test_search_sorts_by_d1000_principle_overlap(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        # t1 has [1,3,15], t2 has [27,24,21]
        results = searcher.search(d1000_principles=[1, 3, 15])
        # t1 should rank highest (3 matches)
        assert results[0].id == "t1"

    def test_search_respects_limit(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(limit=2)
        assert len(results) <= 2

    def test_recommend_uses_ssim_threshold(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        # recommend applies min_ssim=0.8 by default
        results = searcher.recommend([1, 3, 15])
        for t in results:
            assert t.ssim_score >= 0.8

    def test_search_no_results_for_unmatched_category(self, populated_store):
        searcher = TemplateSearcher(populated_store)
        results = searcher.search(category="nonexistent_category_xyz")
        assert results == []


# ── TemplateStore.split_to_sections ─────────────────────────────────────────


class TestTemplateStoreSplitToSections:
    @pytest.fixture
    def store_with_full_page(self, tmp_template_dir, sample_slot_mapping):
        store = TemplateStore(tmp_template_dir)
        html = """<!DOCTYPE html><html><body>
            <section class="hero"><h1 data-slot="text_0">Hero</h1></section>
            <section class="features"><p data-slot="text_1">Features</p></section>
        </body></html>"""
        meta = TemplateMetadata(
            id="full-page-01",
            name="Full Page Template",
            section_type="full_page",
            d1000_principles=[1, 3, 15],
            category="beauty",
        )
        store.add_template(meta, html, {}, sample_slot_mapping)
        return store

    def test_split_returns_list(self, store_with_full_page):
        result = store_with_full_page.split_to_sections("full-page-01")
        assert isinstance(result, list)

    def test_split_creates_two_sections(self, store_with_full_page):
        result = store_with_full_page.split_to_sections("full-page-01")
        assert len(result) == 2

    def test_split_section_ids_contain_parent(self, store_with_full_page):
        result = store_with_full_page.split_to_sections("full-page-01")
        for sec in result:
            assert "full-page-01" in sec.id

    def test_split_sections_inherits_d1000_principles(self, store_with_full_page):
        result = store_with_full_page.split_to_sections("full-page-01")
        for sec in result:
            assert sec.d1000_principles == [1, 3, 15]

    def test_split_sections_registered_in_index(self, store_with_full_page):
        result = store_with_full_page.split_to_sections("full-page-01")
        index = store_with_full_page.load_index()
        index_ids = {t.id for t in index.templates}
        for sec in result:
            assert sec.id in index_ids

    def test_split_nonexistent_template_raises(self, tmp_template_dir):
        store = TemplateStore(tmp_template_dir)
        with pytest.raises(FileNotFoundError):
            store.split_to_sections("does-not-exist")

    def test_split_html_without_sections_returns_single(
        self, tmp_template_dir, sample_slot_mapping
    ):
        store = TemplateStore(tmp_template_dir)
        html = "<html><body><div class='hero'>No section tags</div></body></html>"
        meta = TemplateMetadata(id="no-sections-page", section_type="full_page")
        store.add_template(meta, html, {}, sample_slot_mapping)
        result = store.split_to_sections("no-sections-page")
        assert isinstance(result, list)
        assert len(result) >= 1
