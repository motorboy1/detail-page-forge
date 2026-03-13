"""AI copywriting generator — Phase 2 core engine (batch mode)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from detail_forge.analyzer.parser import Section
from detail_forge.analyzer.ranker import RankedTemplate
from detail_forge.designer.d1000_principles import (
    get_custom_prompt,
    get_enriched_prompt,
    get_section_prompt,
    get_system_prompt_compact,
)


@dataclass
class ProductInfo:
    """User's product information."""
    name: str = ""
    features: list[str] = field(default_factory=list)
    target_audience: str = ""
    price_range: str = ""
    usp: str = ""  # Unique Selling Proposition


@dataclass
class SectionCopy:
    """Generated copy for a single section."""
    section_index: int = 0
    section_type: str = ""
    headline: str = ""
    subheadline: str = ""
    body: str = ""
    cta_text: str = ""
    original_competitor_copy: str = ""


@dataclass
class CopyResult:
    """Complete copywriting result for all sections."""
    product: ProductInfo = field(default_factory=ProductInfo)
    sections: list[SectionCopy] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "product": {
                "name": self.product.name,
                "features": self.product.features,
                "target_audience": self.product.target_audience,
                "price_range": self.product.price_range,
                "usp": self.product.usp,
            },
            "sections": [
                {
                    "section_index": s.section_index,
                    "section_type": s.section_type,
                    "headline": s.headline,
                    "subheadline": s.subheadline,
                    "body": s.body,
                    "cta_text": s.cta_text,
                }
                for s in self.sections
            ],
        }


def generate_all_copy(
    product: ProductInfo,
    template: RankedTemplate,
    selected_principles: list[int] | None = None,
) -> CopyResult:
    """Generate copy for ALL sections in a single Claude CLI call.

    Args:
        product: Product information
        template: Ranked template with sections
        selected_principles: Optional list of D1000 principle IDs to apply.
            If provided, generates a custom design prompt from selected principles.
            If None, uses the default compact system prompt.
    """
    from detail_forge.providers.claude import _call_claude

    section_list = "\n".join(
        f"{i+1}. {s.section_type}" for i, s in enumerate(template.sections)
    )
    features_text = "\n".join(f"- {f}" for f in product.features)

    # D1000 design principles — enriched with PDF knowledge or default
    if selected_principles:
        d1000_guide = get_enriched_prompt(selected_principles, detail_level="medium")
    else:
        d1000_guide = get_system_prompt_compact()

    prompt = f"""당신은 이커머스 상세페이지 전문 카피라이터이자 비주얼 디렉터입니다.
한국 네이버 스마트스토어와 쿠팡에서 잘 팔리는 상세페이지 카피를 작성합니다.

{d1000_guide}

위 디자인 원리를 참고하여, 각 섹션의 카피가 디자인과 어울리도록 작성하세요.
특히 headline은 시각적 임팩트를, body는 설득력을 극대화하세요.

상품명: {product.name}
상품 특징:
{features_text}

아래 {len(template.sections)}개 섹션의 카피를 한번에 작성해 주세요:
{section_list}

JSON 배열로만 응답하세요. 다른 텍스트, 마크다운, 설명 없이 순수 JSON만:
[
  {{"section_type": "hero", "headline": "...", "subheadline": "...", "body": "...", "cta_text": "...", "design_note": "적용할 D1000 원리 키워드"}},
  ...
]

규칙:
- headline: 강렬한 한 줄 (15자 이내)
- subheadline: 보조 설명 (30자 이내)
- body: 설득력 있는 2-3문장
- cta_text: 행동 유도 문구 (hero, cta 섹션만, 나머지는 빈 문자열)
- ** 없이 플레인 텍스트만
- 반드시 JSON 배열만 출력"""

    raw = _call_claude(prompt, max_tokens=4096)

    return _parse_batch_response(raw, product, template)


