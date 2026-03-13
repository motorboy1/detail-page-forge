"""Data models for the template library."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SlotMapping:
    """Maps semantic CopyResult fields to positional data-slot names."""

    headline: str | None = None        # e.g. "text_0"
    subheadline: str | None = None     # e.g. "text_1"
    body: list[str] = field(default_factory=list)  # e.g. ["text_2", "text_3"]
    cta_text: str | None = None        # e.g. "text_5"
    product_image: str | None = None   # e.g. "img_0"
    background_image: str | None = None  # e.g. "bg_0"
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "headline": self.headline,
            "subheadline": self.subheadline,
            "body": self.body,
            "cta_text": self.cta_text,
            "product_image": self.product_image,
            "background_image": self.background_image,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SlotMapping:
        return cls(
            headline=d.get("headline"),
            subheadline=d.get("subheadline"),
            body=d.get("body", []),
            cta_text=d.get("cta_text"),
            product_image=d.get("product_image"),
            background_image=d.get("background_image"),
            extra=d.get("extra", {}),
        )


@dataclass
class TemplateMetadata:
    """Metadata for a single template entry."""

    id: str = ""                          # slug, e.g. "tamburins-hero-01"
    name: str = ""                        # display name
    section_type: str = "full_page"       # hero|features|benefits|...|full_page
    d1000_principles: list[int] = field(default_factory=list)
    category: str = "general"             # beauty|food|electronics|fashion|...
    source_url: str = ""
    ssim_score: float = 0.0
    slot_count: int = 0
    thumbnail_path: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "section_type": self.section_type,
            "d1000_principles": self.d1000_principles,
            "category": self.category,
            "source_url": self.source_url,
            "ssim_score": self.ssim_score,
            "slot_count": self.slot_count,
            "thumbnail_path": self.thumbnail_path,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TemplateMetadata:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TemplateIndex:
    """Catalog of all templates."""

    version: int = 1
    templates: list[TemplateMetadata] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "templates": [t.to_dict() for t in self.templates],
        }

    @classmethod
    def from_dict(cls, d: dict) -> TemplateIndex:
        return cls(
            version=d.get("version", 1),
            templates=[TemplateMetadata.from_dict(t) for t in d.get("templates", [])],
        )
