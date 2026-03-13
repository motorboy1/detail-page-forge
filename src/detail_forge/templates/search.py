"""Search and filter templates by D1000 principles."""

from __future__ import annotations

from detail_forge.templates.models import TemplateMetadata
from detail_forge.templates.store import TemplateStore


class TemplateSearcher:
    def __init__(self, store: TemplateStore) -> None:
        self.store = store

    def search(
        self,
        *,
        section_type: str | None = None,
        d1000_principles: list[int] | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        min_ssim: float = 0.0,
        limit: int = 20,
    ) -> list[TemplateMetadata]:
        """Search templates. Sorted by D1000 principle match count."""
        all_templates = self.store.list_templates(section_type)

        results = []
        for t in all_templates:
            if min_ssim and t.ssim_score < min_ssim:
                continue
            if category and t.category != category:
                continue
            if tags and not set(tags) & set(t.tags):
                continue
            results.append(t)

        if d1000_principles:
            principle_set = set(d1000_principles)
            results.sort(
                key=lambda t: len(set(t.d1000_principles) & principle_set),
                reverse=True,
            )

        return results[:limit]

    def recommend(
        self,
        selected_principles: list[int],
        *,
        section_type: str | None = None,
        category: str | None = None,
        limit: int = 6,
    ) -> list[TemplateMetadata]:
        """Smart recommendation based on D1000 principle overlap."""
        return self.search(
            section_type=section_type,
            d1000_principles=selected_principles,
            category=category,
            min_ssim=0.8,
            limit=limit,
        )
