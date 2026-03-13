"""Asset pipeline for detail-page-forge.

Converts Figma PNG templates to slot-tagged HTML/CSS and manages
template registration with D1000 principle auto-tagging.
"""

from __future__ import annotations

from detail_forge.asset_pipeline.png_converter import (
    ConversionResult,
    LayoutSection,
    LayoutStructure,
    PngConverter,
    score_conversion_quality,
)
from detail_forge.asset_pipeline.slot_tagger import SlotTagger, TagResult

__all__ = [
    "PngConverter",
    "SlotTagger",
    "ConversionResult",
    "LayoutSection",
    "LayoutStructure",
    "TagResult",
    "score_conversion_quality",
]
