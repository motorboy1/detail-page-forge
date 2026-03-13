"""AI image generator for detail page sections."""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.config import get_settings
from detail_forge.copywriter.generator import SectionCopy
from detail_forge.providers.base import AIProviderBase, ImageRequest

SECTION_STYLE_PROMPTS = {
    "hero": (
        "E-commerce product detail page hero banner section. "
        "Clean, professional Korean style. Large product image centered. "
        "Warm, inviting color scheme. Premium feel. "
        "NO text in the image — text will be overlaid separately. "
        "White or light gradient background. {product_context}"
    ),
    "features": (
        "E-commerce product feature section with icon-style layout. "
        "Clean grid or split layout. Visual icons representing product features. "
        "Modern Korean e-commerce style. NO text in image. {product_context}"
    ),
    "benefits": (
        "Product benefit showcase section. Lifestyle photography style. "
        "Show the product being used in a cozy setting. "
        "Warm lighting, Korean home aesthetic. NO text. {product_context}"
    ),
    "testimonials": (
        "Customer review section background. Clean, trustworthy design. "
        "Star ratings visual, satisfied customer imagery. "
        "Korean e-commerce review section style. NO text. {product_context}"
    ),
    "specs": (
        "Product specification section. Technical diagram style. "
        "Clean infographic layout with measurement visuals. "
        "Professional, detailed. NO text. {product_context}"
    ),
    "cta": (
        "Call-to-action section for e-commerce. "
        "Attention-grabbing, warm colors. Product beauty shot. "
        "Korean shopping style, premium feel. NO text. {product_context}"
    ),
    "guarantee": (
        "Trust and guarantee section. Clean badge/seal design. "
        "Quality assurance visuals. Professional and trustworthy. "
        "Korean e-commerce style. NO text. {product_context}"
    ),
    "social_proof": (
        "Social proof section showing popularity. "
        "Sales numbers visualization, award badges. "
        "Korean marketplace bestseller style. NO text. {product_context}"
    ),
}


@dataclass
class ImageCandidate:
    """A candidate image for a section."""
    index: int = 0
    image_data: bytes = b""
    prompt_used: str = ""
    selected: bool = False


@dataclass
class SectionDesign:
    """Design candidates for a single section."""
    section_index: int = 0
    section_type: str = ""
    copy: SectionCopy | None = None
    candidates: list[ImageCandidate] = field(default_factory=list)
    selected_index: int = -1  # -1 = not yet selected

    @property
    def selected_image(self) -> bytes | None:
        """Return the selected image data."""
        if 0 <= self.selected_index < len(self.candidates):
            return self.candidates[self.selected_index].image_data
        return None


class ImageGenerator:
    """Generate image candidates for each section."""

    def __init__(self, provider: AIProviderBase) -> None:
        self.provider = provider
        self.settings = get_settings()

    async def generate_section(
        self, copy: SectionCopy, product_context: str = ""
    ) -> SectionDesign:
        """Generate image candidates for a single section."""
        style_template = SECTION_STYLE_PROMPTS.get(
            copy.section_type,
            SECTION_STYLE_PROMPTS["features"],
        )
        prompt = style_template.format(product_context=product_context)

        request = ImageRequest(
            prompt=prompt,
            width=self.settings.image_width,
            height=self.settings.image_height,
            n=self.settings.candidates_per_section,
        )

        response = await self.provider.generate_images(request)

        candidates = [
            ImageCandidate(
                index=i,
                image_data=img,
                prompt_used=response.prompts_used[i] if i < len(response.prompts_used) else prompt,
            )
            for i, img in enumerate(response.images)
        ]

        return SectionDesign(
            section_index=copy.section_index,
            section_type=copy.section_type,
            copy=copy,
            candidates=candidates,
        )

    async def regenerate_section(
        self, design: SectionDesign, custom_prompt: str | None = None
    ) -> SectionDesign:
        """Regenerate candidates for a section with optional custom prompt."""
        prompt = custom_prompt or SECTION_STYLE_PROMPTS.get(
            design.section_type, SECTION_STYLE_PROMPTS["features"]
        )

        request = ImageRequest(
            prompt=prompt,
            width=self.settings.image_width,
            height=self.settings.image_height,
            n=self.settings.candidates_per_section,
        )

        response = await self.provider.generate_images(request)

        new_candidates = [
            ImageCandidate(
                index=i,
                image_data=img,
                prompt_used=response.prompts_used[i] if i < len(response.prompts_used) else prompt,
            )
            for i, img in enumerate(response.images)
        ]

        design.candidates = new_candidates
        design.selected_index = -1
        return design
