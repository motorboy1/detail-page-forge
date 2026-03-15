"""Template Matcher — auto-selects templates from the 181-template library
based on TechniqueResult workflow sections.

Maps workflow section_type + compound mood + category to best-matching templates.

Fully deterministic, no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.technique_engine.engine import SectionTechniques, TechniqueResult
from detail_forge.templates.models import TemplateMetadata
from detail_forge.templates.store import TemplateStore


@dataclass
class MatchedTemplate:
    """A template matched to a workflow section with a relevance score."""

    template: TemplateMetadata
    section_order: int
    section_type: str
    score: float
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class TemplateMatchResult:
    """Complete result of template matching for a workflow."""

    matched: list[MatchedTemplate]
    template_ids: list[str]
    unmatched_sections: list[int]
    warnings: list[str] = field(default_factory=list)


# ─── Section type mapping (workflow → template library) ──────────

# Workflow sections may use types not present in the template library.
# Map them to the closest available template section_type.
_SECTION_TYPE_FALLBACKS: dict[str, list[str]] = {
    "hero": ["hero", "full_page"],
    "story": ["full_page", "hero"],
    "lifestyle": ["full_page", "hero", "features"],
    "atmosphere": ["full_page", "hero"],
    "immersion": ["hero", "full_page"],
    "showcase": ["hero", "full_page"],
    "depth": ["hero", "full_page"],
    "feature": ["features", "hero", "full_page"],
    "spec": ["features", "full_page"],
    "detail": ["features", "full_page"],
    "comparison": ["features", "full_page"],
    "proof": ["features", "testimonial", "full_page"],
    "testimonial": ["testimonial", "full_page", "features"],
    "cta": ["cta", "hero", "full_page"],
    "conversion": ["cta", "hero", "full_page"],
    "timeline": ["features", "full_page"],
    "gallery": ["full_page", "hero", "features"],
    "scroll": ["full_page", "hero"],
    "interaction": ["full_page", "features", "hero"],
    "reveal": ["hero", "full_page"],
    "divider": ["full_page", "features"],
    "system": ["full_page", "features"],
    "component": ["features", "full_page"],
}

# ─── Mood to tag mapping ────────────────────────────────────────

_MOOD_TAG_MAP: dict[str, list[str]] = {
    "luxury": ["premium", "dark", "minimal"],
    "premium": ["premium", "dark", "bold"],
    "elegant": ["premium", "minimal", "serif", "light"],
    "minimal": ["minimal", "light", "modern"],
    "clean": ["minimal", "light", "modern"],
    "modern": ["modern", "bold"],
    "bold": ["bold", "dark", "gradient"],
    "dynamic": ["bold", "gradient", "modern"],
    "dramatic": ["dark", "bold", "gradient"],
    "cinematic": ["dark", "bold", "premium"],
    "immersive": ["dark", "gradient", "bold"],
    "warm": ["warm", "light", "nature"],
    "authentic": ["warm", "nature", "light"],
    "narrative": ["light", "serif", "editorial"],
    "editorial": ["editorial", "serif", "italic"],
    "retro": ["serif", "warm"],
    "hip": ["bold", "gradient", "modern"],
    "playful": ["bold", "gradient", "light"],
    "youthful": ["bold", "gradient", "modern"],
    "technical": ["dark", "modern", "minimal"],
    "futuristic": ["dark", "gradient", "bold"],
    "professional": ["modern", "light", "minimal"],
    "trustworthy": ["light", "modern"],
    "sensory": ["gradient", "warm", "nature"],
    "tactile": ["warm", "nature"],
    "interactive": ["modern", "bold", "gradient"],
    "polished": ["premium", "modern", "dark"],
    "urgent": ["bold", "dark"],
    "converting": ["bold", "dark"],
    "communal": ["warm", "light"],
    "social": ["light", "modern"],
    "progressive": ["modern", "gradient"],
    "aspirational": ["premium", "light"],
    "artistic": ["editorial", "italic", "serif"],
    "mysterious": ["dark", "gradient"],
}


class TemplateMatcher:
    """Auto-selects templates for each workflow section.

    Usage::

        matcher = TemplateMatcher(template_store)
        match_result = matcher.match(technique_result, category="beauty")
        template_ids = match_result.template_ids
    """

    def __init__(self, store: TemplateStore) -> None:
        self._store = store
        self._all_templates: list[TemplateMetadata] | None = None

    def _get_all_templates(self) -> list[TemplateMetadata]:
        """Lazy-load all templates."""
        if self._all_templates is None:
            self._all_templates = self._store.list_templates()
        return self._all_templates

    def match(
        self,
        result: TechniqueResult,
        category: str | None = None,
        max_per_section: int = 1,
    ) -> TemplateMatchResult:
        """Match templates to each section in the workflow.

        Args:
            result: TechniqueResult from TechniqueEngine.select().
            category: Product category for filtering (e.g. 'beauty').
            max_per_section: Number of templates per section (default 1).

        Returns:
            TemplateMatchResult with matched templates and ordered IDs.
        """
        all_templates = self._get_all_templates()
        matched: list[MatchedTemplate] = []
        used_ids: set[str] = set()
        unmatched: list[int] = []
        warnings: list[str] = []

        for section in result.section_techniques:
            candidates = self._score_candidates(
                section, all_templates, category, used_ids
            )

            if not candidates:
                unmatched.append(section.section_order)
                warnings.append(
                    f"Section {section.section_order} ({section.section_type}): "
                    f"no matching template found"
                )
                continue

            # Take top N candidates
            top = candidates[:max_per_section]
            for m in top:
                matched.append(m)
                used_ids.add(m.template.id)

        # Build ordered template IDs
        template_ids = [m.template.id for m in matched]

        return TemplateMatchResult(
            matched=matched,
            template_ids=template_ids,
            unmatched_sections=unmatched,
            warnings=warnings,
        )

    def _score_candidates(
        self,
        section: SectionTechniques,
        all_templates: list[TemplateMetadata],
        category: str | None,
        used_ids: set[str],
    ) -> list[MatchedTemplate]:
        """Score and rank all templates for a given section."""
        # Determine valid section types
        valid_types = _SECTION_TYPE_FALLBACKS.get(
            section.section_type,
            [section.section_type, "hero", "full_page"],
        )

        # Collect mood-derived target tags
        target_tags = set()
        for mood in section.compound.mood:
            target_tags.update(_MOOD_TAG_MAP.get(mood, []))

        # Collect D1000 principles from atoms
        atom_principles: set[int] = set()
        for atom in section.atoms:
            if hasattr(atom, "source_id") and isinstance(atom.css.get("properties"), dict):
                # Extract source_id if it's a D1000 principle ID
                try:
                    pid = int(atom.css.get("properties", {}).get("source_id", 0))
                except (ValueError, TypeError):
                    pass

        candidates: list[MatchedTemplate] = []

        for tmpl in all_templates:
            # Skip already used templates (prevent duplicates)
            if tmpl.id in used_ids:
                continue

            score = 0.0
            reasons: list[str] = []

            # 1. Section type match (highest weight)
            if tmpl.section_type in valid_types:
                type_bonus = (len(valid_types) - valid_types.index(tmpl.section_type))
                score += type_bonus * 3
                reasons.append(f"type:{tmpl.section_type}")
            else:
                continue  # Skip templates that don't match any valid type

            # 2. Tag overlap with mood-derived tags
            tmpl_tags = set(tmpl.tags)
            tag_overlap = len(tmpl_tags & target_tags)
            score += tag_overlap * 2
            if tag_overlap:
                reasons.append(f"tags:{tag_overlap}")

            # 3. Category match
            if category:
                if tmpl.category == category:
                    score += 4
                    reasons.append(f"cat:{category}")
                elif tmpl.category in ("general", "design"):
                    score += 1  # Neutral categories get small bonus

            # 4. D1000 principle overlap
            tmpl_principles = set(tmpl.d1000_principles)
            principle_overlap = len(tmpl_principles & atom_principles)
            score += principle_overlap * 1.5
            if principle_overlap:
                reasons.append(f"d1000:{principle_overlap}")

            # 5. SSIM quality bonus
            if tmpl.ssim_score >= 0.85:
                score += 1
            elif tmpl.ssim_score >= 0.7:
                score += 0.5

            # 6. Slot count bonus (more slots = more flexible)
            if tmpl.slot_count >= 5:
                score += 0.5

            candidates.append(MatchedTemplate(
                template=tmpl,
                section_order=section.section_order,
                section_type=section.section_type,
                score=score,
                match_reasons=reasons,
            ))

        # Sort by score descending
        candidates.sort(key=lambda m: m.score, reverse=True)
        return candidates
