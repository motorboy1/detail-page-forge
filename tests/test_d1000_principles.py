"""Unit tests for d1000_principles module — T-1.2.2."""

from __future__ import annotations

import pytest

from detail_forge.designer.d1000_principles import (
    CATEGORY_PROFILES,
    D1000_GUIDE,
    PRINCIPLES,
    SECTION_PRINCIPLE_MAP,
    STYLE_KEYWORDS,
    get_enriched_prompt,
    get_principle,
    get_section_prompt,
    get_system_prompt_compact,
    match_principles_from_description,
    search_knowledge,
)

# ── PRINCIPLES dict structure ───────────────────────────────────────────────


class TestPrinciplesDict:
    def test_principles_has_50_entries(self):
        total = sum(len(v) for v in PRINCIPLES.values())
        assert total == 50

    def test_principles_required_fields(self):
        for category, items in PRINCIPLES.items():
            for item in items:
                assert "id" in item, f"Missing 'id' in category={category}"
                assert "name" in item, f"Missing 'name' in id={item.get('id')}"
                assert "rule" in item, f"Missing 'rule' in id={item.get('id')}"

    def test_principle_ids_are_1_to_50(self):
        all_ids = sorted(item["id"] for items in PRINCIPLES.values() for item in items)
        assert all_ids == list(range(1, 51))

    def test_principles_categories_are_expected(self):
        expected = {
            "layout",
            "composition",
            "visual_trick",
            "color",
            "typography",
            "decoration",
            "texture",
        }
        assert set(PRINCIPLES.keys()) == expected

    def test_principle_names_are_non_empty_strings(self):
        for items in PRINCIPLES.values():
            for item in items:
                assert isinstance(item["name"], str) and item["name"].strip()

    def test_principle_rules_are_non_empty_strings(self):
        for items in PRINCIPLES.values():
            for item in items:
                assert isinstance(item["rule"], str) and item["rule"].strip()


# ── CATEGORY_PROFILES structure ─────────────────────────────────────────────


class TestCategoryProfiles:
    def test_has_six_categories(self):
        assert len(CATEGORY_PROFILES) == 6

    def test_expected_category_keys(self):
        expected = {"food", "electronics", "fashion", "beauty", "health", "lifestyle"}
        assert set(CATEGORY_PROFILES.keys()) == expected

    def test_each_profile_has_key_principles(self):
        for cat, profile in CATEGORY_PROFILES.items():
            assert "key_principles" in profile, f"Missing key_principles in {cat}"
            assert isinstance(profile["key_principles"], list)
            assert len(profile["key_principles"]) > 0

    def test_each_profile_has_name_field(self):
        for cat, profile in CATEGORY_PROFILES.items():
            assert "name" in profile and profile["name"]

    def test_each_profile_has_color_mood(self):
        for cat, profile in CATEGORY_PROFILES.items():
            assert "color_mood" in profile and profile["color_mood"]

    def test_key_principles_are_valid_ids(self):
        valid_ids = {item["id"] for items in PRINCIPLES.values() for item in items}
        for cat, profile in CATEGORY_PROFILES.items():
            for pid in profile["key_principles"]:
                assert pid in valid_ids, f"Invalid principle id={pid} in category={cat}"


# ── STYLE_KEYWORDS mapping ──────────────────────────────────────────────────


class TestStyleKeywords:
    def test_style_keywords_is_non_empty(self):
        assert len(STYLE_KEYWORDS) > 0

    def test_each_keyword_maps_to_list_of_ints(self):
        for keyword, ids in STYLE_KEYWORDS.items():
            assert isinstance(ids, list), f"Expected list for keyword={keyword}"
            for pid in ids:
                assert isinstance(pid, int)

    def test_style_keywords_contain_common_moods(self):
        expected_keywords = {"고급", "미니멀", "트렌디", "레트로", "전문적"}
        for kw in expected_keywords:
            assert kw in STYLE_KEYWORDS, f"Missing keyword: {kw}"


# ── SECTION_PRINCIPLE_MAP ───────────────────────────────────────────────────


class TestSectionPrincipleMap:
    EXPECTED_SECTIONS = {
        "hero",
        "features",
        "benefits",
        "testimonials",
        "specs",
        "cta",
        "guarantee",
        "social_proof",
    }

    def test_has_8_section_types(self):
        assert len(SECTION_PRINCIPLE_MAP) == 8

    def test_section_types_match_expected(self):
        assert set(SECTION_PRINCIPLE_MAP.keys()) == self.EXPECTED_SECTIONS

    def test_each_section_has_primary_accent_color(self):
        for section, data in SECTION_PRINCIPLE_MAP.items():
            assert "primary" in data, f"Missing primary in {section}"
            assert "accent" in data, f"Missing accent in {section}"
            assert "color" in data, f"Missing color in {section}"

    def test_section_principle_lists_are_non_empty(self):
        for section, data in SECTION_PRINCIPLE_MAP.items():
            assert len(data["primary"]) > 0
            assert len(data["accent"]) > 0
            assert len(data["color"]) > 0


