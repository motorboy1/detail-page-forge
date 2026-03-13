"""Output renderers for detail-page-forge.

Converts generated HTML detail pages into platform-specific formats:
- CoupangRenderer: 860px PNG image strips for Coupang
- NaverRenderer: sanitized HTML for Naver SmartStore
- WebRenderer: responsive standalone HTML for web deployment
- QualityGate: deterministic 5-dimension quality evaluation
- ExportManager: ZIP packaging of all rendered outputs
"""

from __future__ import annotations

from detail_forge.output.coupang_renderer import CoupangImageSet, CoupangRenderer
from detail_forge.output.export_manager import ExportManager, ExportPackage
from detail_forge.output.naver_renderer import NaverHTML, NaverRenderer
from detail_forge.output.quality_gate import OutputQuality, QualityDimension, QualityGate
from detail_forge.output.web_renderer import WebHTML, WebRenderer

__all__ = [
    "CoupangRenderer",
    "CoupangImageSet",
    "NaverRenderer",
    "NaverHTML",
    "WebRenderer",
    "WebHTML",
    "QualityGate",
    "QualityDimension",
    "OutputQuality",
    "ExportManager",
    "ExportPackage",
]
