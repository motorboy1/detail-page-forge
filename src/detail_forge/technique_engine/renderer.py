"""Technique Renderer — converts selected techniques into CSS/HTML.

Takes TechniqueResult from TechniqueEngine → produces DesignTokenSet + section CSS.

Fully deterministic, no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.designer.design_tokens import (
    CATEGORY_COLOR,
    CATEGORY_EFFECT,
    CATEGORY_SPACING,
    CATEGORY_TYPOGRAPHY,
    DesignToken,
    DesignTokenSet,
)
from detail_forge.technique_engine.engine import (
    AtomicTechnique,
    SectionTechniques,
    TechniqueResult,
)


@dataclass
class SectionCSS:
    """CSS output for a single page section."""

    section_order: int
    section_type: str
    class_name: str
    css_block: str
    inline_styles: dict[str, str]
    animations: list[str]
    pseudo_elements: list[str]


@dataclass
class TechniqueRenderResult:
    """Complete rendering output from TechniqueRenderer.

    Attributes:
        tokens: DesignTokenSet with technique-derived custom properties.
        section_css: Per-section CSS blocks.
        global_css: Page-level CSS (animations, keyframes, utilities).
        technique_annotations: HTML comments for debugging which techniques applied.
    """

    tokens: DesignTokenSet
    section_css: list[SectionCSS]
    global_css: str
    technique_annotations: dict[int, str] = field(default_factory=dict)


# ─── CSS generation constants ────────────────────────────────────────

_SCROLL_REVEAL_CSS = """
.df-scroll-reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
.df-scroll-reveal.df-visible {
  opacity: 1;
  transform: translateY(0);
}
"""

_PARALLAX_CSS = """
.df-parallax-container {
  perspective: 1200px;
  overflow: hidden;
}
.df-parallax-layer {
  transform: translateZ(var(--df-parallax-z, 0px));
  will-change: transform;
}
"""

_SPOTLIGHT_CSS = """
.df-spotlight {
  background: radial-gradient(
    ellipse at var(--df-spot-x, 50%) var(--df-spot-y, 40%),
    rgba(255,255,255,0.15) 0%,
    transparent 60%
  );
}
"""

_FAKE_3D_CSS = """
.df-fake-3d {
  transform: perspective(800px) rotateY(var(--df-rotate-y, 0deg)) rotateX(var(--df-rotate-x, 0deg));
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.df-fake-3d:hover {
  --df-rotate-y: -5deg;
  --df-rotate-x: 5deg;
}
"""

_EASING_KEYFRAMES = """
@keyframes df-fade-up {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes df-scale-in {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes df-slide-left {
  from { opacity: 0; transform: translateX(60px); }
  to { opacity: 1; transform: translateX(0); }
}
"""


class TechniqueRenderer:
    """Converts TechniqueResult into implementable CSS and design tokens.

    Usage::

        renderer = TechniqueRenderer()
        render_result = renderer.render(technique_result)
        tokens = render_result.tokens
        css = render_result.global_css
    """

    def render(self, result: TechniqueResult) -> TechniqueRenderResult:
        """Render a TechniqueResult into CSS and tokens.

        Args:
            result: TechniqueResult from TechniqueEngine.select().

        Returns:
            TechniqueRenderResult with tokens, section CSS, and global CSS.
        """
        # Step 1: Build technique-derived tokens
        tokens = self._build_tokens(result)

        # Step 2: Build per-section CSS
        section_css_list = self._build_section_css(result)

        # Step 3: Build global CSS (animations, utilities)
        global_css = self._build_global_css(result)

        # Step 4: Build debug annotations
        annotations = self._build_annotations(result)

        return TechniqueRenderResult(
            tokens=tokens,
            section_css=section_css_list,
            global_css=global_css,
            technique_annotations=annotations,
        )

    # ─── Token generation ────────────────────────────────────────────

    def _build_tokens(self, result: TechniqueResult) -> DesignTokenSet:
        """Build a DesignTokenSet from technique CSS properties."""
        tokens: list[DesignToken] = []
        seen: set[str] = set()

        for atom in result.all_atoms:
            css_props = atom.css.get("properties", {})
            for prop, value in css_props.items():
                if prop.startswith("--") and prop not in seen:
                    tokens.append(DesignToken(
                        css_name=prop,
                        css_value=str(value),
                        category=_infer_token_category(prop),
                    ))
                    seen.add(prop)

        # Add technique-specific custom properties
        tokens.extend(self._generate_technique_tokens(result))

        return DesignTokenSet(tokens=tokens)

    def _generate_technique_tokens(self, result: TechniqueResult) -> list[DesignToken]:
        """Generate additional custom properties from technique parameters."""
        tokens: list[DesignToken] = []
        atom_ids = {a.id for a in result.all_atoms}

        # Layout technique tokens
        if "layout_negative_space" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-empty-ratio",
                css_value="0.6",
                category=CATEGORY_SPACING,
            ))

        if "layout_four_points" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-grid-point",
                css_value="33% 33%",
                category=CATEGORY_SPACING,
            ))

        # Typography technique tokens
        if "typography_hierarchy" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-scale-ratio",
                css_value="1.618",
                category=CATEGORY_TYPOGRAPHY,
            ))

        # Effect technique tokens
        if "effect_parallax_depth" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-parallax-z",
                css_value="-50px",
                category=CATEGORY_EFFECT,
            ))

        if "effect_spotlight" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-spot-x",
                css_value="50%",
                category=CATEGORY_EFFECT,
            ))
            tokens.append(DesignToken(
                css_name="--df-tech-spot-y",
                css_value="40%",
                category=CATEGORY_EFFECT,
            ))

        # Color technique tokens
        if "color_631_ratio" in atom_ids:
            tokens.append(DesignToken(
                css_name="--df-tech-neutral-ratio",
                css_value="60%",
                category=CATEGORY_COLOR,
            ))
            tokens.append(DesignToken(
                css_name="--df-tech-accent-ratio",
                css_value="30%",
                category=CATEGORY_COLOR,
            ))

        return tokens

    # ─── Section CSS generation ──────────────────────────────────────

    def _build_section_css(self, result: TechniqueResult) -> list[SectionCSS]:
        """Build CSS blocks for each section."""
        sections: list[SectionCSS] = []

        for st in result.section_techniques:
            class_name = f"df-section-{st.section_order}"
            css_rules: list[str] = []
            inline_styles: dict[str, str] = {}
            animations: list[str] = []
            pseudo_elements: list[str] = []

            # Generate rules from each atom
            for atom in st.atoms:
                atom_css = self._atom_to_css(atom, st.section_order)
                css_rules.append(atom_css["rules"])
                inline_styles.update(atom_css["inline"])
                animations.extend(atom_css["animations"])
                pseudo_elements.extend(atom_css["pseudo"])

            # Section container rules
            container_css = self._build_container_css(
                class_name, st, css_rules
            )

            sections.append(SectionCSS(
                section_order=st.section_order,
                section_type=st.section_type,
                class_name=class_name,
                css_block=container_css,
                inline_styles=inline_styles,
                animations=animations,
                pseudo_elements=pseudo_elements,
            ))

        return sections

    def _atom_to_css(self, atom: AtomicTechnique, section_idx: int) -> dict:
        """Convert a single atomic technique to CSS components."""
        rules: list[str] = []
        inline: dict[str, str] = {}
        animations: list[str] = []
        pseudo: list[str] = []
        css_props = atom.css.get("properties", {})

        # ── Layout atoms ─────────────────────────────────────────────
        if atom.id == "layout_negative_space":
            rules.append("padding: 20vh 10vw; min-height: 80vh;")

        elif atom.id == "layout_pierce":
            rules.append("transform: rotate(-15deg); margin-left: -8%;")

        elif atom.id == "layout_four_points":
            rules.append("display: grid; grid-template-columns: repeat(3, 1fr); "
                         "grid-template-rows: repeat(3, 1fr);")

        elif atom.id == "layout_bottom_heavy":
            rules.append("display: flex; flex-direction: column; "
                         "justify-content: flex-end; min-height: 80vh;")

        elif atom.id == "layout_s_curve":
            rules.append("display: flex; flex-direction: column; "
                         "align-items: alternate;")

        elif atom.id == "layout_size_hierarchy":
            rules.append("display: grid; grid-template-columns: 2fr 3fr 1fr; "
                         "align-items: center;")

        elif atom.id == "layout_horizontal_division":
            rules.append("background: linear-gradient(to bottom, "
                         "var(--df-color-primary) 50%, var(--df-color-bg) 50%);")

        elif atom.id == "layout_gravity_stack":
            rules.append("display: flex; flex-direction: column; "
                         "justify-content: flex-end;")

        elif atom.id == "layout_rhythm_pattern":
            rules.append("display: grid; grid-template-columns: 2fr repeat(3, 1fr); "
                         "gap: var(--df-spacing-gap);")

        # ── Color atoms ──────────────────────────────────────────────
        elif atom.id == "color_631_ratio":
            rules.append("/* 6:3:1 ratio enforced via design tokens */")

        elif atom.id == "color_dawn_gradient":
            rules.append("background: linear-gradient(to bottom, "
                         "var(--df-color-primary), var(--df-color-accent), var(--df-color-bg));")

        elif atom.id == "color_low_contrast":
            inline["opacity"] = "0.85"
            rules.append("color: var(--df-color-muted);")

        elif atom.id == "color_colored_punctuation":
            pseudo.append(
                f".df-section-{section_idx} .df-punctuation {{ "
                f"color: var(--df-color-accent); }}"
            )

        elif atom.id == "color_keyword_strategy":
            rules.append("/* keyword strategy applied via token system */")

        # ── Typography atoms ─────────────────────────────────────────
        elif atom.id == "typography_font_mixing":
            rules.append("font-family: var(--df-font-heading);")

        elif atom.id == "typography_text_border":
            rules.append("-webkit-text-stroke: 1px var(--df-color-primary); "
                         "color: transparent;")

        elif atom.id == "typography_image_fill_text":
            rules.append("background-clip: text; -webkit-background-clip: text; "
                         "color: transparent;")

        elif atom.id == "typography_title_hammer":
            rules.append("width: 100%; font-size: clamp(3rem, 8vw, 6rem); "
                         "letter-spacing: 0.5em; text-align: center;")

        elif atom.id == "typography_text_surface":
            pseudo.append(
                f".df-section-{section_idx}::before {{ "
                f"content: attr(data-repeat-text); "
                f"font-size: 0.6rem; line-height: 1.1; opacity: 0.15; "
                f"position: absolute; inset: 0; overflow: hidden; "
                f"pointer-events: none; }}"
            )

        elif atom.id == "typography_hierarchy":
            rules.append("/* modular scale applied via --df-font-size-* tokens */")

        elif atom.id == "typography_density":
            rules.append("letter-spacing: -0.02em; line-height: 1.3;")

        # ── Effect atoms ─────────────────────────────────────────────
        elif atom.id == "effect_spotlight":
            rules.append("position: relative;")
            pseudo.append(
                f".df-section-{section_idx}::after {{ "
                f"content: ''; position: absolute; inset: 0; "
                f"background: radial-gradient(ellipse at 50% 40%, "
                f"rgba(255,255,255,0.15) 0%, transparent 60%); "
                f"pointer-events: none; }}"
            )

        elif atom.id == "effect_mirror":
            pseudo.append(
                f".df-section-{section_idx} .df-product-img {{ "
                f"--reflect: below; "
                f"-webkit-box-reflect: below 0px "
                f"linear-gradient(transparent 60%, rgba(255,255,255,0.3)); }}"
            )

        elif atom.id == "effect_shadow_depth":
            rules.append("box-shadow: var(--df-shadow-depth);")

        elif atom.id == "effect_mesh_gradient":
            rules.append("background: var(--df-gradient-mesh);")

        elif atom.id == "effect_parallax_depth":
            rules.append("perspective: 1200px; overflow: hidden;")

        elif atom.id == "effect_fake_3d":
            rules.append("transform: perspective(800px) rotateY(0deg); "
                         "transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);")

        elif atom.id == "effect_volume":
            rules.append("box-shadow: inset 0 -4px 12px rgba(0,0,0,0.1), "
                         "0 8px 24px rgba(0,0,0,0.08);")

        elif atom.id == "effect_texture_overlay":
            pseudo.append(
                f".df-section-{section_idx}::before {{ "
                f"content: ''; position: absolute; inset: 0; "
                f"background-image: url('data:image/svg+xml,...'); "
                f"opacity: 0.05; mix-blend-mode: multiply; "
                f"pointer-events: none; }}"
            )

        elif atom.id == "effect_water_drop":
            rules.append("border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;")

        # ── Composition atoms ────────────────────────────────────────
        elif atom.id == "composition_tension":
            rules.append("display: flex; align-items: stretch;")
            inline["gap"] = "0"

        elif atom.id == "composition_crowd_contrast":
            rules.append("display: grid; grid-template-columns: 1fr 2fr; "
                         "align-items: center;")

        elif atom.id == "composition_match_cut":
            rules.append("scroll-snap-align: start;")

        elif atom.id == "composition_scene_transition":
            rules.append("scroll-snap-type: y mandatory;")

        elif atom.id == "composition_before_after":
            rules.append("display: grid; grid-template-columns: 1fr 1fr; "
                         "gap: 2px;")

        elif atom.id == "composition_spatial_depth":
            rules.append("perspective: 1000px;")

        elif atom.id == "composition_camera_language":
            rules.append("overflow: hidden;")

        elif atom.id == "composition_blueprint":
            rules.append("background-color: var(--df-color-bg); "
                         "border: 1px solid var(--df-color-muted);")

        elif atom.id == "composition_arrow_connections":
            rules.append("position: relative;")

        elif atom.id == "composition_sticker_scatter":
            rules.append("position: relative;")

        elif atom.id == "composition_repetition":
            rules.append("display: grid; grid-template-columns: repeat(auto-fill, "
                         "minmax(200px, 1fr)); gap: var(--df-spacing-gap);")

        elif atom.id == "composition_text_image_overlap":
            rules.append("position: relative;")

        elif atom.id == "composition_keyhole":
            rules.append("clip-path: circle(30% at 50% 50%); overflow: hidden;")

        elif atom.id == "composition_peeking":
            rules.append("overflow: hidden; position: relative;")

        elif atom.id == "composition_blocking":
            rules.append("position: relative;")

        elif atom.id == "composition_ui_screenshot":
            rules.append("border-radius: 12px; box-shadow: var(--df-shadow-card); "
                         "overflow: hidden;")

        elif atom.id == "composition_torn_paper":
            rules.append("clip-path: polygon(0 0, 100% 2%, 100% 98%, 0 100%);")

        # ── Narrative atoms ──────────────────────────────────────────
        elif atom.id in (
            "narrative_purple_cow", "narrative_storytelling",
            "narrative_soulmate_persona", "narrative_world_building",
            "narrative_fan_conversion", "narrative_risk_scaling",
            "narrative_four_stage_flywheel",
        ):
            rules.append(f"/* {atom.name}: structural pattern, applied via copy */")

        # ── Motion atoms ─────────────────────────────────────────────
        elif atom.id == "motion_scroll_reveal":
            animations.append("df-fade-up")

        elif atom.id == "motion_easing":
            rules.append("transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);")

        elif atom.id == "motion_repetition":
            animations.append("df-scale-in")

        elif atom.id == "motion_arc_trajectory":
            animations.append("df-slide-left")

        elif atom.id == "motion_storyboard":
            rules.append("/* storyboard: section sequencing via scroll-snap */")

        # Fallback: inject raw CSS properties from atom definition
        else:
            for prop, value in css_props.items():
                if not prop.startswith("--"):
                    rules.append(f"{prop}: {value};")

        return {
            "rules": " ".join(rules),
            "inline": inline,
            "animations": animations,
            "pseudo": pseudo,
        }

    def _build_container_css(
        self,
        class_name: str,
        st: SectionTechniques,
        css_rules: list[str],
    ) -> str:
        """Build the complete CSS block for a section container."""
        # Base container styles
        base = [
            f"min-height: {st.height_vh}vh;",
            "position: relative;",
            "overflow: hidden;",
        ]

        # Combine all rules
        all_rules = base + [r for r in css_rules if r.strip()]
        rules_str = "\n    ".join(all_rules)

        return f".{class_name} {{\n    {rules_str}\n}}"

    # ─── Global CSS generation ───────────────────────────────────────

    def _build_global_css(self, result: TechniqueResult) -> str:
        """Build page-level CSS from active technique atoms."""
        parts: list[str] = []
        atom_ids = {a.id for a in result.all_atoms}

        # Always include keyframes
        parts.append(_EASING_KEYFRAMES)

        # Conditional utility CSS based on active atoms
        if "motion_scroll_reveal" in atom_ids:
            parts.append(_SCROLL_REVEAL_CSS)

        if "effect_parallax_depth" in atom_ids:
            parts.append(_PARALLAX_CSS)

        if "effect_spotlight" in atom_ids:
            parts.append(_SPOTLIGHT_CSS)

        if "effect_fake_3d" in atom_ids:
            parts.append(_FAKE_3D_CSS)

        # Responsive overrides
        parts.append(self._build_responsive_css(result))

        return "\n".join(parts)

    def _build_responsive_css(self, result: TechniqueResult) -> str:
        """Build responsive CSS overrides for mobile."""
        return """
@media (max-width: 768px) {
    [class^="df-section-"] {
        min-height: auto;
        padding: 40px 20px;
    }
    .df-fake-3d { transform: none; }
    .df-parallax-layer { transform: none; }
}
"""

    # ─── Debug annotations ───────────────────────────────────────────

    def _build_annotations(self, result: TechniqueResult) -> dict[int, str]:
        """Build HTML comment annotations for each section."""
        annotations: dict[int, str] = {}

        for st in result.section_techniques:
            atom_names = [a.name for a in st.atoms]
            annotation = (
                f"<!-- Technique Engine: section={st.section_type} | "
                f"compound={st.compound.name} | "
                f"atoms=[{', '.join(atom_names)}] -->"
            )
            annotations[st.section_order] = annotation

        return annotations


# ─── Helper functions ────────────────────────────────────────────────


def _infer_token_category(css_name: str) -> str:
    """Infer token category from CSS custom property name."""
    if "color" in css_name or "gradient" in css_name:
        return CATEGORY_COLOR
    if "font" in css_name or "scale" in css_name:
        return CATEGORY_TYPOGRAPHY
    if "spacing" in css_name or "gap" in css_name or "empty" in css_name:
        return CATEGORY_SPACING
    return CATEGORY_EFFECT
