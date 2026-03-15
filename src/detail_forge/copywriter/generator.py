"""AI copywriting generator — Phase 2 core engine (batch mode).

Supports two modes:
  1. Template-based: generate_all_copy() — copy from competitor template sections
  2. Technique-based: generate_technique_copy() — copy directed by TechniqueResult
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from detail_forge.analyzer.parser import Section
from detail_forge.analyzer.ranker import RankedTemplate
from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge
from detail_forge.designer.d1000_principles import (
    get_enriched_prompt,
    get_system_prompt_compact,
)

if TYPE_CHECKING:
    from detail_forge.technique_engine.engine import TechniqueResult


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
    lecture_insights: bool = True,
) -> CopyResult:
    """Generate copy for ALL sections in a single Claude CLI call.

    Args:
        product: Product information
        template: Ranked template with sections
        selected_principles: Optional list of D1000 principle IDs to apply.
            If provided, generates a custom design prompt from selected principles.
            If None, uses the default compact system prompt.
        lecture_insights: If True, inject lecture-derived reasoning prompts.
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

    # Lecture-derived practical insights
    lecture_block = ""
    if lecture_insights:
        kb = LectureKnowledge()
        target_pids = selected_principles or list(range(1, 51))
        prompts = kb.get_reasoning_prompts(target_pids)
        if prompts:
            lecture_block = "\n\n[강의 실전 노하우]\n" + "\n".join(f"- {p}" for p in prompts[:5])

    prompt = f"""당신은 이커머스 상세페이지 전문 카피라이터이자 비주얼 디렉터입니다.
한국 네이버 스마트스토어와 쿠팡에서 잘 팔리는 상세페이지 카피를 작성합니다.

{d1000_guide}

위 디자인 원리를 참고하여, 각 섹션의 카피가 디자인과 어울리도록 작성하세요.
{lecture_block}
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


# ─── Technique-Aware Copy Generation ──────────────────────────────


# Maps narrative atom IDs to Korean copy directives
_NARRATIVE_ATOM_DIRECTIVES: dict[str, str] = {
    "narrative_purple_cow": "제품 카테고리가 아닌 '무엇이 다른가'를 강조하세요. 첫 문장에서 차별점을 바로 보여주세요.",
    "narrative_storytelling": "스펙 나열 대신 탄생 배경→제작 과정→고객 경험 순서의 스토리로 전개하세요.",
    "narrative_world_building": "제품 단독이 아닌, 사용자 라이프스타일 맥락 안에서 제품을 묘사하세요.",
    "narrative_soulmate_persona": "타겟 고객의 구체적인 상황/고민을 담아, '이건 바로 나를 위한 것'이라고 느끼게 하세요.",
    "narrative_fan_conversion": "'구매하기' 대신 '참여/합류/응원'으로 프레이밍하세요. 거래가 아닌 관계입니다.",
    "narrative_four_stage_flywheel": "카피 자체가 공유하고 싶은 콘텐츠가 되도록 작성하세요.",
    "narrative_risk_scaling": "제품의 진화/개선 과정을 보여주어 품질 향상 스토리를 전달하세요.",
}

# Maps compound IDs to section-level copy tone directives
_COMPOUND_COPY_TONE: dict[str, str] = {
    "compound_cinematic_hero": "영화 오프닝처럼 임팩트 있는 한 줄. 호기심과 기대감을 즉시 점화하세요.",
    "compound_premium_product_showcase": "럭셔리 브랜드처럼 간결하고 권위 있는 톤. 군더더기 없이 핵심만.",
    "compound_storytelling_flow": "따뜻한 내러티브 톤. 창업자/브랜드의 진정성 있는 이야기를 전달하세요.",
    "compound_lifestyle_context": "일상 속 장면을 묘사하듯 감각적으로. 사용자가 장면을 상상할 수 있게.",
    "compound_evidence_trust": "수치와 데이터로 뒷받침하는 객관적 톤. Before/After, 인증, 실험 결과를 활용.",
    "compound_social_proof": "실제 후기/커뮤니티 느낌. '저도 처음엔 반신반의...' 같은 공감 화법.",
    "compound_cta_urgency": "부드러운 긴급성. 강압적이지 않으면서도 지금 행동해야 할 이유를 제시.",
    "compound_conversion_engine": "차별화 포인트를 즉시 각인시키는 카피. 왜 이것이어야 하는지 단번에.",
    "compound_technical_authority": "전문가 톤. 기술 스펙을 소비자 언어로 번역하되 전문성을 유지.",
    "compound_spec_detail": "세부 사양을 흥미롭게. 단순 나열 대신 각 스펙이 주는 실질적 혜택을 연결.",
    "compound_minimal_elegant": "절제된 우아함. 한 문장으로 여운을 남기세요. 말하지 않는 것이 더 많은 것을 말합니다.",
    "compound_dynamic_multi_product": "각 제품/라인업의 개성을 짧고 강하게. 비교가 아닌 다양성을 강조.",
    "compound_depth_immersion": "몰입감 있는 감각적 묘사. 질감, 온도, 무게감을 느끼게 하세요.",
    "compound_texture_richness": "촉각적 표현. '부드러운', '매끄러운', '탄탄한' 같은 감각어를 적극 활용.",
    "compound_playful_chaos": "캐주얼하고 위트 있는 톤. 정형화된 광고 문구 대신 친구에게 추천하듯.",
    "compound_food_sensory": "미각/후각/시각을 자극하는 묘사. 맛과 향이 느껴지는 생생한 카피.",
    "compound_editorial_hero": "매거진 표지처럼 세련된 한 줄. 에디토리얼 감성의 절제된 문체.",
    "compound_interactive_storytelling": "사용자 참여를 유도하는 톤. '당신이라면?', '직접 확인해보세요'.",
}

# Maps mood tags to overall tone keywords
_MOOD_TONE_MAP: dict[str, str] = {
    "luxury": "고급스러운", "premium": "프리미엄", "elegant": "우아한",
    "minimal": "절제된", "clean": "깔끔한", "modern": "모던한",
    "warm": "따뜻한", "authentic": "진정성 있는", "narrative": "이야기체",
    "bold": "대담한", "dynamic": "역동적", "dramatic": "드라마틱한",
    "cinematic": "시네마틱한", "immersive": "몰입감 있는",
    "playful": "발랄한", "youthful": "젊은", "energetic": "에너지 넘치는",
    "professional": "전문적인", "technical": "기술적인", "trustworthy": "신뢰감 있는",
    "persuasive": "설득력 있는", "communal": "커뮤니티 느낌의",
    "tactile": "촉각적인", "artistic": "예술적인",
}


def build_technique_copy_directives(technique_result: TechniqueResult) -> str:
    """Build copy generation directives from TechniqueResult.

    Converts technique engine output into structured Korean copy instructions
    for each section. Used as input to Claude prompt or fallback generator.

    Returns:
        Multi-line string with per-section copy directives.
    """
    lines: list[str] = []

    # Overall tone from mood profile
    mood_tones = [
        _MOOD_TONE_MAP[m]
        for m in technique_result.mood_profile[:5]
        if m in _MOOD_TONE_MAP
    ]
    if mood_tones:
        lines.append(f"[전체 톤] {', '.join(mood_tones)} 느낌으로 통일하세요.")
    lines.append("")

    # Per-section directives
    for section in technique_result.section_techniques:
        lines.append(f"[섹션 {section.section_order}: {section.section_type}]")
        lines.append(f"역할: {section.role}")

        # Compound-level tone directive
        tone = _COMPOUND_COPY_TONE.get(section.compound.id)
        if tone:
            lines.append(f"톤: {tone}")

        # Narrative atom directives (specific copywriting techniques)
        for atom in section.atoms:
            directive = _NARRATIVE_ATOM_DIRECTIVES.get(atom.id)
            if directive:
                lines.append(f"기법: {directive}")

        lines.append("")

    return "\n".join(lines)


def generate_technique_copy(
    product: ProductInfo,
    technique_result: TechniqueResult,
    lecture_insights: bool = True,
) -> CopyResult:
    """Generate copy directed by TechniqueResult.

    Each section gets copy instructions derived from the workflow's compound
    patterns and narrative atoms. Falls back to deterministic copy if Claude
    is unavailable.

    Args:
        product: Product information.
        technique_result: TechniqueResult from TechniqueEngine.select().
        lecture_insights: If True, inject lecture-derived reasoning prompts.

    Returns:
        CopyResult with per-section copy.
    """
    try:
        from detail_forge.providers.claude import _call_claude
    except Exception:
        # Claude provider unavailable — use deterministic fallback
        return _technique_fallback_copy(product, technique_result)

    features_text = "\n".join(f"- {f}" for f in product.features)
    directives = build_technique_copy_directives(technique_result)

    # Section list with roles
    section_list = "\n".join(
        f"{s.section_order}. {s.section_type} — {s.role}"
        for s in technique_result.section_techniques
    )

    # Lecture insights
    lecture_block = ""
    if lecture_insights:
        kb = LectureKnowledge()
        prompts = kb.get_reasoning_prompts(list(range(1, 51)))
        if prompts:
            lecture_block = "\n\n[강의 실전 노하우]\n" + "\n".join(
                f"- {p}" for p in prompts[:5]
            )

    prompt = f"""당신은 이커머스 상세페이지 전문 카피라이터이자 비주얼 디렉터입니다.
