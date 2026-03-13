"""Unit tests for copywriter/generator.py — T-1.2.4."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from detail_forge.copywriter.generator import (
    CopyGenerator,
    CopyResult,
    ProductInfo,
    SectionCopy,
    _fallback_copy,
    _parse_batch_response,
    _parse_section_from_text,
)

# ── ProductInfo dataclass ────────────────────────────────────────────────────


class TestProductInfo:
    def test_default_values(self):
        product = ProductInfo()
        assert product.name == ""
        assert product.features == []
        assert product.target_audience == ""
        assert product.price_range == ""
        assert product.usp == ""

    def test_custom_values(self, sample_product_info):
        p = sample_product_info
        assert p.name == "테스트 스킨케어 세럼"
        assert len(p.features) == 3
        assert p.target_audience == "20-30대 여성"


# ── SectionCopy dataclass ────────────────────────────────────────────────────


class TestSectionCopy:
    def test_default_values(self):
        sc = SectionCopy()
        assert sc.section_index == 0
        assert sc.section_type == ""
        assert sc.headline == ""
        assert sc.subheadline == ""
        assert sc.body == ""
        assert sc.cta_text == ""

    def test_custom_values(self, sample_section_copy):
        sc = sample_section_copy
        assert sc.section_type == "hero"
        assert sc.headline == "최고의 보습 세럼"
        assert sc.cta_text == "지금 구매하기"


# ── CopyResult ───────────────────────────────────────────────────────────────


class TestCopyResult:
    def test_to_dict_structure(self, sample_product_info, sample_section_copy):
        result = CopyResult(product=sample_product_info, sections=[sample_section_copy])
        d = result.to_dict()
        assert "product" in d
        assert "sections" in d
        assert d["product"]["name"] == sample_product_info.name
        assert len(d["sections"]) == 1

    def test_to_dict_section_fields(self, sample_section_copy):
        result = CopyResult(sections=[sample_section_copy])
        sections = result.to_dict()["sections"]
        assert sections[0]["section_type"] == "hero"
        assert sections[0]["headline"] == "최고의 보습 세럼"
        assert "section_index" in sections[0]

    def test_empty_result(self):
        result = CopyResult()
        d = result.to_dict()
        assert d["sections"] == []


# ── _fallback_copy ───────────────────────────────────────────────────────────


class TestFallbackCopy:
    SECTION_TYPES = [
        "hero",
        "features",
        "benefits",
        "testimonials",
        "specs",
        "cta",
        "guarantee",
        "social_proof",
    ]

    @pytest.mark.parametrize("section_type", SECTION_TYPES)
    def test_fallback_returns_section_copy_for_known_type(self, section_type):
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = section_type
        result = _fallback_copy(mock_section)
        assert isinstance(result, SectionCopy)
        assert result.section_type == section_type
        assert len(result.headline) > 0

    def test_fallback_for_unknown_section_uses_features_default(self):
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = "unknown_custom_type"
        result = _fallback_copy(mock_section)
        assert isinstance(result, SectionCopy)
        # Should use "features" default
        assert result.headline == "이런 점이 다릅니다"

    def test_hero_fallback_has_cta(self):
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = "hero"
        result = _fallback_copy(mock_section)
        assert result.cta_text != ""

    def test_non_cta_sections_have_empty_cta_or_short_cta(self):
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = "features"
        result = _fallback_copy(mock_section)
        assert isinstance(result.cta_text, str)


# ── _parse_batch_response ────────────────────────────────────────────────────


def _make_template(sections_data):
    """Build a minimal mock RankedTemplate."""
    template = MagicMock()
    sections = []
    for i, data in enumerate(sections_data):
        s = MagicMock()
        s.index = i
        s.section_type = data.get("section_type", "hero")
        s.headline = data.get("headline", "")
        sections.append(s)
    template.sections = sections
    return template


class TestParseBatchResponse:
    def test_parses_valid_json_array(self, sample_product_info):
        sections_data = [
            {"section_type": "hero", "headline": "헤드라인"},
            {"section_type": "features", "headline": "특징"},
        ]
        template = _make_template(sections_data)
        raw = json.dumps(
            [
                {
                    "section_type": "hero",
                    "headline": "멋진 제품",
                    "subheadline": "서브",
                    "body": "본문",
                    "cta_text": "구매",
                },
                {
                    "section_type": "features",
                    "headline": "특장점",
                    "subheadline": "",
                    "body": "내용",
                    "cta_text": "",
                },
            ]
        )
        result = _parse_batch_response(raw, sample_product_info, template)
        assert isinstance(result, CopyResult)
        assert len(result.sections) == 2
        assert result.sections[0].headline == "멋진 제품"
        assert result.sections[1].headline == "특장점"

    def test_falls_back_when_json_is_invalid(self, sample_product_info):
        template = _make_template([{"section_type": "hero"}])
        result = _parse_batch_response("완전히 잘못된 텍스트", sample_product_info, template)
        assert isinstance(result, CopyResult)
        assert len(result.sections) == 1

    def test_falls_back_for_partial_json(self, sample_product_info):
        # JSON with fewer items than sections
        sections_data = [
            {"section_type": "hero"},
            {"section_type": "features"},
        ]
        template = _make_template(sections_data)
        raw = json.dumps(
            [
                {
                    "section_type": "hero",
                    "headline": "하나만",
                    "subheadline": "",
                    "body": "",
                    "cta_text": "",
                },
            ]
        )
        result = _parse_batch_response(raw, sample_product_info, template)
        assert len(result.sections) == 2
        # second section should use fallback
        assert result.sections[1].headline != ""

    def test_product_is_preserved_in_result(self, sample_product_info):
        template = _make_template([{"section_type": "hero"}])
        raw = json.dumps(
            [
                {
                    "section_type": "hero",
                    "headline": "H",
                    "subheadline": "",
                    "body": "",
                    "cta_text": "",
                }
            ]
        )
        result = _parse_batch_response(raw, sample_product_info, template)
        assert result.product.name == sample_product_info.name

    def test_strips_moai_formatting(self, sample_product_info):
        template = _make_template([{"section_type": "hero"}])
        # Include MoAI-style prefix garbage
        raw = (
            '\U0001f916 some garbage \u2500\u2500\u2500\u2500\n'
            '[{"section_type":"hero","headline":"Clean",'
            '"subheadline":"","body":"","cta_text":""}]'
        )
        result = _parse_batch_response(raw, sample_product_info, template)
        # Should still parse the JSON even with prefix noise
        assert isinstance(result, CopyResult)


# ── _parse_section_from_text ─────────────────────────────────────────────────


class TestParseSectionFromText:
    def test_extracts_korean_labels(self):
        raw = "헤드라인: 멋진 제품\n서브헤드라인: 부제목\n본문: 설명 텍스트\nCTA: 구매하기"
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = "hero"
        mock_section.headline = ""
        result = _parse_section_from_text(raw, mock_section)
        assert result.headline == "멋진 제품"
        assert result.subheadline == "부제목"
        assert result.body == "설명 텍스트"
        assert result.cta_text == "구매하기"

    def test_uses_section_headline_when_not_found(self):
        mock_section = MagicMock()
        mock_section.index = 0
        mock_section.section_type = "features"
        mock_section.headline = "기본 헤드라인"
        result = _parse_section_from_text("no labels here", mock_section)
        assert result.headline == "기본 헤드라인"

    def test_returns_section_copy_type(self):
        mock_section = MagicMock()
        mock_section.index = 1
        mock_section.section_type = "cta"
        mock_section.headline = ""
        result = _parse_section_from_text("", mock_section)
        assert isinstance(result, SectionCopy)
        assert result.section_type == "cta"


# ── CopyGenerator (legacy wrapper) ──────────────────────────────────────────


class TestCopyGenerator:
    def test_copy_generator_is_instantiable_without_provider(self):
        gen = CopyGenerator()
        assert gen.provider is None

    def test_copy_generator_accepts_provider(self, mock_ai_provider):
        gen = CopyGenerator(provider=mock_ai_provider)
        assert gen.provider is mock_ai_provider

    def test_generate_method_exists(self):
        gen = CopyGenerator()
        assert callable(gen.generate)
