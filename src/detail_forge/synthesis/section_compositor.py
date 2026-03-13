"""Section Compositor — fills data-slot HTML templates with SectionCopy.

Uses BeautifulSoup4 for HTML manipulation. Fully deterministic, no AI calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from detail_forge.copywriter.generator import SectionCopy
from detail_forge.designer.design_tokens import DesignTokenSet
from detail_forge.templates.models import SlotMapping


@dataclass
class ComposedSection:
    """Result of composing a template section with copy and design tokens.

    Attributes:
        section_type: Hero, features, benefits, etc.
        html: Full HTML with data-slot attributes filled.
        css: Section-specific CSS (token variables, overrides).
        quality_score: 0-10 score based on slot fill rate and token coverage.
        warnings: Missing slots, unfilled tokens, etc.
    """

    section_type: str
    html: str
    css: str
    quality_score: float
    warnings: list[str] = field(default_factory=list)


class SectionCompositor:
    """Composes template HTML with SectionCopy and DesignTokenSet.

    All logic is deterministic. No AI API calls are made.
    """

    def compose(
        self,
        template_html: str,
        copy: SectionCopy,
        slot_mapping: SlotMapping,
        tokens: DesignTokenSet,
        product_images: dict[str, str] | None = None,
    ) -> ComposedSection:
        """Compose a template section with copy, slot mapping, and design tokens.

        Args:
            template_html: Raw HTML string with data-slot attributes.
            copy: SectionCopy with headline, subheadline, body, cta_text, etc.
            slot_mapping: Maps semantic copy fields to data-slot names.
            tokens: Design tokens to inject as CSS custom properties.
            product_images: Optional dict mapping slot_name -> image URL.

        Returns:
            ComposedSection with filled HTML, CSS block, quality score, and warnings.
        """
        if not template_html:
            return ComposedSection(
                section_type=copy.section_type,
                html="",
                css=tokens.to_css(),
                quality_score=0.0,
                warnings=["Empty template HTML"],
            )

        soup = BeautifulSoup(template_html, "html.parser")
        warnings: list[str] = []

        # --- Fill text slots -----------------------------------------------
        slot_data = _build_slot_data(copy, slot_mapping)

        # Collect image slot names so they are not reported as unfilled text slots
        image_slot_names: set[str] = set()
        if slot_mapping.product_image:
            image_slot_names.add(slot_mapping.product_image)
        if slot_mapping.background_image:
            image_slot_names.add(slot_mapping.background_image)

        all_text_slots = [
            el.get("data-slot")
            for el in soup.find_all(attrs={"data-slot": True})
            if el.get("data-slot") not in image_slot_names
        ]
        total_slots = len(all_text_slots)
        filled_slots = 0

        for el in soup.find_all(attrs={"data-slot": True}):
            name = el.get("data-slot")
            if name in slot_data:
                el.string = slot_data[name]
                filled_slots += 1
            elif name and name not in image_slot_names:
                warnings.append(f"Unfilled slot: {name}")

        # --- Fill image slots ----------------------------------------------
        if product_images:
            for slot_name, url in product_images.items():
                for img_el in soup.find_all(attrs={"data-slot": slot_name}):
                    img_el["src"] = url

        # --- Build CSS token block ----------------------------------------
        css = tokens.to_css()

        # --- Quality score (deterministic) --------------------------------
        has_headline = bool(copy.headline)
        has_image = bool(product_images)
        has_cta = bool(copy.cta_text)

        fill_rate = (filled_slots / total_slots) if total_slots > 0 else 0.0
        score = (
            fill_rate * 5.0
            + (2.0 if has_headline else 0.0)
            + (1.5 if has_image else 0.0)
            + (1.5 if has_cta else 0.0)
        )
        score = min(10.0, score)

        # Produce warnings for missing optional copy fields
        if slot_mapping.subheadline and not copy.subheadline:
            warnings.append("Missing subheadline copy")
        if slot_mapping.body and not copy.body:
            warnings.append("Missing body copy")
        if slot_mapping.cta_text and not copy.cta_text:
            warnings.append("Missing cta_text copy")
        if slot_mapping.headline and not copy.headline:
            warnings.append("Missing headline copy")

        return ComposedSection(
            section_type=copy.section_type,
            html=str(soup),
            css=css,
            quality_score=round(score, 4),
            warnings=warnings,
        )


# --- Private helpers --------------------------------------------------------


def _build_slot_data(copy: SectionCopy, slot_mapping: SlotMapping) -> dict[str, str]:
    """Build a mapping from slot names to text values from copy + slot_mapping."""
    data: dict[str, str] = {}

    if slot_mapping.headline and copy.headline:
        data[slot_mapping.headline] = copy.headline
    if slot_mapping.subheadline and copy.subheadline:
        data[slot_mapping.subheadline] = copy.subheadline
    if slot_mapping.cta_text and copy.cta_text:
        data[slot_mapping.cta_text] = copy.cta_text

    # Body may span multiple slots
    if slot_mapping.body and copy.body:
        parts = _split_body(copy.body, len(slot_mapping.body))
        for slot_name, part in zip(slot_mapping.body, parts):
            data[slot_name] = part

    # Extra mappings
    for field_name, slot_name in slot_mapping.extra.items():
        value = getattr(copy, field_name, None)
        if value:
            data[slot_name] = str(value)

    return data


def _split_body(body: str, n: int) -> list[str]:
    """Split body text into n parts by sentences."""
    parts = [s.strip() for s in re.split(r"[.。!]\s*", body) if len(s.strip()) > 3]
    if not parts:
        return [body] * n
    while len(parts) < n:
        parts.append(parts[-1] if parts else body)
    return parts[:n]