한국 네이버 스마트스토어와 쿠팡에서 잘 팔리는 상세페이지 카피를 작성합니다.

아래 기법 엔진이 결정한 디자인 전략에 맞는 카피를 작성하세요.

{directives}
{lecture_block}

상품명: {product.name}
상품 특징:
{features_text}
{f"타겟 고객: {product.target_audience}" if product.target_audience else ""}
{f"가격대: {product.price_range}" if product.price_range else ""}
{f"차별점: {product.usp}" if product.usp else ""}

아래 {len(technique_result.section_techniques)}개 섹션의 카피를 한번에 작성해 주세요:
{section_list}

JSON 배열로만 응답하세요. 다른 텍스트, 마크다운, 설명 없이 순수 JSON만:
[
  {{"section_type": "hero", "headline": "...", "subheadline": "...", "body": "...", "cta_text": "..."}},
  ...
]

규칙:
- headline: 강렬한 한 줄 (15자 이내). 각 섹션의 '톤' 지시를 반영할 것
- subheadline: 보조 설명 (30자 이내)
- body: 설득력 있는 2-3문장. 각 섹션의 '기법' 지시를 구체적으로 반영할 것
- cta_text: 행동 유도 문구 (hero, cta 섹션만, 나머지는 빈 문자열)
- ** 없이 플레인 텍스트만
- 반드시 JSON 배열만 출력"""

    try:
        raw = _call_claude(prompt, max_tokens=4096)
        return _parse_technique_response(raw, product, technique_result)
    except Exception:
        return _technique_fallback_copy(product, technique_result)


def _parse_technique_response(
    raw: str,
    product: ProductInfo,
    technique_result: TechniqueResult,
) -> CopyResult:
    """Parse Claude response for technique-based copy generation."""
    clean = re.sub(r'\U0001f916.*?\u2500+', '', raw, flags=re.DOTALL).strip()
    if not clean:
        clean = raw

    start = clean.find("[")
    end = clean.rfind("]") + 1

    result = CopyResult(product=product)
    sections = technique_result.section_techniques

    if start >= 0 and end > start:
        try:
            items = json.loads(clean[start:end])
            for i, section in enumerate(sections):
                if i < len(items):
                    item = items[i]
                    result.sections.append(SectionCopy(
                        section_index=section.section_order,
                        section_type=section.section_type,
                        headline=item.get("headline", f"섹션 {section.section_order}"),
                        subheadline=item.get("subheadline", ""),
                        body=item.get("body", ""),
                        cta_text=item.get("cta_text", ""),
                    ))
                else:
                    result.sections.append(
                        _technique_section_fallback(product, section)
                    )
            return result
        except json.JSONDecodeError:
            pass

    # Full fallback
    return _technique_fallback_copy(product, technique_result)


# ─── Technique-Aware Deterministic Fallback ───────────────────────

# Section-type-specific fallback templates keyed by compound mood
_TECHNIQUE_FALLBACK_TEMPLATES: dict[str, dict[str, tuple[str, str, str, str]]] = {
    "hero": {
        "luxury": ("{name}", "프리미엄의 새로운 기준", "{features_first} — 당신이 찾던 바로 그것, {name}이 일상을 바꿉니다.", "자세히 보기"),
        "warm": ("{name}", "마음을 담은 정성", "{features_first}. 진심을 담아 만든 {name}, 따뜻한 하루의 시작.", "지금 만나기"),
        "bold": ("{name}", "다르니까 대담하게", "{features_first}. 평범함을 거부한 {name}, 지금 만나보세요.", "바로 보기"),
        "default": ("{name}", "새로운 기준을 제시합니다", "{features_first}. {name}과 함께하는 특별한 경험.", "자세히 보기"),
    },
    "story": {
        "default": ("이렇게 시작되었습니다", "{name}의 탄생 이야기", "'{features_first}'이라는 가치에서 출발했습니다. {name}은 '이것만은 다르게'라는 신념으로 만들어졌습니다.", ""),
    },
    "lifestyle": {
        "default": ("당신의 일상 속에서", "자연스럽게 스며드는 변화", "{features_first}. 매일의 루틴에 {name}을 더했을 뿐인데, 하루가 달라졌습니다.", ""),
    },
    "spec": {
        "default": ("이것이 기술력입니다", "핵심 스펙을 확인하세요", "{features_first} — 단순한 수치가 아닌, 체감할 수 있는 차이입니다.", ""),
    },
    "detail": {
        "default": ("디테일이 다릅니다", "하나하나 꼼꼼하게", "소재부터 마감까지, {name}의 모든 디테일에는 이유가 있습니다.", ""),
    },
    "proof": {
        "default": ("증거로 말합니다", "직접 확인하세요", "{features_first}. 말이 아닌 데이터로 증명합니다. {name}의 실력을 확인하세요.", ""),
    },
    "comparison": {
        "default": ("비교해 보세요", "차이는 분명합니다", "같은 카테고리, 다른 결과. {name}만의 차별점을 확인하세요.", ""),
    },
    "testimonial": {
        "default": ("실제 사용자의 이야기", "직접 써본 분들의 솔직한 후기", "처음엔 반신반의했지만, 써보니 확실히 다르더라고요.", ""),
    },
    "cta": {
        "luxury": ("지금이 기회입니다", "특별한 분을 위한 특별한 제안", "지금 {name}을 만나보세요. 후회 없는 선택이 될 것입니다.", "지금 구매하기"),
        "communal": ("함께해 주세요", "{name} 패밀리에 합류하세요", "구매가 아닌 참여입니다. {name}과 함께 시작하세요.", "합류하기"),
        "default": ("결정의 순간입니다", "지금 시작하세요", "더 이상 망설일 이유가 없습니다. {name}이 기다리고 있습니다.", "지금 구매하기"),
    },
}


def _technique_section_fallback(
    product: ProductInfo,
    section,
) -> SectionCopy:
    """Generate fallback copy for a single technique section."""
    section_type = section.section_type
    compound_moods = set(section.compound.mood) if hasattr(section, 'compound') else set()

    templates = _TECHNIQUE_FALLBACK_TEMPLATES.get(
        section_type,
        _TECHNIQUE_FALLBACK_TEMPLATES.get("proof", {}),
    )

    # Pick mood-matched template or default
    h, s, b, c = templates.get("default", ("", "", "", ""))
    for mood_key in ("luxury", "warm", "bold", "communal"):
        if mood_key in compound_moods and mood_key in templates:
            h, s, b, c = templates[mood_key]
            break

    features_first = product.features[0] if product.features else "핵심 기능"
    fmt = {"name": product.name or "제품", "features_first": features_first}
    return SectionCopy(
        section_index=section.section_order,
        section_type=section_type,
        headline=h.format_map(fmt),
        subheadline=s.format_map(fmt),
        body=b.format_map(fmt),
        cta_text=c.format_map(fmt),
    )


def _technique_fallback_copy(
    product: ProductInfo,
    technique_result: TechniqueResult,
) -> CopyResult:
    """Generate deterministic fallback copy for all technique sections."""
    result = CopyResult(product=product)
    for section in technique_result.section_techniques:
        result.sections.append(_technique_section_fallback(product, section))
    return result


# Keep backward compatibility
class CopyGenerator:
    """Legacy wrapper — use generate_all_copy() directly."""

    def __init__(self, provider=None) -> None:
        self.provider = provider

    async def generate(
        self, product: ProductInfo, template: RankedTemplate
    ) -> CopyResult:
        return generate_all_copy(product, template)
