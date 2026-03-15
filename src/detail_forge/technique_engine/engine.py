"""Technique Engine — decision engine for automatic technique selection.

Takes product info + context → selects atomic techniques → resolves conflicts →
returns a TechniqueResult ready for rendering.

Fully deterministic, no AI calls.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from detail_forge.copywriter.generator import ProductInfo

# ─── Data paths ──────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "technique_system"
_ATOMS_PATH = _DATA_DIR / "technique_atoms.json"
_COMPOUNDS_PATH = _DATA_DIR / "technique_compounds.json"
_WORKFLOWS_PATH = _DATA_DIR / "technique_workflows.json"


# ─── Data models ─────────────────────────────────────────────────────


@dataclass
class AtomicTechnique:
    """A single executable design technique."""

    id: str
    name: str
    name_en: str
    category: str
    source: str
    rule: str
    why: str
    css: dict
    applies_when: list[str]
    conflicts_with: list[str]
    composable_with: list[str]
    parameters: dict
    intensity: str
    mood: list[str]

    @classmethod
    def from_dict(cls, d: dict) -> AtomicTechnique:
        return cls(
            id=d["id"],
            name=d["name"],
            name_en=d["name_en"],
            category=d["category"],
            source=d["source"],
            rule=d["rule"],
            why=d["why"],
            css=d.get("css", {}),
            applies_when=d.get("applies_when", []),
            conflicts_with=d.get("conflicts_with", []),
            composable_with=d.get("composable_with", []),
            parameters=d.get("parameters", {}),
            intensity=d.get("intensity", "moderate"),
            mood=d.get("mood", []),
        )


@dataclass
class CompoundPattern:
    """A pre-defined combination of atomic techniques."""

    id: str
    name: str
    name_en: str
    description: str
    atoms: list[str]
    category: str
    applies_when: list[str]
    mood: list[str]
    section_type: str

    @classmethod
    def from_dict(cls, d: dict) -> CompoundPattern:
        return cls(
            id=d["id"],
            name=d["name"],
            name_en=d["name_en"],
            description=d["description"],
            atoms=d["atoms"],
            category=d["category"],
            applies_when=d.get("applies_when", []),
            mood=d.get("mood", []),
            section_type=d.get("section_type", ""),
        )


@dataclass
class WorkflowSection:
    """One section within a workflow definition."""

    section_order: int
    section_type: str
    compound_id: str
    role: str
    height_vh: int


@dataclass
class WorkflowDefinition:
    """A full-page workflow combining compounds into a page structure."""

    id: str
    name: str
    name_en: str
    description: str
    target_categories: list[str]
    target_audience: list[str]
    page_structure: list[WorkflowSection]
    foundation_compounds: list[str]
    mood_flow: list[str]
    estimated_scroll_depth: str

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowDefinition:
        sections = [
            WorkflowSection(
                section_order=s["section_order"],
                section_type=s["section_type"],
                compound_id=s["compound_id"],
                role=s["role"],
                height_vh=s["height_vh"],
            )
            for s in d["page_structure"]
        ]
        return cls(
            id=d["id"],
            name=d["name"],
            name_en=d["name_en"],
            description=d["description"],
            target_categories=d.get("target_categories", []),
            target_audience=d.get("target_audience", []),
            page_structure=sections,
            foundation_compounds=d.get("foundation_compounds", []),
            mood_flow=d.get("mood_flow", []),
            estimated_scroll_depth=d.get("estimated_scroll_depth", "medium"),
        )


@dataclass
class TechniqueResult:
    """Output of TechniqueEngine.select().

    Contains the resolved set of techniques ready for rendering.

    Attributes:
        workflow: The selected workflow definition.
        section_techniques: Per-section resolved atomic techniques.
        foundation_atoms: Foundation-layer atomic techniques (always applied).
        all_atoms: Flat list of all unique atomic techniques selected.
        mood_profile: Aggregated mood tags for the entire page.
        conflicts_resolved: List of conflict resolutions made.
    """

    workflow: WorkflowDefinition
    section_techniques: list[SectionTechniques]
    foundation_atoms: list[AtomicTechnique]
    all_atoms: list[AtomicTechnique]
    mood_profile: list[str]
    conflicts_resolved: list[str] = field(default_factory=list)


@dataclass
class SectionTechniques:
    """Resolved techniques for a single page section."""

    section_order: int
    section_type: str
    compound: CompoundPattern
    atoms: list[AtomicTechnique]
    role: str
    height_vh: int


# ─── Category mapping for product matching ───────────────────────────

_CATEGORY_ALIASES: dict[str, list[str]] = {
    "electronics": ["전자", "가전", "디지털", "IT", "테크", "tech", "gadget"],
    "food": ["식품", "음식", "건강식품", "간식", "음료", "푸드"],
    "beauty": ["뷰티", "화장품", "코스메틱", "스킨케어", "향수"],
    "fashion": ["패션", "의류", "가방", "신발", "악세서리", "주얼리"],
    "health": ["건강", "헬스", "운동", "피트니스", "보충제", "영양제"],
    "lifestyle": ["생활", "리빙", "인테리어", "가구", "소품"],
    "luxury": ["럭셔리", "프리미엄", "명품", "하이엔드"],
    "tech": ["앱", "SaaS", "소프트웨어", "플랫폼", "API"],
}

_MOOD_KEYWORDS: dict[str, list[str]] = {
    "프리미엄": ["luxury", "premium", "elegant"],
    "미니멀": ["minimal", "clean", "elegant"],
    "모던": ["modern", "sophisticated"],
    "따뜻한": ["warm", "authentic", "organic"],
    "트렌디": ["bold", "hip", "modern"],
    "감성적": ["emotional", "warm", "narrative"],
    "시네마틱": ["cinematic", "dramatic", "immersive"],
    "캐주얼": ["playful", "youthful", "energetic"],
    "전문적": ["professional", "technical", "trustworthy"],
    "레트로": ["retro", "vintage", "nostalgic"],
}


class TechniqueEngine:
    """Selects and resolves design techniques based on product context.

    Usage::

        engine = TechniqueEngine()
        result = engine.select(
            product=product_info,
            category="beauty",
            style_keywords=["프리미엄", "미니멀"],
        )
    """

    def __init__(self) -> None:
        self._atoms: dict[str, AtomicTechnique] = {}
        self._compounds: dict[str, CompoundPattern] = {}
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load all technique data from JSON files."""
        if _ATOMS_PATH.exists():
            with open(_ATOMS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("techniques", []):
                atom = AtomicTechnique.from_dict(item)
                self._atoms[atom.id] = atom

        if _COMPOUNDS_PATH.exists():
            with open(_COMPOUNDS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("compounds", []):
                compound = CompoundPattern.from_dict(item)
                self._compounds[compound.id] = compound

        if _WORKFLOWS_PATH.exists():
            with open(_WORKFLOWS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("workflows", []):
                workflow = WorkflowDefinition.from_dict(item)
                self._workflows[workflow.id] = workflow

    # ─── Public API ──────────────────────────────────────────────────

    def select(
        self,
        product: ProductInfo,
        category: str | None = None,
        style_keywords: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> TechniqueResult:
        """Select the best technique combination for a product.

        Args:
            product: ProductInfo with name, features, target_audience, etc.
            category: Product category (e.g. 'beauty', 'electronics').
                      If None, inferred from product features.
            style_keywords: Korean style keywords (e.g. ['프리미엄', '미니멀']).
            workflow_id: Explicit workflow ID to use. If None, auto-selected.

        Returns:
            TechniqueResult with resolved techniques per section.
        """
        # Step 1: Resolve category
        resolved_category = category or self._infer_category(product)

        # Step 2: Build target mood profile
        target_moods = self._build_mood_profile(style_keywords or [])

        # Step 3: Select workflow
        workflow = self._select_workflow(
            workflow_id, resolved_category, target_moods
        )

        # Step 4: Resolve foundation atoms
        foundation_atoms = self._resolve_foundation_atoms(workflow)

        # Step 5: Resolve per-section techniques
        section_techniques, conflicts = self._resolve_sections(workflow, target_moods)

        # Step 6: Collect all unique atoms
        all_atom_ids: set[str] = {a.id for a in foundation_atoms}
        for st in section_techniques:
            for a in st.atoms:
                all_atom_ids.add(a.id)
        all_atoms = [self._atoms[aid] for aid in all_atom_ids if aid in self._atoms]

        # Step 7: Aggregate mood profile
        mood_profile = list(dict.fromkeys(
            workflow.mood_flow + target_moods
        ))

        return TechniqueResult(
            workflow=workflow,
            section_techniques=section_techniques,
            foundation_atoms=foundation_atoms,
            all_atoms=all_atoms,
            mood_profile=mood_profile,
            conflicts_resolved=conflicts,
        )

    def list_workflows(self) -> list[WorkflowDefinition]:
        """Return all available workflow definitions."""
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Get a specific workflow by ID."""
        return self._workflows.get(workflow_id)

    def get_compound(self, compound_id: str) -> CompoundPattern | None:
        """Get a specific compound pattern by ID."""
        return self._compounds.get(compound_id)

    def get_atom(self, atom_id: str) -> AtomicTechnique | None:
        """Get a specific atomic technique by ID."""
        return self._atoms.get(atom_id)

    # ─── Private: Category inference ─────────────────────────────────

    def _infer_category(self, product: ProductInfo) -> str:
        """Infer product category from product info text fields."""
        searchable = " ".join([
            product.name,
            " ".join(product.features),
            product.target_audience,
        ]).lower()

        best_category = "lifestyle"
        best_score = 0

        for category, aliases in _CATEGORY_ALIASES.items():
            score = sum(1 for alias in aliases if alias.lower() in searchable)
            if score > best_score:
                best_score = score
                best_category = category

        return best_category

    # ─── Private: Mood profile ───────────────────────────────────────

    def _build_mood_profile(self, style_keywords: list[str]) -> list[str]:
        """Convert Korean style keywords to mood tags."""
        moods: list[str] = []
        for kw in style_keywords:
            moods.extend(_MOOD_KEYWORDS.get(kw, []))
        return list(dict.fromkeys(moods))

    # ─── Private: Workflow selection ─────────────────────────────────

    def _select_workflow(
        self,
        explicit_id: str | None,
        category: str,
        target_moods: list[str],
    ) -> WorkflowDefinition:
        """Select the best workflow for the given context."""
        if explicit_id and explicit_id in self._workflows:
            return self._workflows[explicit_id]

        best_workflow: WorkflowDefinition | None = None
        best_score = -1

        for wf in self._workflows.values():
            score = 0

            # Category match
            if category in wf.target_categories:
                score += 3

            # Mood overlap
            mood_overlap = len(set(wf.mood_flow) & set(target_moods))
            score += mood_overlap

            if score > best_score:
                best_score = score
                best_workflow = wf

        # Fallback to storytelling conversion (most versatile)
        if best_workflow is None:
            best_workflow = self._workflows.get(
                "workflow_storytelling_conversion",
                next(iter(self._workflows.values())),
            )

        return best_workflow

    # ─── Private: Foundation resolution ──────────────────────────────

    def _resolve_foundation_atoms(
        self, workflow: WorkflowDefinition
    ) -> list[AtomicTechnique]:
        """Resolve foundation-layer atomic techniques from foundation compounds."""
        atoms: list[AtomicTechnique] = []
        seen: set[str] = set()

        for compound_id in workflow.foundation_compounds:
            compound = self._compounds.get(compound_id)
            if not compound:
                continue
            for atom_id in compound.atoms:
                if atom_id not in seen and atom_id in self._atoms:
                    atoms.append(self._atoms[atom_id])
                    seen.add(atom_id)

        return atoms

    # ─── Private: Section resolution ─────────────────────────────────

    def _resolve_sections(
        self,
        workflow: WorkflowDefinition,
        target_moods: list[str],
    ) -> tuple[list[SectionTechniques], list[str]]:
        """Resolve techniques for each section, handling conflicts."""
        section_techniques: list[SectionTechniques] = []
        conflicts_resolved: list[str] = []
        used_atoms: set[str] = set()

        for section in workflow.page_structure:
            compound = self._compounds.get(section.compound_id)
            if not compound:
                continue

            # Resolve atoms for this compound
            resolved_atoms: list[AtomicTechnique] = []
            for atom_id in compound.atoms:
                atom = self._atoms.get(atom_id)
                if not atom:
                    continue

                # Check for conflicts with already selected atoms
                conflict = self._check_conflict(atom, resolved_atoms)
                if conflict:
                    conflicts_resolved.append(
                        f"Section {section.section_order} ({section.section_type}): "
                        f"'{atom.name}' conflicts with '{conflict.name}', skipped"
                    )
                    continue

                resolved_atoms.append(atom)
                used_atoms.add(atom_id)

            section_techniques.append(
                SectionTechniques(
                    section_order=section.section_order,
                    section_type=section.section_type,
                    compound=compound,
                    atoms=resolved_atoms,
                    role=section.role,
                    height_vh=section.height_vh,
                )
            )

        return section_techniques, conflicts_resolved

    def _check_conflict(
        self,
        candidate: AtomicTechnique,
        existing: list[AtomicTechnique],
    ) -> AtomicTechnique | None:
        """Check if candidate conflicts with any existing atom.

        Returns the conflicting atom, or None if no conflict.
        """
        for atom in existing:
            if atom.id in candidate.conflicts_with:
                return atom
            if candidate.id in atom.conflicts_with:
                return atom
        return None
