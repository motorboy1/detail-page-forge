"""One-Click Generator — orchestrates the full pipeline from template selection
to rendered output in a single call.

Pipeline:
    TechniqueEngine.select()  [optional, technique-driven mode]
    -> TemplateStore.get_template()
    -> TechniqueRenderer.render()  [optional, technique CSS injection]
    -> PageAssembler.assemble()
    -> WebRenderer.render()
    -> NaverRenderer.render()  [optional]
    -> QualityGate.evaluate()

Fully deterministic, no AI calls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from detail_forge.copywriter.generator import (
    ProductInfo,
    SectionCopy,
    _technique_fallback_copy,
)
from detail_forge.designer.theme_generator import Theme, ThemeGenerator
from detail_forge.exceptions import InputValidationError, TemplateNotFoundError
from detail_forge.output.naver_renderer import NaverHTML, NaverRenderer
from detail_forge.output.quality_gate import OutputQuality, QualityGate
from detail_forge.output.web_renderer import WebHTML, WebRenderer
from detail_forge.synthesis.coherence_engine import CoherenceEngine
from detail_forge.synthesis.page_assembler import AssembledPage, PageAssembler
from detail_forge.synthesis.section_compositor import SectionCompositor
from detail_forge.technique_engine.engine import TechniqueEngine, TechniqueResult
from detail_forge.technique_engine.renderer import TechniqueRenderer, TechniqueRenderResult
from detail_forge.technique_engine.template_matcher import TemplateMatcher, TemplateMatchResult
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
        technique_result: TechniqueResult if technique-driven mode was used.
        technique_render: TechniqueRenderResult with CSS from technique engine.
    """

    assembled_page: AssembledPage
    theme: Theme
    web_html: WebHTML
    naver_html: NaverHTML | None
    quality: OutputQuality
    generation_time_ms: int
    warnings: list[str] = field(default_factory=list)
    technique_result: TechniqueResult | None = None
    technique_render: TechniqueRenderResult | None = None
    template_match: TemplateMatchResult | None = None


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
        self._technique_engine = TechniqueEngine()
        self._technique_renderer = TechniqueRenderer()
        self._template_matcher = TemplateMatcher(self._store)

    def generate(
        self,
        product: ProductInfo,
        copy_sections: list[SectionCopy],
        template_ids: list[str],
        theme: Theme | None = None,
        principle_ids: list[int] | None = None,
        include_naver: bool = True,
        use_technique_engine: bool = False,
        category: str | None = None,
        style_keywords: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> GenerationResult:
        """Run the full generation pipeline.

        Theme selection priority:
            1. ``theme`` parameter (if provided, used as-is)
            2. ``principle_ids`` parameter (auto-creates custom theme)
            3. Default: 'classic_trust' recipe

        When ``use_technique_engine=True``, the Technique Engine automatically
        selects a workflow, resolves atomic techniques, and injects technique-
        derived CSS into the output. Technique tokens are merged with theme
        tokens (technique tokens take priority).

        Args:
            product: Product information for the page.
            copy_sections: List of SectionCopy objects (one per template section).
            template_ids: Ordered list of template IDs to load and assemble.
            theme: Explicit Theme to use (overrides principle_ids).
            principle_ids: D1000 principle IDs to build a custom theme.
            include_naver: If True, also render Naver SmartStore HTML.
            use_technique_engine: If True, activate the Technique Engine pipeline.
            category: Product category for technique selection (e.g. 'beauty').
            style_keywords: Korean style keywords (e.g. ['프리미엄', '미니멀']).
            workflow_id: Explicit workflow ID for technique engine.

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

        # ── Technique Engine (optional) ───────────────────────────────────
        technique_result: TechniqueResult | None = None
        technique_render: TechniqueRenderResult | None = None
        template_match: TemplateMatchResult | None = None

        if use_technique_engine:
            technique_result = self._technique_engine.select(
                product=product,
                category=category,
                style_keywords=style_keywords,
                workflow_id=workflow_id,
            )
            technique_render = self._technique_renderer.render(technique_result)

            # Merge technique tokens into theme tokens (technique wins on conflict)
            resolved_theme = Theme(
                name=resolved_theme.name,
                description=resolved_theme.description,
                principle_ids=resolved_theme.principle_ids,
                tokens=resolved_theme.tokens.merge(technique_render.tokens),
                mood=resolved_theme.mood,
                category_affinity=resolved_theme.category_affinity,
            )

            # Auto-select templates if none provided
            if not template_ids:
                template_match = self._template_matcher.match(
                    result=technique_result,
                    category=category,
                )
                template_ids = template_match.template_ids

                # Auto-generate technique-aware copy if none provided
                if not copy_sections:
                    fallback_copy = _technique_fallback_copy(
                        product, technique_result
                    )
                    copy_sections = fallback_copy.sections
                else:
                    # Extend copy_sections to match template count if shorter
                    while len(copy_sections) < len(template_match.matched):
                        m = template_match.matched[len(copy_sections)]
                        copy_sections.append(SectionCopy(
                            section_index=len(copy_sections),
                            section_type=m.section_type,
                        ))

        # ── Template loading ──────────────────────────────────────────────
        sections_data, template_warnings = self._build_sections_data(template_ids, copy_sections)

        # ── Page assembly ─────────────────────────────────────────────────
        assembled = self._assembler.assemble(
            sections_data=sections_data,
            tokens=resolved_theme.tokens,
            product_name=product.name,
        )

        # ── Inject technique CSS into assembled HTML ──────────────────────
        if technique_render:
            assembled = self._inject_technique_css(assembled, technique_render)

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
            technique_result=technique_result,
            technique_render=technique_render,
            template_match=template_match,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _inject_technique_css(
        self,
        assembled: AssembledPage,
        technique_render: TechniqueRenderResult,
    ) -> AssembledPage:
        """Inject technique-derived CSS into assembled HTML.

        Adds global CSS (keyframes, utilities) and per-section CSS into the
        <style> block of the assembled page.
        """
        # Build the technique CSS block
        css_parts: list[str] = [
            "/* ── Technique Engine CSS ── */",
            technique_render.global_css,
        ]
        for sec_css in technique_render.section_css:
            css_parts.append(sec_css.css_block)
            css_parts.extend(sec_css.pseudo_elements)

        technique_css = "\n".join(css_parts)

        # Inject before </style> or append as new <style> block
        html = assembled.html
        if "</style>" in html:
            html = html.replace("</style>", technique_css + "\n</style>", 1)
        else:
            html = html.replace("</head>", f"<style>\n{technique_css}\n</style>\n</head>", 1)

        return AssembledPage(
            html=html,
            section_count=assembled.section_count,
            total_quality_score=assembled.total_quality_score,
            coherence_score=assembled.coherence_score,
        )

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
