"""Batch converter for Vision AI-generated HTML templates.

Workflow:
1. Claude Code reads PNG images and generates raw HTML
2. Raw HTML is saved to data/templates/_staging/{template_id}.html
3. This module processes staged HTML files:
   - Runs Slotify (adds data-slot attributes)
   - Auto-generates metadata (D1000 principles, category, tags)
   - Imports into the TemplateStore
4. Progress is tracked in data/templates/_staging/progress.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from detail_forge.templates.importer import TemplateImporter
from detail_forge.templates.models import SlotMapping, TemplateMetadata
from detail_forge.templates.slotify import slotify
from detail_forge.templates.store import TemplateStore

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_STAGING_DIR = _PROJECT_ROOT / "data" / "templates" / "_staging"
_FIGMA_DIR = _PROJECT_ROOT / "data" / "d1000_knowledge" / "figma_templates"
_PART2_DIR = _PROJECT_ROOT / "data" / "d1000_knowledge" / "figma_part2"
_PROGRESS_FILE = _STAGING_DIR / "progress.json"


# Section type detection based on layout characteristics
_SECTION_KEYWORDS = {
    "hero": ["hero", "banner", "main", "landing", "cover", "splash"],
    "features": ["feature", "benefit", "advantage", "grid", "card"],
    "cta": ["cta", "call-to-action", "action", "signup", "subscribe"],
    "testimonial": ["testimonial", "review", "quote", "feedback"],
    "pricing": ["pricing", "price", "plan", "tier"],
    "gallery": ["gallery", "portfolio", "showcase", "grid"],
    "footer": ["footer", "bottom", "contact"],
    "about": ["about", "story", "mission"],
}

# Design style tag detection
_STYLE_TAGS = {
    "dark": ["dark", "black", "#000", "#111", "#1a1a", "rgb(0,", "rgba(0,"],
    "light": ["white", "#fff", "#fafafa", "rgb(255,", "light"],
    "gradient": ["gradient", "linear-gradient", "radial-gradient"],
    "minimal": ["minimal", "clean", "simple"],
    "bold": ["bold", "heavy", "strong", "impact"],
    "premium": ["premium", "luxury", "elegant", "serif"],
    "modern": ["modern", "geometric", "sans-serif"],
    "playful": ["playful", "fun", "colorful", "vibrant"],
}


def ensure_staging_dir() -> Path:
    """Create the staging directory if it doesn't exist."""
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return _STAGING_DIR


def save_staged_html(
    template_id: str,
    html: str,
    *,
    source_image: str = "",
    d1000_principles: list[int] | None = None,
    category: str = "",
    tags: list[str] | None = None,
    section_type: str = "",
) -> Path:
    """Save raw HTML to staging directory with optional metadata hint."""
    staging = ensure_staging_dir()
    html_path = staging / f"{template_id}.html"
    html_path.write_text(html, encoding="utf-8")

    # Save metadata hints alongside
    hints = {
        "template_id": template_id,
        "source_image": source_image,
        "d1000_principles": d1000_principles or [],
        "category": category,
        "tags": tags or [],
        "section_type": section_type,
        "staged_at": datetime.now(timezone.utc).isoformat(),
    }
    hints_path = staging / f"{template_id}.json"
    hints_path.write_text(json.dumps(hints, ensure_ascii=False, indent=2))

    return html_path


def process_staged(template_id: str, store: TemplateStore | None = None) -> TemplateMetadata:
    """Process a single staged HTML file into the template store."""
    if store is None:
        store = TemplateStore()

    staging = ensure_staging_dir()
    html_path = staging / f"{template_id}.html"
    hints_path = staging / f"{template_id}.json"

    if not html_path.exists():
        raise FileNotFoundError(f"No staged HTML for {template_id}")

    raw_html = html_path.read_text(encoding="utf-8")

    # Load metadata hints
    hints: dict = {}
    if hints_path.exists():
        hints = json.loads(hints_path.read_text())

    # Run Slotify
    result = slotify(raw_html)

    # Auto-detect section type if not provided
    section_type = hints.get("section_type", "") or _detect_section_type(raw_html)

    # Auto-detect style tags if not provided
    tags = hints.get("tags", []) or _detect_style_tags(raw_html)

    # Auto-detect category
    category = hints.get("category", "") or "design"

    # Build slot mapping
    importer = TemplateImporter(store)
    slot_mapping = importer.auto_map_slots(result.to_slots_dict(), section_type)

    # Generate thumbnail from source image if available
    thumbnail_bytes = None
    source_image = hints.get("source_image", "")
    if source_image:
        src_path = Path(source_image)
        if not src_path.is_absolute():
            # Try figma_templates then figma_part2
            for base in [_FIGMA_DIR, _PART2_DIR]:
                candidate = base / source_image
                if candidate.exists():
                    src_path = candidate
                    break
        if src_path.exists():
            from detail_forge.templates.importer import _make_thumbnail
            thumbnail_bytes = _make_thumbnail(src_path)

    # Create metadata
    metadata = TemplateMetadata(
        id=template_id,
        name=_id_to_name(template_id),
        section_type=section_type,
        d1000_principles=hints.get("d1000_principles", []),
        category=category,
        source_url=f"figma://{hints.get('source_image', template_id)}",
        ssim_score=0.0,  # AI-generated, no SSIM comparison
        slot_count=len(result.slots),
        tags=tags,
    )

    # Add to store
    store.add_template(
        metadata,
        result.html,
        result.to_slots_dict(),
        slot_mapping,
        thumbnail_bytes,
    )

    # Update progress
    _update_progress(template_id, "completed")

    return metadata


