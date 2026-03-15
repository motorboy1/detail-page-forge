"""Python port of the figma-clone Slotify pipeline.

Transforms raw HTML into a template with data-slot attributes and
generates a slot inventory (slots.json format).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag


# Elements whose visible text content is slottable
_TEXT_TAGS = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "span", "a", "li", "td", "th",
    "button", "label", "figcaption", "blockquote",
    "strong", "em", "b", "i", "small", "mark",
})

# Minimum text length to create a slot (skip empty/whitespace)
_MIN_TEXT_LEN = 1


@dataclass
class SlotRecord:
    """A single editable slot discovered in the HTML."""

    name: str           # e.g. "text_0", "img_3", "link_5"
    type: str           # "text" | "image" | "link"
    default_value: str  # current text / src / href
    tag: str = ""       # HTML tag name
    alt: str = ""       # img alt text
    text: str = ""      # link display text
    subtype: str = ""   # "background" for bg-image slots
    index: int = 0

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "type": self.type,
            "defaultValue": self.default_value,
            "tag": self.tag,
            "index": self.index,
        }
        if self.alt:
            d["alt"] = self.alt
        if self.text:
            d["text"] = self.text
        if self.subtype:
            d["subtype"] = self.subtype
        return d


@dataclass
class SlotifyResult:
    """Output of the slotify operation."""

    html: str
    slots: list[SlotRecord] = field(default_factory=list)
    text_count: int = 0
    image_count: int = 0
    link_count: int = 0

    def to_slots_dict(self) -> dict:
        """Return dict matching the slots.json schema."""
        return {
            "total": len(self.slots),
            "text": self.text_count,
            "image": self.image_count,
            "link": self.link_count,
            "slots": [s.to_dict() for s in self.slots],
        }


def slotify(html: str) -> SlotifyResult:
    """Add data-slot attributes to all editable elements in *html*.

    Mirrors the figma-clone Slotify pipeline:
    1. Text slots: h1-h6, p, span, a, li, button, etc.
    2. Image slots: <img> tags
    3. Link slots: <a href="...">
    4. Background image slots: style="background-image: url(...)"

    Returns a SlotifyResult with the transformed HTML and slot inventory.
    """
    soup = BeautifulSoup(html, "html.parser")
    slots: list[SlotRecord] = []
    text_idx = 0
    img_idx = 0
    link_idx = 0
    bg_idx = 0

    # Track elements we've already slotted to avoid duplicates
    slotted: set[int] = set()

    # -- 1. Text slots --
    for el in soup.find_all(_TEXT_TAGS):
        if not isinstance(el, Tag):
            continue
        el_id = id(el)
        if el_id in slotted:
            continue

        # Skip elements that only contain other tag children (no direct text)
        direct_text = el.string or "".join(
            t.strip() for t in el.find_all(string=True, recursive=False)
        )
        if not direct_text or len(direct_text.strip()) < _MIN_TEXT_LEN:
            continue

        # Skip if a parent is already slotted (avoid double-slotting nested text)
        if _has_slotted_ancestor(el, slotted):
            continue

        slot_name = f"text_{text_idx}"
        el["data-slot"] = slot_name
        el["data-slot-type"] = "text"
        slotted.add(el_id)

        slots.append(SlotRecord(
            name=slot_name,
            type="text",
            default_value=direct_text.strip(),
            tag=el.name,
            index=text_idx,
        ))
        text_idx += 1

    # -- 2. Image slots --
    for el in soup.find_all("img"):
        if not isinstance(el, Tag):
            continue
        el_id = id(el)
        if el_id in slotted:
            continue

        slot_name = f"img_{img_idx}"
        el["data-slot"] = slot_name
        el["data-slot-type"] = "image"
        slotted.add(el_id)

        slots.append(SlotRecord(
            name=slot_name,
            type="image",
            default_value=el.get("src", ""),
            alt=el.get("alt", ""),
            tag="img",
            index=img_idx,
        ))
        img_idx += 1

    # -- 3. Link slots --
    for el in soup.find_all("a", href=True):
        if not isinstance(el, Tag):
            continue

        slot_name = f"link_{link_idx}"
        el["data-slot-link"] = slot_name
        # Don't add to slotted set -- <a> can also have text slots

        link_text = el.get_text(strip=True)
        slots.append(SlotRecord(
            name=slot_name,
            type="link",
            default_value=el["href"],
            text=link_text,
            tag="a",
            index=link_idx,
        ))
        link_idx += 1

    # -- 4. Background image slots --
    bg_pattern = re.compile(r"background(?:-image)?\s*:\s*url\(([^)]+)\)", re.I)
    for el in soup.find_all(style=True):
        if not isinstance(el, Tag):
            continue
        style_val = el.get("style", "")
        match = bg_pattern.search(style_val)
        if not match:
            continue

        bg_url = match.group(1).strip("'\"")
        slot_name = f"bg_{bg_idx}"
        el["data-slot-bg"] = slot_name

        slots.append(SlotRecord(
            name=slot_name,
            type="image",
            subtype="background",
            default_value=bg_url,
            tag=el.name,
            index=bg_idx,
        ))
        bg_idx += 1

    return SlotifyResult(
        html=str(soup),
        slots=slots,
        text_count=text_idx,
        image_count=img_idx + bg_idx,
        link_count=link_idx,
    )


def _has_slotted_ancestor(el: Tag, slotted: set[int]) -> bool:
    """Check if any ancestor of *el* has already been slotted."""
    parent = el.parent
    while parent and isinstance(parent, Tag):
        if id(parent) in slotted:
            return True
        parent = parent.parent
    return False
