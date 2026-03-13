"""Lecture transcript knowledge base for D1000 design principles.

Indexes and queries insights from lecture transcripts in
data/d1000_knowledge/lectures/ (or transcripts/).
Handles missing directories gracefully with empty results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LectureInsight:
    """An insight extracted from lecture transcripts."""

    principle_id: int
    insight_text: str
    source_lecture: str
    reasoning_prompt: str  # prompt for AI to apply this insight


# Default lecture directories — support both naming conventions
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # project root
_DEFAULT_LECTURE_DIRS = [
    _PROJECT_ROOT / "data" / "d1000_knowledge" / "lectures",
    _PROJECT_ROOT / "data" / "d1000_knowledge" / "transcripts",
]

_INDEX_FILENAME = "insights_index.json"


def _build_reasoning_prompt(principle_id: int, insight_text: str) -> str:
    """Build an AI reasoning prompt from the insight text."""
    return (
        f"D1000 원칙 #{principle_id}을 적용하여 상세페이지 디자인을 개선하세요.\n"
        f"핵심 인사이트: {insight_text[:200]}\n"
        f"이 원칙을 현재 섹션의 레이아웃과 카피에 구체적으로 적용하는 방법을 제안하세요."
    )


def _extract_insights_from_transcript(
    data: dict,
    source_name: str,
) -> list[LectureInsight]:
    """Extract LectureInsight objects from a single transcript JSON."""
    insights: list[LectureInsight] = []

    principle_id: int = data.get("d1000_principle_id", 0)
    topic: str = data.get("topic", "")
    text: str = data.get("text", "")

    if not principle_id or not text:
        return insights

    # Use topic as a brief summary, full text as reasoning source
    brief = topic if topic else text[:100]
    # Extract key sentence from text (first sentence-like chunk up to 200 chars)
    sentences = [s.strip() for s in text.replace(".", ".\n").split("\n") if len(s.strip()) > 20]
    insight_text = sentences[0] if sentences else brief

    reasoning_prompt = _build_reasoning_prompt(principle_id, insight_text)
    insights.append(
        LectureInsight(
            principle_id=principle_id,
            insight_text=insight_text,
            source_lecture=source_name,
            reasoning_prompt=reasoning_prompt,
        )
    )
    return insights


class LectureKnowledge:
    """Index and query design lecture insights mapped to D1000 principles."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        if data_dir is None:
            # Try default directories
            self._data_dir: Path | None = None
            for candidate in _DEFAULT_LECTURE_DIRS:
                if candidate.exists():
                    self._data_dir = candidate.resolve()
                    break
            # If none exist, use the first default (will return empty gracefully)
            if self._data_dir is None:
                self._data_dir = _DEFAULT_LECTURE_DIRS[0].resolve()
        else:
            self._data_dir = Path(data_dir).resolve()

        self._index_path = self._data_dir / _INDEX_FILENAME
        self._cache: list[LectureInsight] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_index(self) -> list[LectureInsight]:
        """Load lecture insight index.

        Returns an empty list if no data directory or transcripts exist.
        """
        if self._cache is not None:
            return self._cache

        # Try loading from pre-built index
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text(encoding="utf-8"))
                self._cache = [LectureInsight(**item) for item in data]
                return self._cache
            except (json.JSONDecodeError, TypeError, KeyError):
                pass  # Fall through to rebuild

        # Scan transcript JSON files
        if not self._data_dir or not self._data_dir.exists():
            self._cache = []
            return self._cache

        insights = self._scan_transcripts()
        self._cache = insights
        return self._cache

    def get_insights_for_principles(
        self, principle_ids: list[int]
    ) -> list[LectureInsight]:
        """Get relevant lecture insights for given D1000 principle IDs."""
        if not principle_ids:
            return []

        target_ids = set(principle_ids)
        return [
            insight
            for insight in self.load_index()
            if insight.principle_id in target_ids
        ]

    def get_reasoning_prompts(
        self, principle_ids: list[int]
    ) -> list[str]:
        """Get AI reasoning prompts derived from lecture knowledge."""
        insights = self.get_insights_for_principles(principle_ids)
        return [insight.reasoning_prompt for insight in insights]

    def save_index(self) -> None:
        """Persist the current index to insights_index.json."""
        insights = self.load_index()
        self._data_dir.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "principle_id": ins.principle_id,
                "insight_text": ins.insight_text,
                "source_lecture": ins.source_lecture,
                "reasoning_prompt": ins.reasoning_prompt,
            }
            for ins in insights
        ]
        self._index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scan_transcripts(self) -> list[LectureInsight]:
        """Walk data_dir for JSON transcript files and build insight index."""
        insights: list[LectureInsight] = []

        for path in sorted(self._data_dir.glob("*.json")):
            if path.name == _INDEX_FILENAME:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                extracted = _extract_insights_from_transcript(data, path.stem)
                insights.extend(extracted)
            except (json.JSONDecodeError, TypeError):
                continue  # Skip malformed files

        return insights
