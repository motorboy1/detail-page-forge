"""Image selection logic — bridging UI selections to pipeline."""

from __future__ import annotations

from detail_forge.designer.generator import SectionDesign


def is_all_selected(designs: list[SectionDesign]) -> bool:
    """Check if all sections have a selected image."""
    return all(d.selected_index >= 0 for d in designs if d is not None)


def get_selected_images(designs: list[SectionDesign]) -> list[bytes]:
    """Get list of selected image data."""
    return [d.selected_image for d in designs if d and d.selected_image]
