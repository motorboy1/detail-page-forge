"""Synthesis package — M-2.1 Synthesis Engine Core + M-2.3 OneClickGenerator.

Public exports:
    SectionCompositor: Fills template HTML slots with SectionCopy + DesignTokenSet.
    CoherenceEngine: Validates and adjusts cross-section design consistency.
    PageAssembler: Assembles sections into a complete HTML page.
    OneClickGenerator: Orchestrates the full pipeline from template to rendered output.
    GenerationResult: Dataclass holding all pipeline outputs.
"""

from detail_forge.synthesis.coherence_engine import CoherenceEngine
from detail_forge.synthesis.one_click_generator import GenerationResult, OneClickGenerator
from detail_forge.synthesis.page_assembler import PageAssembler
from detail_forge.synthesis.section_compositor import SectionCompositor

__all__ = [
    "SectionCompositor",
    "CoherenceEngine",
    "PageAssembler",
    "OneClickGenerator",
    "GenerationResult",
]
