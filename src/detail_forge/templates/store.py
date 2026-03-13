"""Template store — file-based CRUD for the template library."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from detail_forge.templates.models import (
    SlotMapping,
    TemplateIndex,
    TemplateMetadata,
)


class TemplateStore:
    """File-based template library.

    Layout::

        base_dir/
          index.json
          {slug}/
            template.html
            slots.json
            slot_mapping.json
            metadata.json
            thumbnail.jpg
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[3] / "data" / "templates"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.base_dir / "index.json"

    # ── Index ──────────────────────────────────────────

    def load_index(self) -> TemplateIndex:
        if self._index_path.exists():
            return TemplateIndex.from_dict(json.loads(self._index_path.read_text()))
        return TemplateIndex()

    def save_index(self, index: TemplateIndex) -> None:
        self._index_path.write_text(
            json.dumps(index.to_dict(), ensure_ascii=False, indent=2)
        )

    # ── CRUD ──────────────────────────────────────────

    def add_template(
        self,
        metadata: TemplateMetadata,
        html: str,
        slots: dict,
        slot_mapping: SlotMapping,
        thumbnail_bytes: bytes | None = None,
    ) -> None:
        tdir = self.base_dir / metadata.id
        tdir.mkdir(parents=True, exist_ok=True)

        (tdir / "template.html").write_text(html, encoding="utf-8")
        (tdir / "slots.json").write_text(
            json.dumps(slots, ensure_ascii=False, indent=2)
        )
        (tdir / "slot_mapping.json").write_text(
            json.dumps(slot_mapping.to_dict(), ensure_ascii=False, indent=2)
        )

        if not metadata.created_at:
            metadata.created_at = datetime.now(timezone.utc).isoformat()

        if thumbnail_bytes:
            thumb_path = tdir / "thumbnail.jpg"
            thumb_path.write_bytes(thumbnail_bytes)
            metadata.thumbnail_path = str(thumb_path.relative_to(self.base_dir))

        (tdir / "metadata.json").write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2)
        )

        # Update index
        index = self.load_index()
        index.templates = [t for t in index.templates if t.id != metadata.id]
        index.templates.append(metadata)
        self.save_index(index)

    def get_template(
        self, template_id: str
    ) -> tuple[TemplateMetadata, str, dict, SlotMapping]:
        tdir = self.base_dir / template_id
        if not tdir.exists():
            raise FileNotFoundError(f"Template {template_id} not found")
        meta = TemplateMetadata.from_dict(
            json.loads((tdir / "metadata.json").read_text())
        )
        html = (tdir / "template.html").read_text(encoding="utf-8")
        slots = json.loads((tdir / "slots.json").read_text())
        mapping = SlotMapping.from_dict(
            json.loads((tdir / "slot_mapping.json").read_text())
        )
        return meta, html, slots, mapping

    def delete_template(self, template_id: str) -> None:
        tdir = self.base_dir / template_id
        if tdir.exists():
            shutil.rmtree(tdir)
        index = self.load_index()
        index.templates = [t for t in index.templates if t.id != template_id]
        self.save_index(index)

    def list_templates(
        self, section_type: str | None = None
    ) -> list[TemplateMetadata]:
        index = self.load_index()
        if section_type:
            return [t for t in index.templates if t.section_type == section_type]
        return index.templates

    # ── Section splitting ───────────────────────────────

    def split_to_sections(self, template_id: str) -> list[TemplateMetadata]:
        """Split a full_page template into individual section templates.

        Parses the template HTML for <section> and <div class="..."> elements
        and registers each as a standalone template in the store.

        Args:
            template_id: ID of the full_page template to split.

        Returns:
            List of TemplateMetadata for the newly created section templates.

        Raises:
            FileNotFoundError: If template_id does not exist.
        """
        from bs4 import BeautifulSoup

        meta, html, slots, mapping = self.get_template(template_id)

        soup = BeautifulSoup(html, "html.parser")

        # Find top-level section elements — prefer <section> tags, fallback to
        # named <div class="..."> children of <body>.
        section_elements = soup.find_all("section")
        if not section_elements:
            body = soup.find("body")
            if body:
                section_elements = [
                    el for el in body.children
                    if hasattr(el, "name") and el.name in ("div", "article", "aside")
                    and el.get("class")
                ]

        if not section_elements:
            # Nothing to split — register the whole template as one section
            section_elements = [soup]

        created: list[TemplateMetadata] = []
        for idx, el in enumerate(section_elements):
            # Infer section type from class name or ordinal
            css_classes = el.get("class", []) if hasattr(el, "get") else []
            section_type = (
                css_classes[0].replace("section-", "") if css_classes
                else f"section-{idx}"
            )

            # Normalize to known section types
            _known = {"hero", "features", "benefits", "cta", "testimonials", "faq"}
            if section_type not in _known:
                section_type = "general"

            section_id = f"{template_id}--{section_type}-{idx}"
            section_html = f"<!DOCTYPE html><html><body>{el}</body></html>"

            # Build a fresh SlotMapping for this section by scanning its slots
            section_slots: dict[str, str] = {}
            section_mapping = SlotMapping()

            slot_els = el.find_all(attrs={"data-slot": True}) if hasattr(el, "find_all") else []
            for sel in slot_els:
                slot_name = sel["data-slot"]
                section_slots[slot_name] = sel.get_text(strip=True)
                if slot_name == mapping.headline:
                    section_mapping.headline = slot_name
                elif slot_name == mapping.subheadline:
                    section_mapping.subheadline = slot_name
                elif slot_name == mapping.cta_text:
                    section_mapping.cta_text = slot_name
                elif slot_name in mapping.body:
                    section_mapping.body.append(slot_name)

            img_els = el.find_all(attrs={"data-slot": True}) if hasattr(el, "find_all") else []
            for img_el in img_els:
                slot_name = img_el.get("data-slot", "")
                if slot_name.startswith("img_") and not section_mapping.product_image:
                    section_mapping.product_image = slot_name

            section_meta = TemplateMetadata(
                id=section_id,
                name=f"{meta.name} — {section_type} ({idx})",
                section_type=section_type,
                d1000_principles=meta.d1000_principles.copy(),
                category=meta.category,
                tags=[f"parent:{template_id}", template_id],
            )

            self.add_template(
                metadata=section_meta,
                html=section_html,
                slots=section_slots,
                slot_mapping=section_mapping,
            )
            created.append(section_meta)

        return created
