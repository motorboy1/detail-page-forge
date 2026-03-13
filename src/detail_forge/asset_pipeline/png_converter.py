"""PNG to HTML/CSS converter using Vision AI.

Converts Figma template PNGs to structured, slot-tagged HTML/CSS
via a pluggable AIProviderBase.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from detail_forge.providers.base import AIProviderBase
from detail_forge.templates.models import SlotMapping

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ContentArea:
    """A single content area within a layout section."""

    type: str           # headline | subheadline | body | cta | image | bg_image
    text: str = ""
    alt: str = ""
    style_hints: dict = field(default_factory=dict)


@dataclass
class LayoutSection:
    """Represents a visual section extracted from the PNG."""

    section_type: str                          # hero | features | benefits | cta | ...
    content_areas: list[dict]                  # raw dicts from AI response
    style_hints: dict = field(default_factory=dict)


@dataclass
class LayoutStructure:
    """Full layout extracted from a PNG."""

    sections: list[LayoutSection] = field(default_factory=list)
    global_style_hints: dict = field(default_factory=dict)


@dataclass
class ConversionResult:
    """Result of converting a PNG to HTML/CSS."""

    html: str
    css: str
    quality_score: float          # 0-10
    slot_mapping: SlotMapping

    @property
    def needs_curation(self) -> bool:
        """True when quality_score < 7 (manual curation required)."""
        return self.quality_score < 7


# ---------------------------------------------------------------------------
# Quality scorer (deterministic, no AI calls)
# ---------------------------------------------------------------------------

_LAYOUT_KEYWORDS = re.compile(
    r"\b(flex|grid|position|margin|padding|display)\b", re.IGNORECASE
)


def score_conversion_quality(
    *,
    html: str,
    css: str,
    slot_mapping: SlotMapping,
    slot_count: int,
) -> float:
    """Score an HTML/CSS conversion result on a 0-10 scale.

    Scoring dimensions (each up to 2.5 points):
    1. HTML validity  — has proper tags, non-empty content
    2. Slot coverage  — headline + subheadline + body + image slots
    3. CSS quality    — presence of layout-related rules
    4. Layout complexity preserved — section count, nesting depth

    Returns a float in [0.0, 10.0].  Result is fully deterministic.
    """
    score = 0.0

    # Dimension 1: HTML validity (0-2.5)
    html_lower = html.lower()
    html_len = len(html.strip())
    if html_len > 50 and "<" in html:
        score += 1.0
    if "<body" in html_lower or "<div" in html_lower or "<section" in html_lower:
        score += 0.75
    if "<h1" in html_lower or "<h2" in html_lower:
        score += 0.75

    # Dimension 2: Slot coverage (0-2.5)
    has_headline = slot_mapping.headline is not None
    has_sub = slot_mapping.subheadline is not None
    has_body = bool(slot_mapping.body)
    has_img = slot_mapping.product_image is not None or slot_mapping.background_image is not None
    filled = sum([has_headline, has_sub, has_body, has_img])
    score += filled * (2.5 / 4)

    # Dimension 3: CSS quality (0-2.5)
    css_len = len(css.strip())
    if css_len > 20:
        score += 1.0
    css_rule_count = css.count("{")
    if css_rule_count >= 1:
        score += 0.75
    if _LAYOUT_KEYWORDS.search(css):
        score += 0.75

    # Dimension 4: Layout complexity (0-2.5)
    if slot_count >= 3:
        score += 1.0
    section_count = html_lower.count("<section") + html_lower.count("<div")
    if section_count >= 2:
        score += 0.75
    if slot_count >= 5:
        score += 0.75

    return min(round(score, 2), 10.0)


# ---------------------------------------------------------------------------
# Vision AI layout prompt
# ---------------------------------------------------------------------------

_LAYOUT_PROMPT = """Analyze this design template image and extract its layout structure.
Return ONLY valid JSON with the following schema:
{
  "sections": [
    {
      "type": "hero|features|benefits|cta|testimonials|general",
      "content_areas": [
        {"type": "headline|subheadline|body|cta|image|bg_image",
         "text": "...", "alt": "...", "style_hints": {}}
      ]
    }
  ],
  "style_hints": {
    "color_scheme": "light|dark|colorful",
    "layout_type": "hero-centered|split|grid|...",
    "d1000_principles": [list of integer IDs]
  }
}
If there are no sections, return {"sections": [], "style_hints": {}}.
"""


# ---------------------------------------------------------------------------
# HTML/CSS generator
# ---------------------------------------------------------------------------

def _section_css_class(section_type: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", section_type.lower())


def _build_css_for_layout(layout: LayoutStructure) -> str:
    """Generate minimal semantic CSS from a LayoutStructure."""
    lines: list[str] = [
        "/* Generated by PngConverter */",
        "*, *::before, *::after { box-sizing: border-box; }",
        "body { margin: 0; font-family: sans-serif; }",
    ]
    for section in layout.sections:
        cls = _section_css_class(section.section_type)
        color = section.style_hints.get("color", "")
        rules = ["  padding: 40px 20px;"]
        if color:
            rules.append(f"  background-color: {color};")
        lines.append(f".section-{cls} {{")
        lines.extend(rules)
        lines.append("}")
    return "\n".join(lines)


def _build_html_for_layout(layout: LayoutStructure) -> str:
    """Generate semantic HTML from a LayoutStructure."""
    section_parts: list[str] = []
    for section in layout.sections:
        cls = _section_css_class(section.section_type)
        inner: list[str] = []
        for area in section.content_areas:
            atype = area.get("type", "body") if isinstance(area, dict) else area.type
            text = area.get("text", "") if isinstance(area, dict) else area.text
            alt = area.get("alt", "image") if isinstance(area, dict) else area.alt

            if atype == "headline":
                inner.append(f"  <h1>{text}</h1>")
            elif atype == "subheadline":
                inner.append(f"  <h2>{text}</h2>")
            elif atype == "body":
                inner.append(f"  <p>{text}</p>")
            elif atype == "cta":
                inner.append(f'  <button type="button">{text}</button>')
            elif atype in ("image", "img"):
                inner.append(f'  <img src="" alt="{alt}">')
            elif atype == "bg_image":
                bg_div = (
                    '  <div class="bg-placeholder"'
                    ' style="background-image: url(\'\'\\);">'
                    '</div>'
                )
                inner.append(bg_div)

        section_html = "\n".join(inner)
        section_parts.append(
            f'<section class="section-{cls}">\n{section_html}\n</section>'
        )

    body_content = "\n".join(section_parts) if section_parts else "<div></div>"
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "  <title>Converted Template</title>\n"
        "</head>\n"
        "<body>\n"
        f"{body_content}\n"
        "</body>\n"
        "</html>"
    )


# ---------------------------------------------------------------------------
# PngConverter
# ---------------------------------------------------------------------------


class PngConverter:
    """Convert Figma PNG templates to HTML/CSS using Vision AI.

    Accepts any AIProviderBase implementation (dependency injection).
    Tests should pass a mock provider — no real API calls are made.
    """

    def __init__(self, provider: AIProviderBase) -> None:
        self._provider = provider

    # -- Public API ----------------------------------------------------------

    async def convert(self, png_path: str | Path) -> ConversionResult:
        """Convert a PNG file to HTML/CSS with slot mapping.

        Args:
            png_path: Path to the PNG file (str or Path).

        Returns:
            ConversionResult with html, css, quality_score, slot_mapping.
        """
        from detail_forge.asset_pipeline.slot_tagger import SlotTagger

        png_path = Path(png_path)
        image_data = png_path.read_bytes()

        # Step 1: Vision AI layout extraction
        raw_json = await self._provider.analyze_image(image_data, _LAYOUT_PROMPT)
        layout = self._parse_layout_response(raw_json)

        # Step 2: Generate HTML/CSS
        html, css = self._generate_html_css(layout)

        # Step 3: Auto-tag slots and build SlotMapping
        tagger = SlotTagger()
        tag_result = tagger.tag(html)

        # Step 4: Score the result
        quality_score = score_conversion_quality(
            html=tag_result.html,
            css=css,
            slot_mapping=tag_result.slot_mapping,
            slot_count=tag_result.slot_count,
        )

        return ConversionResult(
            html=tag_result.html,
            css=css,
            quality_score=quality_score,
            slot_mapping=tag_result.slot_mapping,
        )

    def _generate_html_css(self, layout: LayoutStructure) -> tuple[str, str]:
        """Generate (html, css) from a LayoutStructure."""
        html = _build_html_for_layout(layout)
        css = _build_css_for_layout(layout)
        return html, css

    # -- Private helpers -----------------------------------------------------

    def _parse_layout_response(self, raw_json: str) -> LayoutStructure:
        """Parse Vision AI JSON response into a LayoutStructure."""
        try:
            data = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            return LayoutStructure()

        global_hints = data.get("style_hints", {})
        sections: list[LayoutSection] = []
        for sec in data.get("sections", []):
            sec_type = sec.get("type", "general")
            content_areas = sec.get("content_areas", [])
            style_hints = sec.get("style_hints", {})
            sections.append(
                LayoutSection(
                    section_type=sec_type,
                    content_areas=content_areas,
                    style_hints=style_hints,
                )
            )

        return LayoutStructure(sections=sections, global_style_hints=global_hints)
