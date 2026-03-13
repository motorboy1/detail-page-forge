"""Pinterest reference image library for D1000-tagged design references.

Indexes and searches Pinterest reference images from data/d1000_knowledge/pinterest/.
Handles missing directories gracefully with empty results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReferenceImage:
    """A Pinterest reference image with D1000 metadata."""

    file_path: str
    category: str  # food, electronics, fashion, beauty, health, lifestyle
    d1000_principles: list[int] = field(default_factory=list)
    style_keywords: list[str] = field(default_factory=list)
    source_url: str = ""


_DEFAULT_PINTEREST_DIR = (
    Path(__file__).parent.parent.parent.parent  # src/
    / ".."  # project root
    / "data"
    / "d1000_knowledge"
    / "pinterest"
)

# Mapping known categories to common D1000 principles (heuristic seed)
_CATEGORY_PRINCIPLES: dict[str, list[int]] = {
    "food": [1, 3, 7, 15, 22],
    "electronics": [2, 5, 11, 18, 30],
    "fashion": [1, 4, 8, 16, 21],
    "beauty": [3, 6, 9, 17, 25],
    "health": [2, 7, 12, 20, 28],
    "lifestyle": [1, 5, 10, 19, 27],
}

_KNOWN_CATEGORIES = list(_CATEGORY_PRINCIPLES.keys())


def _infer_category(file_path: str) -> str:
    """Infer category from file path or name."""
    path_lower = file_path.lower()
    for cat in _KNOWN_CATEGORIES:
        if cat in path_lower:
            return cat
    return "lifestyle"


def _infer_style_keywords(file_path: str, category: str) -> list[str]:
    """Infer style keywords from file name."""
    keywords: list[str] = [category]
    name = Path(file_path).stem.lower()
    # Common visual keywords
    for kw in ("minimal", "bold", "luxury", "natural", "clean", "vibrant", "soft", "dark", "light"):
        if kw in name:
            keywords.append(kw)
    return keywords


class ReferenceLibrary:
    """Index and search D1000-tagged Pinterest reference images."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        if data_dir is None:
            self._data_dir = _DEFAULT_PINTEREST_DIR.resolve()
        else:
            self._data_dir = Path(data_dir).resolve()
        self._index_path = self._data_dir / "index.json"
        self._cache: list[ReferenceImage] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_index(self) -> list[ReferenceImage]:
        """Load or build the reference image index.

        Returns an empty list if the directory does not exist yet.
        """
        if self._cache is not None:
            return self._cache

        # Try loading from pre-built index.json first
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text(encoding="utf-8"))
                self._cache = [ReferenceImage(**item) for item in data]
                return self._cache
            except (json.JSONDecodeError, TypeError, KeyError):
                pass  # Fall through to rebuild

        # Scan directory if it exists
        if not self._data_dir.exists():
            self._cache = []
            return self._cache

        images = self._scan_directory()
        self._cache = images
        return self._cache

    def search(
        self,
        category: str | None = None,
        d1000_principles: list[int] | None = None,
        style_keywords: list[str] | None = None,
        limit: int = 20,
    ) -> list[ReferenceImage]:
        """Search references by category, principles, or keywords.

        All provided filters are applied as AND conditions.
        """
        results = self.load_index()

        if category:
            results = [r for r in results if r.category.lower() == category.lower()]

        if d1000_principles:
            principle_set = set(d1000_principles)
            results = [r for r in results if principle_set.intersection(r.d1000_principles)]

        if style_keywords:
            kw_set = {k.lower() for k in style_keywords}
            results = [
                r for r in results
                if kw_set.intersection({k.lower() for k in r.style_keywords})
            ]

        return results[:limit]

    def recommend_for_product(
        self,
        product_category: str,
        style_keyword: str = "",
    ) -> list[ReferenceImage]:
        """Recommend reference images for a product category.

        Returns up to 10 relevant references.
        """
        principles = _CATEGORY_PRINCIPLES.get(product_category.lower(), [])
        keywords = [style_keyword] if style_keyword else None

        results = self.search(
            category=product_category,
            d1000_principles=principles if principles else None,
            style_keywords=keywords,
            limit=10,
        )

        # If no category match, try principle-only
        if not results and principles:
            results = self.search(
                d1000_principles=principles,
                style_keywords=keywords,
                limit=10,
            )

        return results

    def save_index(self) -> None:
        """Persist the current index to index.json."""
        images = self.load_index()
        self._data_dir.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "file_path": img.file_path,
                "category": img.category,
                "d1000_principles": img.d1000_principles,
                "style_keywords": img.style_keywords,
                "source_url": img.source_url,
            }
            for img in images
        ]
        self._index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scan_directory(self) -> list[ReferenceImage]:
        """Walk the data directory and build index from image files."""
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        images: list[ReferenceImage] = []

        for path in sorted(self._data_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in image_extensions:
                rel_path = str(path.relative_to(self._data_dir))
                category = _infer_category(rel_path)
                keywords = _infer_style_keywords(rel_path, category)
                principles = _CATEGORY_PRINCIPLES.get(category, [])
                images.append(
                    ReferenceImage(
                        file_path=rel_path,
                        category=category,
                        d1000_principles=principles,
                        style_keywords=keywords,
                        source_url="",
                    )
                )

        return images
