"""Technique Engine — selects and applies design techniques automatically.

Three-tier system:
    Atomic → Compound → Workflow

Pipeline:
    ProductInfo + context → TechniqueEngine.select() → TechniqueResult
    TechniqueResult → TechniqueRenderer.render() → DesignTokenSet + CSS
"""

from detail_forge.technique_engine.engine import TechniqueEngine, TechniqueResult
from detail_forge.technique_engine.renderer import TechniqueRenderer
from detail_forge.technique_engine.template_matcher import TemplateMatcher, TemplateMatchResult

__all__ = [
    "TechniqueEngine",
    "TechniqueRenderer",
    "TechniqueResult",
    "TemplateMatcher",
    "TemplateMatchResult",
]