# ── get_enriched_prompt ─────────────────────────────────────────────────────


class TestGetEnrichedPrompt:
    @pytest.mark.parametrize("detail_level", ["brief", "medium", "full"])
    def test_returns_non_empty_for_valid_principles(self, detail_level):
        result = get_enriched_prompt([1, 3, 15], detail_level=detail_level)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_returns_compact_prompt_for_empty_principles(self):
        result = get_enriched_prompt([])
        compact = get_system_prompt_compact()
        assert result == compact

    def test_result_contains_principle_names(self):
        result = get_enriched_prompt([1, 15])
        assert "4개의 점" in result or "#01" in result
        assert "6:3:1" in result or "#15" in result

    def test_all_50_principles_can_be_enriched(self):
        all_ids = [item["id"] for items in PRINCIPLES.values() for item in items]
        result = get_enriched_prompt(all_ids, detail_level="brief")
        assert isinstance(result, str)
        assert len(result) > 100

    @pytest.mark.parametrize("principle_id", [1, 5, 10, 25, 50])
    def test_single_principle_enriched_prompt(self, principle_id):
        result = get_enriched_prompt([principle_id])
        assert isinstance(result, str)
        assert len(result) > 30


# ── search_knowledge ────────────────────────────────────────────────────────


class TestSearchKnowledge:
    def test_returns_list(self):
        results = search_knowledge("디자인")
        assert isinstance(results, list)

    def test_result_items_have_expected_fields(self):
        results = search_knowledge("디자인")
        for r in results:
            assert "id" in r
            assert "name" in r
            assert "relevance" in r

    def test_top_n_limit_respected(self):
        results = search_knowledge("디자인", top_n=3)
        assert len(results) <= 3

    def test_no_results_for_unknown_query(self):
        results = search_knowledge("XYZXYZ_NONEXISTENT_TERM_12345")
        assert results == []

    def test_results_sorted_by_relevance(self):
        results = search_knowledge("디자인", top_n=10)
        if len(results) >= 2:
            assert results[0]["relevance"] >= results[-1]["relevance"]


# ── get_principle helper ────────────────────────────────────────────────────


class TestGetPrinciple:
    def test_returns_dict_for_valid_id(self):
        result = get_principle(1)
        assert result is not None
        assert result["id"] == 1

    def test_returns_none_for_invalid_id(self):
        result = get_principle(999)
        assert result is None

    @pytest.mark.parametrize("pid", [1, 15, 28, 36, 50])
    def test_known_principles_are_found(self, pid):
        assert get_principle(pid) is not None

    def test_boundary_principle_50(self):
        p = get_principle(50)
        assert p is not None
        assert p["id"] == 50


# ── get_section_prompt ──────────────────────────────────────────────────────


class TestGetSectionPrompt:
    @pytest.mark.parametrize(
        "section_type",
        [
            "hero",
            "features",
            "benefits",
            "testimonials",
            "specs",
            "cta",
            "guarantee",
            "social_proof",
        ],
    )
    def test_returns_non_empty_for_all_sections(self, section_type):
        result = get_section_prompt(section_type)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_empty_for_unknown_section(self):
        result = get_section_prompt("nonexistent_section")
        assert result == ""

    def test_section_prompt_with_category(self):
        result = get_section_prompt("hero", "beauty")
        assert isinstance(result, str)
        assert len(result) > 0


# ── match_principles_from_description ──────────────────────────────────────


class TestMatchPrinciplesFromDescription:
    def test_returns_list_of_ints(self):
        result = match_principles_from_description("고급스러운 미니멀 디자인")
        assert isinstance(result, list)
        assert all(isinstance(p, int) for p in result)

    def test_returns_defaults_for_unrecognized_text(self):
        result = match_principles_from_description("알수없는텍스트abcxyz")
        assert result == [1, 3, 11, 15, 4] or len(result) > 0

    def test_trendy_keyword_maps_to_trendy_principles(self):
        result = match_principles_from_description("트렌디한 힙한 디자인")
        # 트렌디 -> [36, 29, 38, 42, 32] / 힙한 -> [29, 42, 22, 33, 36]
        trendy_ids = set(STYLE_KEYWORDS.get("트렌디", []) + STYLE_KEYWORDS.get("힙한", []))
        assert any(p in trendy_ids for p in result)

    def test_result_is_sorted(self):
        result = match_principles_from_description("고급")
        assert result == sorted(result)


# ── D1000_GUIDE completeness ────────────────────────────────────────────────


class TestD1000Guide:
    def test_guide_has_50_entries(self):
        assert len(D1000_GUIDE) == 50

    def test_guide_entries_have_required_fields(self):
        for entry in D1000_GUIDE:
            assert "id" in entry
            assert "cat" in entry
            assert "name" in entry
            assert "tip" in entry
            assert "prompt" in entry

    def test_guide_ids_match_principles_ids(self):
        guide_ids = {e["id"] for e in D1000_GUIDE}
        principle_ids = {item["id"] for items in PRINCIPLES.values() for item in items}
        assert guide_ids == principle_ids