def _parse_batch_response(
    raw: str, product: ProductInfo, template: RankedTemplate
) -> CopyResult:
    """Parse batch JSON response from Claude."""
    # Strip MoAI formatting
    clean = re.sub(r'\U0001f916.*?\u2500+', '', raw, flags=re.DOTALL).strip()
    if not clean:
        clean = raw

    # Extract JSON array
    start = clean.find("[")
    end = clean.rfind("]") + 1

    result = CopyResult(product=product)

    if start >= 0 and end > start:
        try:
            items = json.loads(clean[start:end])
            for i, section in enumerate(template.sections):
                if i < len(items):
                    item = items[i]
                    result.sections.append(SectionCopy(
                        section_index=section.index,
                        section_type=section.section_type,
                        headline=item.get("headline", section.headline or f"섹션 {i+1}"),
                        subheadline=item.get("subheadline", ""),
                        body=item.get("body", ""),
                        cta_text=item.get("cta_text", ""),
                    ))
                else:
                    result.sections.append(_fallback_copy(section))
            return result
        except json.JSONDecodeError:
            pass

    # Fallback: try parsing as individual labeled sections
    for section in template.sections:
        result.sections.append(_parse_section_from_text(raw, section))

    return result


def _parse_section_from_text(raw: str, section: Section) -> SectionCopy:
    """Fallback: extract copy from unstructured text."""
    label_re = re.compile(
        r"^\*{0,2}(헤드라인|서브헤드라인|본문|CTA)\s*[:：]\*{0,2}\s*(.+)",
        re.IGNORECASE | re.MULTILINE,
    )
    headline = subheadline = body = cta = ""
    for m in label_re.finditer(raw):
        label, value = m.group(1), m.group(2).strip()
        if label == "헤드라인" and not headline:
            headline = value
        elif label == "서브헤드라인" and not subheadline:
            subheadline = value
        elif label == "본문" and not body:
            body = value
        elif label == "CTA" and not cta:
            cta = value

    return SectionCopy(
        section_index=section.index,
        section_type=section.section_type,
        headline=headline or section.headline or f"{section.section_type} 섹션",
        subheadline=subheadline or "",
        body=body or "",
        cta_text=cta or "",
    )


def _fallback_copy(section: Section) -> SectionCopy:
    """Generate minimal fallback copy."""
    defaults = {
        "hero": ("최고의 선택", "당신을 위한 프리미엄", "지금 바로 경험해보세요.", "자세히 보기"),
        "features": ("이런 점이 다릅니다", "핵심 특징을 확인하세요", "차별화된 품질과 기능으로 만족을 드립니다.", ""),
        "benefits": ("왜 선택해야 할까요?", "확실한 이유가 있습니다", "고객님의 일상을 더 편리하게 만들어 드립니다.", ""),
        "testimonials": ("실제 고객 후기", "직접 사용해본 분들의 이야기", "많은 분들이 만족하고 계십니다.", ""),
        "specs": ("상세 스펙", "꼼꼼하게 확인하세요", "최고급 소재와 정밀한 제조 공정으로 만들었습니다.", ""),
        "cta": ("지금이 기회입니다", "한정 수량 특별가", "오늘 주문하시면 특별 혜택을 드립니다.", "지금 구매하기"),
        "guarantee": ("안심하고 구매하세요", "100% 만족 보증", "교환, 환불, 무료 배송 모두 지원합니다.", ""),
        "social_proof": ("이미 많은 분들이 선택했습니다", "숫자가 증명합니다", "높은 재구매율이 품질을 말해줍니다.", ""),
    }
    h, s, b, c = defaults.get(section.section_type, defaults["features"])
    return SectionCopy(
        section_index=section.index,
        section_type=section.section_type,
        headline=h, subheadline=s, body=b, cta_text=c,
    )


# Keep backward compatibility
class CopyGenerator:
    """Legacy wrapper — use generate_all_copy() directly."""

    def __init__(self, provider=None) -> None:
        self.provider = provider

    async def generate(
        self, product: ProductInfo, template: RankedTemplate
    ) -> CopyResult:
        return generate_all_copy(product, template)
