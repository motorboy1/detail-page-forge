"""One-Click Generator — orchestrates the full pipeline from template selection
to rendered output in a single call.

Pipeline:
    TemplateStore.get_template()
    -> PageAssembler.assemble()
    -> WebRenderer.render()
    -> NaverRenderer.render()  [optional]
    -> QualityGate.evaluate()

Fully deterministic, no AI calls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from detail_forge.copywriter.generator import ProductInfo, SectionCopy
from detail_forge.designer.theme_generator import Theme, ThemeGenerator
from detail_forge.exceptions import InputValidationError, TemplateNotFoundError
from detail_forge.output.naver_renderer import NaverHTML, NaverRenderer
from detail_forge.output.quality_gate import OutputQuality, QualityGate
from detail_forge.output.web_renderer import WebHTML, WebRenderer
from detail_forge.synthesis.coherence_engine import CoherenceEngine
from detail_forge.synthesis.page_assembler import AssembledPage, PageAssembler
from detail_forge.synthesis.section_compositor import SectionCompositor
from detail_forge.templates.store import TemplateStore


@dataclass
class GenerationResult:
    """Complete result from OneClickGenerator.generate().

    Attributes:
        assembled_page: Assembled HTML page from PageAssembler.
        theme: Theme used for generation.
        web_html: Responsive standalone HTML from WebRenderer.
        naver_html: Naver SmartStore HTML, or None if not requested.
        quality: OutputQuality from QualityGate.
        generation_time_ms: Wall-clock time for the full pipeline in milliseconds.
    """

    assembled_page: AssembledPage
    theme: Theme
    web_html: WebHTML
    naver_html: NaverHTML | None
    quality: OutputQuality
    generation_time_ms: int
    warnings: list[str] = field(default_factory=list)


class OneClickGenerator:
    """Orchestrates the full detail-page generation pipeline.

    Usage::

        store = TemplateStore()
        gen = OneClickGenerator(template_store=store)
        result = gen.generate(
            product=product_info,
            copy_sections=copy_list,
            template_ids=["hero-01", "features-01"],
        )

    Args:
        template_store: TemplateStore instance for loading templates.
        compositor: Optional SectionCompositor (created if not provided).
        coherence: Optional CoherenceEngine (created if not provided).
    """

    def __init__(
        self,
        template_store: TemplateStore,
        compositor: SectionCompositor | None = None,
        coherence: CoherenceEngine | None = None,
    ) -> None:
        self._store = template_store
        self._compositor = compositor or SectionCompositor()
        self._coherence = coherence or CoherenceEngine()
        self._assembler = PageAssembler(
            compositor=self._compositor,
            coherence=self._coherence,
        )
        self._web_renderer = WebRenderer()
        self._naver_renderer = NaverRenderer()
        self._quality_gate = QualityGate()
        self._theme_generator = ThemeGenerator()

    def generate(
        self,
        product: ProductInfo,
        copy_sections: list[SectionCopy],
        template_ids: list[str],
        theme: Theme | None = None,
        principle_ids: list[int] | None = None,
        include_naver: bool = True,
    ) -> GenerationResult:
        """Run the full generation pipeline.

        Theme selection priority:
            1. ``theme`` parameter (if provided, used as-is)
            2. ``principle_ids`` parameter (auto-creates custom theme)
            3. Default: 'classic_trust' recipe

        Args:
            product: Product information for the page.
            copy_sections: List of SectionCopy objects (one per template section).
            template_ids: Ordered list of template IDs to load and assemble.
            theme: Explicit Theme to use (overrides principle_ids).
            principle_ids: D1000 principle IDs to build a custom theme.
            include_naver: If True, also render Naver SmartStore HTML.

        Returns:
            GenerationResult with all pipeline outputs.
        """
        start_ms = time.monotonic()

        # ── Input validation ──────────────────────────────────────────────
        if not product.name or not product.name.strip():
            raise InputValidationError(
                "Product name is required",
                error_code="VALIDATION_MISSING_FIELD",
                details={"missing_fields": ["name"]},
            )

        # ── Theme resolution ──────────────────────────────────────────────
        resolved_theme = self._resolve_theme(theme, principle_ids)

        # ── Template loading ──────────────────────────────────────────────
        sections_data, template_warnings = self._build_sections_data(template_ids, copy_sections)

        # ── Page assembly ─────────────────────────────────────────────────
        assembled = self._assembler.assemble(
            sections_data=sections_data,
            tokens=resolved_theme.tokens,
            product_name=product.name,
        )

        # ── Web rendering ─────────────────────────────────────────────────
        web_html = self._web_renderer.render(
            html=assembled.html,
            product_name=product.name,
        )

        # ── Naver rendering (optional) ────────────────────────────────────
        naver_html: NaverHTML | None = None
        if include_naver:
            naver_html = self._naver_renderer.render(html=assembled.html)

        # ── Quality evaluation ────────────────────────────────────────────
        quality = self._quality_gate.evaluate(html=web_html.html, platform="web")

        elapsed_ms = int((time.monotonic() - start_ms) * 1000)

        return GenerationResult(
            assembled_page=assembled,
            theme=resolved_theme,
            web_html=web_html,
            naver_html=naver_html,
            quality=quality,
            generation_time_ms=elapsed_ms,
            warnings=template_warnings,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _resolve_theme(
        self,
        theme: Theme | None,
        principle_ids: list[int] | None,
    ) -> Theme:
        """Resolve which theme to use for this generation run."""
        if theme is not None:
            return theme
        if principle_ids is not None:
            return self._theme_generator.generate_custom(principle_ids=principle_ids)
        return self._theme_generator.generate("classic_trust")

    def _build_sections_data(
        self,
        template_ids: list[str],
        copy_sections: list[SectionCopy],
    ) -> tuple[list[dict], list[str]]:
        """Load templates and pair each with the best matching copy section.

        Pairing strategy:
        - First try to match by section_type (copy.section_type == meta.section_type)
        - Fall back to positional index pairing
        - If template_ids is empty, returns an empty list

        Args:
            template_ids: Ordered list of template IDs.
            copy_sections: Available SectionCopy objects.

        Returns:
            List of dicts ready for PageAssembler.assemble().
        """
        if not template_ids:
            return [], []

        sections_data: list[dict] = []
        warnings: list[str] = []

        for idx, tid in enumerate(template_ids):
            try:
                meta, html, _slots, slot_mapping = self._store.get_template(tid)
            except (TemplateNotFoundError, FileNotFoundError):
                warnings.append(f"Template '{tid}' not found, skipped")
                continue

            # Match copy: prefer section_type match, then positional, then empty
            copy = _find_copy(meta.section_type, idx, copy_sections)

            sections_data.append(
                {
                    "template_html": html,
                    "copy": copy,
                    "slot_mapping": slot_mapping,
                }
            )

        return sections_data, warnings


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _find_copy(
    section_type: str,
    positional_index: int,
    copy_sections: list[SectionCopy],
) -> SectionCopy:
    """Find the best SectionCopy for a template section.

    Priority:
        1. First copy whose section_type matches exactly.
        2. Copy at positional_index (if available).
        3. Empty SectionCopy as fallback.
    """
    # Try type match first
    for copy in copy_sections:
        if copy.section_type == section_type:
            return copy

    # Fall back to positional
    if positional_index < len(copy_sections):
        return copy_sections[positional_index]

    # Last resort: empty copy
    return SectionCopy(section_index=positional_index, section_type=section_type)
