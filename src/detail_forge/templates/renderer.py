"""Render templates by filling data-slot attributes with product copy."""

from __future__ import annotations

import re
from bs4 import BeautifulSoup

from detail_forge.copywriter.generator import SectionCopy
from detail_forge.templates.models import SlotMapping


def fill_template(
    html: str,
    slot_mapping: SlotMapping,
    copy: SectionCopy,
    product_photos: list[str] | None = None,
) -> str:
    """Fill data-slot attributes in template HTML with CopyResult fields."""
    soup = BeautifulSoup(html, "html.parser")

    slot_data: dict[str, str] = {}

    if slot_mapping.headline and copy.headline:
        slot_data[slot_mapping.headline] = copy.headline
    if slot_mapping.subheadline and copy.subheadline:
        slot_data[slot_mapping.subheadline] = copy.subheadline
    if slot_mapping.cta_text and copy.cta_text:
        slot_data[slot_mapping.cta_text] = copy.cta_text

    # Body may span multiple slots
    if slot_mapping.body and copy.body:
        body_parts = _split_body(copy.body, len(slot_mapping.body))
        for slot_name, part in zip(slot_mapping.body, body_parts):
            slot_data[slot_name] = part

    # Extra mappings
    for field_name, slot_name in slot_mapping.extra.items():
        if hasattr(copy, field_name):
            slot_data[slot_name] = getattr(copy, field_name)

    # Fill text slots
    for el in soup.find_all(attrs={"data-slot": True}):
        name = el.get("data-slot")
        stype = el.get("data-slot-type", "text")
        if name in slot_data:
            if stype == "text":
                el.string = slot_data[name]
            elif stype == "image" and product_photos:
                el["src"] = product_photos[0]

    # Fill image slots from product_photos
    if product_photos and slot_mapping.product_image:
        for el in soup.find_all(attrs={"data-slot": slot_mapping.product_image}):
            el["src"] = product_photos[0]

    # Fill background image slots
    if product_photos and slot_mapping.background_image:
        for el in soup.find_all(attrs={"data-slot-bg": slot_mapping.background_image}):
            style = el.get("style", "")
            style = re.sub(
                r"background-image:\s*url\(['\"]?[^'\")\s]+['\"]?\)",
                f"background-image: url('{product_photos[0]}')",
                style,
            )
            el["style"] = style

    return str(soup)


def _split_body(body: str, n: int) -> list[str]:
    """Split body text into n parts by sentences."""
    parts = [s.strip() for s in re.split(r"[.。!]\s*", body) if len(s.strip()) > 3]
    if not parts:
        return [body] * n
    while len(parts) < n:
        parts.append(parts[-1] if parts else body)
    return parts[:n]
