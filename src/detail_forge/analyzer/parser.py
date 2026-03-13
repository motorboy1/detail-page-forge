"""Section parser — extract sections from competitor detail pages using AI vision."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from detail_forge.providers.base import AIProviderBase


@dataclass
class Section:
    """A section extracted from a competitor detail page."""
    index: int = 0
    section_type: str = ""  # hero, features, benefits, testimonials, specs, cta, guarantee
    headline: str = ""
    body_text: str = ""
    has_image: bool = False
    image_description: str = ""
    layout: str = ""  # full-width, split, grid, text-only
    strength_score: int = 0  # 1-10, how compelling this section is


@dataclass
class ParsedPage:
    """Parsed competitor page with extracted sections."""
    title: str = ""
    url: str = ""
    sections: list[Section] = field(default_factory=list)
    overall_score: int = 0


PARSE_PROMPT = """이 이미지는 이커머스 상세페이지(상품 상세 설명)입니다. 각 섹션을 분석해 주세요.

각 섹션에 대해 다음을 JSON 배열로 출력해 주세요:
[
  {
    "index": 1,
    "section_type": "hero|features|benefits|testimonials|specs|cta|guarantee|social_proof",
    "headline": "해당 섹션의 메인 텍스트",
    "body_text": "본문 텍스트 요약",
    "has_image": true/false,
    "image_description": "이미지 내용 설명",
    "layout": "full-width|split|grid|text-only",
    "strength_score": 1-10
  }
]

중요:
- 위에서 아래로 순서대로 분석
- 한국어로 작성
- JSON만 출력 (다른 텍스트 없이)"""


class SectionParser:
    """Parse competitor detail pages into structured sections using AI vision."""

    def __init__(self, provider: AIProviderBase) -> None:
        self.provider = provider

    async def parse(self, screenshot: bytes, title: str = "", url: str = "") -> ParsedPage:
        """Parse a detail page screenshot into sections."""
        raw = await self.provider.analyze_image(screenshot, PARSE_PROMPT)

        # Extract JSON from response
        sections = self._extract_sections(raw)

        page = ParsedPage(
            title=title,
            url=url,
            sections=sections,
            overall_score=sum(s.strength_score for s in sections) // max(len(sections), 1),
        )
        return page

    def _extract_sections(self, raw: str) -> list[Section]:
        """Extract Section objects from AI response."""
        # Find JSON array in response
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []

        try:
            data = json.loads(raw[start:end])
        except json.JSONDecodeError:
            return []

        sections: list[Section] = []
        for item in data:
            sections.append(
                Section(
                    index=item.get("index", 0),
                    section_type=item.get("section_type", ""),
                    headline=item.get("headline", ""),
                    body_text=item.get("body_text", ""),
                    has_image=item.get("has_image", False),
                    image_description=item.get("image_description", ""),
                    layout=item.get("layout", ""),
                    strength_score=item.get("strength_score", 0),
                )
            )
        return sections
