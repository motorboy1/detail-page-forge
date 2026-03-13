"""Quality checklist — automated 20-item validation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckItem:
    """A single quality check item."""
    category: str = ""
    name: str = ""
    description: str = ""
    passed: bool = False
    score: int = 0  # 0-10
    notes: str = ""


@dataclass
class QualityReport:
    """Complete quality report."""
    items: list[CheckItem] = field(default_factory=list)
    total_score: int = 0
    max_score: int = 0
    pass_rate: float = 0.0
    recommendation: str = ""


CHECKLIST_ITEMS = [
    # 1. Planning & Strategy
    ("기획/전략", "타겟 고객 명확성", "상세페이지가 특정 타겟 고객에게 명확하게 소구하는가"),
    ("기획/전략", "핵심 메시지 전달", "상품의 USP가 명확하게 전달되는가"),
    ("기획/전략", "경쟁 우위 부각", "경쟁사 대비 차별점이 잘 드러나는가"),
    ("기획/전략", "구매 전환 유도", "설득하는 논리적 흐름이 있는가"),
    # 2. Copywriting
    ("카피라이팅", "명확성/간결성", "문장이 쉽고 간결한가"),
    ("카피라이팅", "설득력", "고객 문제를 공감하고 해결책을 제시하는가"),
    ("카피라이팅", "감성적 소구", "긍정적 경험을 상상하게 하는가"),
    ("카피라이팅", "오타/비문", "문법 오류 없이 깔끔한가"),
    ("카피라이팅", "AI 카피 자연스러움", "AI 생성 카피가 어색하지 않은가"),
    # 3. Design & Visual
    ("디자인", "브랜드 일관성", "전체적인 톤앤매너가 일치하는가"),
    ("디자인", "가독성", "텍스트와 배경 대비가 적절한가"),
    ("디자인", "시각적 계층", "중요 정보가 시각적으로 강조되는가"),
    ("디자인", "이미지 품질", "모든 이미지 해상도가 높고 선명한가"),
    ("디자인", "제품 사진 현실성", "합성이 자연스러운가"),
    ("디자인", "모바일 최적화", "모바일에서 잘 보이는가"),
    # 4. Technical & UX
    ("기술/UX", "로딩 속도", "이미지 용량이 적절한가"),
    ("기술/UX", "CTA 명확성", "구매 버튼이 눈에 띄는가"),
    ("기술/UX", "정보 정확성", "상품 정보가 정확한가"),
    # 5. Overall
    ("종합", "전체 만족도", "전반적으로 1등 상세페이지 수준인가"),
    ("종합", "컨닝 전략 적용", "경쟁사 벤치마킹이 효과적으로 적용되었는가"),
]


class QualityChecker:
    """Run automated quality checks on the generated detail page."""

    def check(
        self,
        sections_count: int,
        has_hero: bool,
        has_cta: bool,
        images_count: int,
        avg_image_size_kb: float,
        has_product_photo: bool,
        copy_sections: list[dict] | None = None,
    ) -> QualityReport:
        """Run all quality checks and return a report."""
        items: list[CheckItem] = []

        for category, name, description in CHECKLIST_ITEMS:
            item = CheckItem(category=category, name=name, description=description)

            # Auto-check what we can
            if name == "로딩 속도":
                item.passed = avg_image_size_kb < 500
                item.score = 10 if avg_image_size_kb < 300 else (7 if avg_image_size_kb < 500 else 3)
                item.notes = f"평균 이미지 크기: {avg_image_size_kb:.0f}KB"
            elif name == "이미지 품질":
                item.passed = images_count >= sections_count
                item.score = 10 if images_count >= sections_count else 5
                item.notes = f"이미지 {images_count}개 / 섹션 {sections_count}개"
            elif name == "제품 사진 현실성":
                item.passed = has_product_photo
                item.score = 8 if has_product_photo else 3
            elif name == "CTA 명확성":
                item.passed = has_cta
                item.score = 10 if has_cta else 2
            elif name == "핵심 메시지 전달":
                item.passed = has_hero
                item.score = 10 if has_hero else 3
            else:
                # Default pass for items needing human review
                item.passed = True
                item.score = 7
                item.notes = "자동 검증 대상 아님 (기본 통과)"

            items.append(item)

        total = sum(i.score for i in items)
        max_score = len(items) * 10
        pass_rate = sum(1 for i in items if i.passed) / len(items) if items else 0

        recommendation = "우수" if pass_rate >= 0.9 else ("양호" if pass_rate >= 0.7 else "개선 필요")

        return QualityReport(
            items=items,
            total_score=total,
            max_score=max_score,
            pass_rate=pass_rate,
            recommendation=recommendation,
        )
