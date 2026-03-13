"""Page Assembler — assembles composed sections into a complete HTML page.

Fully deterministic, no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass

from detail_forge.designer.design_tokens import DesignTokenSet
from detail_forge.synthesis.coherence_engine import CoherenceEngine
from detail_forge.synthesis.section_compositor import ComposedSection, SectionCompositor

# Google Fonts used by common DesignTokenSet configurations
_GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&"
    "family=Playfair+Display:ital,wght@0,400;0,700;1,400&"
    "family=Space+Grotesk:wght@300;400;500;700&display=swap"
)

_SECTION_TRANSITIONS_CSS = """
/* Section transitions */
.dp > section,
.dp > div {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease, transform 0.6s ease;
  margin-bottom: 0;
}
.dp > section.df-visible,
.dp > div.df-visible {
  opacity: 1;
  transform: translateY(0);
}
.df-section-wrapper {
  transition: all 0.3s ease;
}
"""

_NOSCRIPT_FALLBACK = """
<noscript>
<style>
.dp > section, .dp > div { opacity: 1 !important; transform: none !important; }
</style>
</noscript>
"""

_SCROLL_REVEAL_JS = """
<script>
(function() {
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('df-visible');
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.dp > section, .dp > div').forEach(function(el) {
    observer.observe(el);
  });
})();
</script>
"""


@dataclass
class AssembledPage:
    """A fully assembled HTML page from multiple composed sections.

    Attributes:
        html: Complete HTML document string.
        section_count: Number of sections assembled.
        total_quality_score: Average quality score across all sections.
        coherence_score: Coherence score from CoherenceEngine.
    """

    html: str
    section_count: int
    total_quality_score: float
    coherence_score: float


class PageAssembler:
    """Assembles multiple ComposedSection objects into a single HTML document.

    Uses SectionCompositor for per-section composition and CoherenceEngine
    for cross-section consistency validation and adjustment.
    """

    def __init__(
        self,
        compositor: SectionCompositor,
        coherence: CoherenceEngine,
    ) -> None:
        self._compositor = compositor
        self._coherence = coherence

    def assemble(
        self,
        sections_data: list[dict],
        tokens: DesignTokenSet,
        product_name: str = "",
    ) -> AssembledPage:
        """Assemble sections into a complete HTML page.

        Args:
            sections_data: List of dicts, each containing:
                - template_html: str
                - copy: SectionCopy
                - slot_mapping: SlotMapping
                - product_images: dict[str, str] | None (optional)
            tokens: DesignTokenSet for the complete page.
            product_name: Optional product name for the <title> element.

        Returns:
            AssembledPage with complete HTML and quality metrics.
        """
        if not sections_data:
            return AssembledPage(
                html=_build_html_document(
                    sections_html="",
                    tokens_css=tokens.to_css(),
                    product_name=product_name,
                    coherence_score=10.0,
                ),
                section_count=0,
                total_quality_score=0.0,
                coherence_score=10.0,
            )

        # --- Compose each section -----------------------------------------
        composed: list[ComposedSection] = []
        for entry in sections_data:
            template_html = entry.get("template_html", "")
            copy = entry["copy"]
            slot_mapping = entry["slot_mapping"]
            product_images = entry.get("product_images")

            section = self._compositor.compose(
                template_html=template_html,
                copy=copy,
                slot_mapping=slot_mapping,
                tokens=tokens,
                product_images=product_images,
            )
            composed.append(section)

        # --- Coherence check and adjust ------------------------------------
        coherence_report = self._coherence.check(composed, tokens)
        adjusted = self._coherence.adjust(composed, tokens)

        # --- Compute aggregate quality scores -----------------------------
        total_quality = sum(s.quality_score for s in adjusted) / len(adjusted) if adjusted else 0.0

        # --- Build the HTML document -------------------------------------
        sections_html = "\n".join(s.html for s in adjusted)
        html_doc = _build_html_document(
            sections_html=sections_html,
            tokens_css=tokens.to_css(),
            product_name=product_name,
            coherence_score=coherence_report.score,
        )

        return AssembledPage(
            html=html_doc,
            section_count=len(adjusted),
            total_quality_score=round(total_quality, 4),
            coherence_score=round(coherence_report.score, 4),
        )


# ─── Private helpers ────────────────────────────────────────────────────────


def _build_html_document(
    sections_html: str,
    tokens_css: str,
    product_name: str,
    coherence_score: float,  # noqa: ARG001 — reserved for meta tag if needed
) -> str:
    """Build a complete HTML5 document wrapping the composed sections."""
    title = product_name if product_name else "Detail Page"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="{_GOOGLE_FONTS_URL}" rel="stylesheet" />
  <style>
    {tokens_css}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: var(--df-font-body, sans-serif); background: var(--df-color-bg, #fff); }}
    .dp {{ width: 100%; }}
    {_SECTION_TRANSITIONS_CSS}
  </style>
</head>
<body>
  <div class="dp">
{sections_html}
  </div>
  {_NOSCRIPT_FALLBACK}
  {_SCROLL_REVEAL_JS}
</body>
</html>"""
