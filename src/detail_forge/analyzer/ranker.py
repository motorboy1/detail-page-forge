"""Competitor ranker — rank and combine best sections."""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.analyzer.parser import ParsedPage, Section


@dataclass
class RankedTemplate:
    """Combined template with best sections from all competitors."""
    sections: list[Section] = field(default_factory=list)
    source_pages: list[ParsedPage] = field(default_factory=list)


class CompetitorRanker:
    """Rank competitors and combine best sections into a template."""

    def rank_and_combine(self, parsed_pages: list[ParsedPage]) -> RankedTemplate:
        """Take parsed competitor pages, return combined best-of template."""
        if not parsed_pages:
            return RankedTemplate()

        # Sort pages by overall score
        sorted_pages = sorted(parsed_pages, key=lambda p: p.overall_score, reverse=True)

        # Use #1 page as skeleton
        skeleton = sorted_pages[0]
        best_sections: list[Section] = list(skeleton.sections)

        # For each section type, check if another page has a stronger version
        section_types_seen: set[str] = set()
        for section in best_sections:
            section_types_seen.add(section.section_type)

        # Collect best-scoring sections from other pages for types we already have
        for page in sorted_pages[1:]:
            for section in page.sections:
                # Find matching section in our template
                for i, existing in enumerate(best_sections):
                    if (
                        existing.section_type == section.section_type
                        and section.strength_score > existing.strength_score
                    ):
                        best_sections[i] = section
                        break

        # Add unique section types from other pages
        for page in sorted_pages[1:]:
            for section in page.sections:
                if section.section_type not in section_types_seen and section.strength_score >= 7:
                    best_sections.append(section)
                    section_types_seen.add(section.section_type)

        return RankedTemplate(sections=best_sections, source_pages=sorted_pages)
