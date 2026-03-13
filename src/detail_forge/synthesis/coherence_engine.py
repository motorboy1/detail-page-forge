"""Coherence Engine — validates and adjusts consistency across composed sections.

Fully deterministic, no AI calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from detail_forge.designer.design_tokens import DesignTokenSet
from detail_forge.synthesis.section_compositor import ComposedSection


@dataclass
class CoherenceReport:
    """Result of coherence validation across multiple ComposedSection objects.

    Attributes:
        is_coherent: True if all sections are consistently styled.
        score: 0-10 coherence score.
        issues: Descriptions of detected inconsistencies.
        adjustments_made: Descriptions of auto-corrections applied.
    """

    is_coherent: bool
    score: float
    issues: list[str] = field(default_factory=list)
    adjustments_made: list[str] = field(default_factory=list)


# Regex to extract font-family declarations from CSS text
_FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;]+);", re.IGNORECASE)
# Regex to find CSS custom property references
_CSS_VAR_COLOR_RE = re.compile(r"var\(--df-color-[^)]+\)")
_CSS_VAR_SPACING_RE = re.compile(r"var\(--df-spacing-[^)]+\)")


class CoherenceEngine:
    """Validates and auto-adjusts cross-section design consistency.

    Checks:
    - Font family consistency (all sections reference same font tokens)
    - Color consistency (all sections reference --df-color-* tokens)
    - Spacing consistency (all sections reference --df-spacing-* tokens)
    """

    def check(
        self,
        sections: list[ComposedSection],
        tokens: DesignTokenSet,
    ) -> CoherenceReport:
        """Validate consistency across composed sections.

        Args:
            sections: List of ComposedSection objects to validate.
            tokens: DesignTokenSet defining the design system.

        Returns:
            CoherenceReport with score, issues, and coherence status.
        """
        if not sections:
            return CoherenceReport(is_coherent=True, score=10.0, issues=[], adjustments_made=[])

        issues: list[str] = []

        # --- Font consistency check ----------------------------------------
        font_sets: list[set[str]] = []
        for sec in sections:
            fonts = set(_FONT_FAMILY_RE.findall(sec.css))
            if fonts:
                font_sets.append(fonts)

        consistent_fonts = True
        if len(font_sets) > 1:
            first = font_sets[0]
            for fs in font_sets[1:]:
                if fs != first:
                    consistent_fonts = False
                    issues.append("Inconsistent font families across sections")
                    break

        # --- Color token reference check -----------------------------------
        consistent_colors = True
        # Check if any section uses raw color values instead of token vars
        raw_color_re = re.compile(r"(?:color|background(?:-color)?)\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))")
        all_raw_colors: list[set[str]] = []
        for sec in sections:
            raw_colors = set(raw_color_re.findall(sec.html))
            if raw_colors:
                all_raw_colors.append(raw_colors)

        if len(all_raw_colors) > 1:
            first_colors = all_raw_colors[0]
            for color_set in all_raw_colors[1:]:
                if color_set != first_colors:
                    consistent_colors = False
                    issues.append("Inconsistent raw color values across sections")
                    break

        # --- Spacing token reference check ---------------------------------
        consistent_spacing = True
        # Check if sections use inconsistent spacing values
        raw_spacing_re = re.compile(r"(?:padding|margin|gap)\s*:\s*(\d+(?:px|rem|em|%)(?:\s+\d+(?:px|rem|em|%))*)")
        all_raw_spacing: list[set[str]] = []
        for sec in sections:
            raw_spacings = set(raw_spacing_re.findall(sec.html + sec.css))
            if raw_spacings:
                all_raw_spacing.append(raw_spacings)

        if len(all_raw_spacing) > 1:
            first_spacing = all_raw_spacing[0]
            for spacing_set in all_raw_spacing[1:]:
                if spacing_set != first_spacing:
                    consistent_spacing = False
                    issues.append("Inconsistent spacing values across sections")
                    break

        # --- Transition/animation check ------------------------------------
        has_transitions = any(
            "transition" in sec.css.lower() or "animation" in sec.css.lower() for sec in sections
        )

        # --- Score calculation (deterministic) ----------------------------
        score = (
            (3.0 if consistent_fonts else 0.0)
            + (3.0 if consistent_colors else 0.0)
            + (2.0 if consistent_spacing else 0.0)
            + (2.0 if has_transitions else 0.0)
        )

        is_coherent = len(issues) == 0

        return CoherenceReport(
            is_coherent=is_coherent,
            score=round(score, 4),
            issues=issues,
            adjustments_made=[],
        )

    def adjust(
        self,
        sections: list[ComposedSection],
        tokens: DesignTokenSet,
    ) -> list[ComposedSection]:
        """Wrap each section in a div with consistent token CSS variables.

        Ensures all sections reference the same design tokens by injecting
        a wrapper div with CSS custom properties when they are missing.

        Args:
            sections: Sections to adjust.
            tokens: DesignTokenSet providing the canonical variable values.

        Returns:
            Adjusted list of ComposedSection objects.
        """
        if not sections:
            return []

        # Build inline style string with essential token vars
        token_style = _build_inline_token_style(tokens)
        css_vars_block = tokens.to_css()

        adjusted: list[ComposedSection] = []
        for sec in sections:
            # Wrap HTML with token vars if not already present
            combined = sec.html + sec.css
            if "--df-color-primary" not in combined:
                wrapped_html = (
                    f'<div class="df-section-wrapper" style="{token_style}">{sec.html}</div>'
                )
            else:
                wrapped_html = sec.html

            # Ensure the CSS block includes token variables
            new_css = sec.css
            if css_vars_block not in new_css:
                new_css = css_vars_block + "\n" + new_css

            adjusted.append(
                ComposedSection(
                    section_type=sec.section_type,
                    html=wrapped_html,
                    css=new_css,
                    quality_score=sec.quality_score,
                    warnings=sec.warnings,
                )
            )

        return adjusted


# ─── Private helpers ────────────────────────────────────────────────────────


def _build_inline_token_style(tokens: DesignTokenSet) -> str:
    """Build a condensed inline-style string of token CSS custom properties."""
    parts = [f"{t.css_name}: {t.css_value}" for t in tokens.tokens]
    return "; ".join(parts)
