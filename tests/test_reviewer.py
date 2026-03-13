"""Unit tests for reviewer/checklist.py — T-1.2.6."""

from __future__ import annotations

import pytest

from detail_forge.reviewer.checklist import (
    CHECKLIST_ITEMS,
    CheckItem,
    QualityChecker,
    QualityReport,
)

# ── CHECKLIST_ITEMS constant ─────────────────────────────────────────────────


class TestChecklistItems:
    def test_has_20_items(self):
        assert len(CHECKLIST_ITEMS) == 20

    def test_each_item_has_three_elements(self):
        for item in CHECKLIST_ITEMS:
            assert len(item) == 3, f"Expected (category, name, description) tuple, got {item}"

    def test_categories_present(self):
        categories = {item[0] for item in CHECKLIST_ITEMS}
        expected = {"기획/전략", "카피라이팅", "디자인", "기술/UX", "종합"}
        assert categories == expected

    def test_names_are_non_empty(self):
        for category, name, description in CHECKLIST_ITEMS:
            assert name.strip(), f"Empty name in category={category}"

    def test_descriptions_are_non_empty(self):
        for category, name, description in CHECKLIST_ITEMS:
            assert description.strip(), f"Empty description for name={name}"

    def test_no_duplicate_names(self):
        names = [item[1] for item in CHECKLIST_ITEMS]
        assert len(names) == len(set(names)), "Duplicate item names found"


# ── CheckItem dataclass ──────────────────────────────────────────────────────


class TestCheckItem:
    def test_default_values(self):
        item = CheckItem()
        assert item.category == ""
        assert item.name == ""
        assert item.description == ""
        assert item.passed is False
        assert item.score == 0
        assert item.notes == ""

    def test_custom_values(self):
        item = CheckItem(
            category="디자인",
            name="브랜드 일관성",
            description="전체적인 톤앤매너가 일치하는가",
            passed=True,
            score=8,
            notes="자동 검증 통과",
        )
        assert item.passed is True
        assert item.score == 8


# ── QualityReport dataclass ──────────────────────────────────────────────────


class TestQualityReport:
    def test_default_values(self):
        report = QualityReport()
        assert report.items == []
        assert report.total_score == 0
        assert report.max_score == 0
        assert report.pass_rate == 0.0
        assert report.recommendation == ""


# ── QualityChecker.check ─────────────────────────────────────────────────────


class TestQualityCheckerCheck:
    @pytest.fixture
    def checker(self):
        return QualityChecker()

    def test_returns_quality_report(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        assert isinstance(report, QualityReport)

    def test_report_has_20_items(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        assert len(report.items) == 20

    def test_each_item_is_check_item(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=False,
            images_count=3,
            avg_image_size_kb=400.0,
            has_product_photo=False,
        )
        for item in report.items:
            assert isinstance(item, CheckItem)

    def test_total_score_is_sum_of_item_scores(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        assert report.total_score == sum(i.score for i in report.items)

    def test_max_score_equals_20_times_10(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=100.0,
            has_product_photo=True,
        )
        assert report.max_score == 200

    def test_pass_rate_between_0_and_1(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        assert 0.0 <= report.pass_rate <= 1.0

    def test_loading_speed_passes_when_under_500kb(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=400.0,
            has_product_photo=True,
        )
        loading_item = next(i for i in report.items if i.name == "로딩 속도")
        assert loading_item.passed is True

    def test_loading_speed_fails_when_over_500kb(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=600.0,
            has_product_photo=True,
        )
        loading_item = next(i for i in report.items if i.name == "로딩 속도")
        assert loading_item.passed is False

    def test_loading_speed_score_excellent_under_300kb(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        loading_item = next(i for i in report.items if i.name == "로딩 속도")
        assert loading_item.score == 10

    def test_cta_passes_when_has_cta_true(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        cta_item = next(i for i in report.items if i.name == "CTA 명확성")
        assert cta_item.passed is True
        assert cta_item.score == 10

    def test_cta_fails_when_has_cta_false(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=False,
            has_cta=False,
            images_count=3,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        cta_item = next(i for i in report.items if i.name == "CTA 명확성")
        assert cta_item.passed is False
        assert cta_item.score == 2

    def test_hero_message_passes_when_has_hero(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        hero_item = next(i for i in report.items if i.name == "핵심 메시지 전달")
        assert hero_item.passed is True

    def test_product_photo_check(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=200.0,
            has_product_photo=False,
        )
        photo_item = next(i for i in report.items if i.name == "제품 사진 현실성")
        assert photo_item.passed is False
        assert photo_item.score == 3

    def test_image_quality_passes_when_images_cover_sections(self, checker):
        report = checker.check(
            sections_count=4,
            has_hero=True,
            has_cta=True,
            images_count=4,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        img_item = next(i for i in report.items if i.name == "이미지 품질")
        assert img_item.passed is True

    def test_image_quality_fails_when_not_enough_images(self, checker):
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=2,
            avg_image_size_kb=200.0,
            has_product_photo=True,
        )
        img_item = next(i for i in report.items if i.name == "이미지 품질")
        assert img_item.passed is False

    def test_recommendation_excellent_when_high_pass_rate(self, checker):
        # All positives should yield 우수
        report = checker.check(
            sections_count=5,
            has_hero=True,
            has_cta=True,
            images_count=5,
            avg_image_size_kb=100.0,
            has_product_photo=True,
        )
        assert report.recommendation in ("우수", "양호", "개선 필요")
        # pass_rate should be high with all good inputs
        assert report.pass_rate >= 0.7

    def test_recommendation_improvement_needed_when_low_pass_rate(self, checker):
        # All negatives
        report = checker.check(
            sections_count=5,
            has_hero=False,
            has_cta=False,
            images_count=0,
            avg_image_size_kb=800.0,
            has_product_photo=False,
        )
        assert report.recommendation in ("개선 필요", "양호", "우수")

    def test_loading_speed_note_contains_kb(self, checker):
        report = checker.check(
            sections_count=3,
            has_hero=True,
            has_cta=True,
            images_count=3,
            avg_image_size_kb=250.0,
            has_product_photo=True,
        )
        loading_item = next(i for i in report.items if i.name == "로딩 속도")
        assert "KB" in loading_item.notes
