"""SlotTagger: auto data-slot tagging and D1000 principle detection.

Uses BeautifulSoup4 to parse HTML and identify content areas,
then tags them with data-slot attributes and generates a SlotMapping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from detail_forge.templates.models import SlotMapping

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TagResult:
    """Result of SlotTagger.tag()."""

    html: str
    slot_mapping: SlotMapping
    slot_count: int


# ---------------------------------------------------------------------------
# D1000 rule patterns (deterministic, no AI)
# ---------------------------------------------------------------------------

# Each entry: (principle_id, confidence, detection_fn(html: str, css: str) -> bool)
# Detection functions use simple heuristics over HTML/CSS text.

def _has_background_image(html: str, css: str) -> bool:
    combined = html + css
    return bool(re.search(r"background-image\s*:\s*url\(", combined, re.IGNORECASE))


def _has_minimal_content(html: str, css: str) -> bool:
    """Principle 3: minimal content with large whitespace."""
    tag_count = len(re.findall(r"<[a-z]", html, re.IGNORECASE))
    padding_match = re.search(r"padding\s*:\s*(\d+)px", css)
    large_padding = padding_match and int(padding_match.group(1)) >= 60
    return tag_count <= 5 or bool(large_padding)


def _has_grid_or_repeat(html: str, css: str) -> bool:
    """Principle 13: big element + repetition."""
    return bool(re.search(r"\bgrid\b|\brepeat\b|\bflex-wrap\b", css, re.IGNORECASE))


def _has_full_bleed_title(html: str, css: str) -> bool:
    """Principle 22: hammer title (full-width title band)."""
    return bool(re.search(r"width\s*:\s*100%", css) and re.search(r"<h1|<h2", html, re.IGNORECASE))


def _has_overlapping_elements(html: str, css: str) -> bool:
    """Principle 2: elements overlap / pierce each other."""
    return bool(re.search(r"\bposition\s*:\s*(absolute|relative)\b", css, re.IGNORECASE))


def _has_gradient(html: str, css: str) -> bool:
    """Principle 28: metal texture (gradient)."""
    return bool(re.search(r"gradient", css, re.IGNORECASE))


def _has_color_ratio(html: str, css: str) -> bool:
    """Principle 15: 6:3:1 color formula (multiple color declarations)."""
    color_count = len(re.findall(r"(?:color|background)\s*:\s*#|rgba?\(", css, re.IGNORECASE))
    return color_count >= 3


_D1000_RULES: list[tuple[int, float, object]] = [
    (2, 0.7, _has_overlapping_elements),
    (3, 0.6, _has_minimal_content),
    (13, 0.65, _has_grid_or_repeat),
    (15, 0.7, _has_color_ratio),
    (22, 0.75, _has_full_bleed_title),
    (27, 0.8, _has_background_image),
    (28, 0.7, _has_gradient),
    (36, 0.7, lambda h, c: bool(re.search(r"blur\(", c, re.IGNORECASE))),
]


# ---------------------------------------------------------------------------
# SlotTagger
# ---------------------------------------------------------------------------


class SlotTagger:
    """Parse HTML, attach data-slot attributes, and generate a SlotMapping.

    Text tagging strategy:
        h1 (first)           -> data-slot="text_0"  (headline)
        h2 or second heading -> data-slot="text_1"  (subheadline)
        p / body text        -> data-slot="text_N"  (body slots)
        button / a (CTA)     -> data-slot="text_N"  (cta)

    Image tagging strategy:
        img elements         -> data-slot="img_0", "img_1", ...
        elements with inline background-image -> data-slot-bg="bg_0"
    """

    def tag(self, html: str) -> TagResult:
        """Parse and tag HTML, returning TagResult with modified HTML + SlotMapping."""
        soup = BeautifulSoup(html, "html.parser")

        text_counter = 0
        img_counter = 0
        bg_counter = 0

        slot_mapping = SlotMapping()

        # Tag elements with background-image style FIRST (before other traversal)
        bg_pattern = re.compile(r"background-image\s*:\s*url\(", re.IGNORECASE)
        for el in soup.find_all(style=True):
            style = el.get("style", "")
            if bg_pattern.search(style):
                slot_name = f"bg_{bg_counter}"
                el["data-slot-bg"] = slot_name
                if bg_counter == 0:
                    slot_mapping.background_image = slot_name
                bg_counter += 1

        # Tag text elements
        body_slots: list[str] = []
        processed_elements: set = set()

        for el in soup.find_all(["h1", "h2", "h3", "p", "button", "a", "span"]):
            if id(el) in processed_elements:
                continue
            # Skip empty elements and navigation-level anchors with href
            text = el.get_text(strip=True)
            if not text or len(text) < 2:
                continue

            slot_name = f"text_{text_counter}"
            el["data-slot"] = slot_name
            processed_elements.add(id(el))

            if text_counter == 0:
                slot_mapping.headline = slot_name
            elif text_counter == 1:
                slot_mapping.subheadline = slot_name
            elif el.name in ("p",):
                body_slots.append(slot_name)
            elif el.name in ("button", "a") and slot_mapping.cta_text is None:
                slot_mapping.cta_text = slot_name

            text_counter += 1

        if body_slots:
            slot_mapping.body = body_slots

        # Tag img elements
        for img in soup.find_all("img"):
            slot_name = f"img_{img_counter}"
            img["data-slot"] = slot_name
            if img_counter == 0:
                slot_mapping.product_image = slot_name
            img_counter += 1

        total_slots = text_counter + img_counter + bg_counter

        return TagResult(
            html=str(soup),
            slot_mapping=slot_mapping,
            slot_count=total_slots,
        )

    def analyze_d1000_principles(self, html: str, css: str) -> list[dict]:
        """Detect D1000 principles from HTML and CSS using heuristics.

        Returns:
            List of {"principle_id": int, "confidence": float} dicts.
            Result is deterministic — same inputs always produce same output.
        """
        results: list[dict] = []
        for principle_id, confidence, detect_fn in _D1000_RULES:
            try:
                matched = detect_fn(html, css)
            except Exception:
                matched = False
            if matched:
                results.append({"principle_id": principle_id, "confidence": confidence})
        return results
