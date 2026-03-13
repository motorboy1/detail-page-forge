"""Import figma-clone output into the template library."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image
import io

from detail_forge.templates.models import SlotMapping, TemplateMetadata
from detail_forge.templates.store import TemplateStore


class TemplateImporter:
    def __init__(self, store: TemplateStore) -> None:
        self.store = store

    def import_from_figma_clone(
        self,
        output_dir: str | Path,
        *,
        template_id: str | None = None,
        name: str = "",
        section_type: str = "full_page",
        d1000_principles: list[int] | None = None,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> TemplateMetadata:
        """Import a figma-clone output directory as a template."""
        output_dir = Path(output_dir)

        clone_html = (output_dir / "clone.html").read_text(encoding="utf-8")
        slots = json.loads((output_dir / "slots.json").read_text())

        # Read quality report
        ssim = 0.0
        report_path = output_dir / "report.json"
        if report_path.exists():
            report = json.loads(report_path.read_text())
            ssim = report.get("ssim", 0.0)

        # Auto-generate ID from directory name
        if not template_id:
            template_id = _slugify(output_dir.parent.name + "-" + output_dir.name)
            if template_id.endswith("-"):
                template_id = _slugify(output_dir.name)

        if not name:
            name = template_id.replace("-", " ").title()

        # Source URL from extract-meta
        source_url = ""
        meta_path = output_dir / "extract-meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            source_url = meta.get("url", "")

        # Auto-map slots
        slot_mapping = self.auto_map_slots(slots, section_type)

        # Generate thumbnail from original.png
        thumbnail_bytes = None
        orig_png = output_dir / "original.png"
        if orig_png.exists():
            thumbnail_bytes = _make_thumbnail(orig_png)

        metadata = TemplateMetadata(
            id=template_id,
            name=name,
            section_type=section_type,
            d1000_principles=d1000_principles or [],
            category=category,
            source_url=source_url,
            ssim_score=ssim,
            slot_count=slots.get("total", 0),
            tags=tags or [],
        )

        self.store.add_template(
            metadata, clone_html, slots, slot_mapping, thumbnail_bytes
        )
        return metadata

    def auto_map_slots(self, slots: dict, section_type: str) -> SlotMapping:
        """Heuristically map slot names to semantic fields."""
        slot_list = slots.get("slots", [])

        h_tags = []
        p_tags = []
        btn_tags = []
        img_tags = []
        bg_tags = []

        for s in slot_list:
            tag = s.get("tag", "").lower()
            stype = s.get("type", "")
            name = s.get("name", "")

            if stype == "image":
                img_tags.append(name)
            elif tag in ("h1", "h2", "h3"):
                h_tags.append(name)
            elif tag in ("button", "a") and _looks_like_cta(s.get("defaultValue", "")):
                btn_tags.append(name)
            elif stype == "text":
                p_tags.append(name)

        # Check for bg slots
        for s in slot_list:
            if s.get("name", "").startswith("bg_"):
                bg_tags.append(s["name"])

        return SlotMapping(
            headline=h_tags[0] if h_tags else (p_tags[0] if p_tags else None),
            subheadline=h_tags[1] if len(h_tags) > 1 else (p_tags[1] if len(p_tags) > 1 else None),
            body=p_tags[2:5] if len(p_tags) > 2 else p_tags[1:3],
            cta_text=btn_tags[0] if btn_tags else None,
            product_image=img_tags[0] if img_tags else None,
            background_image=bg_tags[0] if bg_tags else None,
        )


def _looks_like_cta(text: str) -> bool:
    cta_words = ["구매", "주문", "보기", "신청", "시작", "buy", "shop", "order", "get", "start", "try"]
    return any(w in text.lower() for w in cta_words)


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣-]", "-", text.lower())
    return re.sub(r"-+", "-", text).strip("-")


def _make_thumbnail(image_path: Path, width: int = 400, quality: int = 75) -> bytes:
    img = Image.open(image_path)
    ratio = width / img.width
    new_h = int(img.height * ratio)
    img = img.resize((width, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