def process_all_staged(store: TemplateStore | None = None) -> list[TemplateMetadata]:
    """Process all staged HTML files."""
    if store is None:
        store = TemplateStore()

    staging = ensure_staging_dir()
    results = []

    for html_file in sorted(staging.glob("*.html")):
        template_id = html_file.stem
        # Skip already processed
        progress = _load_progress()
        if progress.get(template_id, {}).get("status") == "completed":
            continue

        try:
            _update_progress(template_id, "processing")
            metadata = process_staged(template_id, store)
            results.append(metadata)
        except Exception as e:
            _update_progress(template_id, "error", str(e))

    return results


def get_progress() -> dict:
    """Get current processing progress."""
    progress = _load_progress()
    total = len(list(_STAGING_DIR.glob("*.html"))) if _STAGING_DIR.exists() else 0
    completed = sum(1 for v in progress.values() if v.get("status") == "completed")
    errors = sum(1 for v in progress.values() if v.get("status") == "error")
    return {
        "total_staged": total,
        "completed": completed,
        "errors": errors,
        "remaining": total - completed - errors,
        "details": progress,
    }


def list_unprocessed_images() -> list[dict]:
    """List all Figma template images that haven't been converted yet."""
    progress = _load_progress()
    processed_ids = {
        k for k, v in progress.items() if v.get("status") == "completed"
    }

    images = []
    for img_path in sorted(_FIGMA_DIR.glob("*.png")):
        tid = _image_to_template_id(img_path)
        if tid not in processed_ids:
            images.append({
                "path": str(img_path),
                "template_id": tid,
                "filename": img_path.name,
                "collection": "figma_templates",
            })

    for img_path in sorted(_PART2_DIR.glob("*.png")):
        tid = _image_to_template_id(img_path)
        if tid not in processed_ids:
            images.append({
                "path": str(img_path),
                "template_id": tid,
                "filename": img_path.name,
                "collection": "figma_part2",
            })

    return images


# -- Private helpers --

def _detect_section_type(html: str) -> str:
    """Heuristically detect section type from HTML content."""
    html_lower = html.lower()
    for stype, keywords in _SECTION_KEYWORDS.items():
        if any(kw in html_lower for kw in keywords):
            return stype
    return "hero"  # Default to hero for single-section designs


def _detect_style_tags(html: str) -> list[str]:
    """Detect visual style tags from HTML/CSS."""
    html_lower = html.lower()
    detected = []
    for tag, indicators in _STYLE_TAGS.items():
        if any(ind in html_lower for ind in indicators):
            detected.append(tag)
    return detected or ["modern"]


def _id_to_name(template_id: str) -> str:
    """Convert template_id to display name."""
    # d1000-figma-287 -> D1000 Figma 287
    return template_id.replace("-", " ").replace("_", " ").title()


def _image_to_template_id(img_path: Path) -> str:
    """Convert image filename to template ID."""
    stem = img_path.stem  # e.g. "template_1_287" or "part2_1_3"
    return f"d1000-{stem.replace('_', '-')}"


def _load_progress() -> dict:
    """Load progress tracking file."""
    if _PROGRESS_FILE.exists():
        return json.loads(_PROGRESS_FILE.read_text())
    return {}


def _update_progress(template_id: str, status: str, error: str = "") -> None:
    """Update progress for a template."""
    progress = _load_progress()
    progress[template_id] = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        progress[template_id]["error"] = error
    ensure_staging_dir()
    _PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
