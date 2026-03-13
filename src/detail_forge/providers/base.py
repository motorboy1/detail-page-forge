"""Base classes for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CopyRequest:
    """Request for copywriting generation."""
    product_name: str
    product_features: list[str]
    section_type: str  # hero, features, benefits, testimonials, cta
    competitor_copy: str = ""
    tone: str = "professional"
    language: str = "ko"


@dataclass
class CopyResponse:
    """Response from copywriting generation."""
    headline: str = ""
    subheadline: str = ""
    body: str = ""
    cta_text: str = ""
    raw_text: str = ""


@dataclass
class ImageRequest:
    """Request for image generation."""
    prompt: str
    style_reference: str = ""
    width: int = 860
    height: int = 1200
    n: int = 3


@dataclass
class ImageResponse:
    """Response from image generation."""
    images: list[bytes] = field(default_factory=list)
    prompts_used: list[str] = field(default_factory=list)


class AIProviderBase(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate_copy(self, request: CopyRequest) -> CopyResponse:
        """Generate copywriting text."""
        ...

    @abstractmethod
    async def generate_images(self, request: ImageRequest) -> ImageResponse:
        """Generate images."""
        ...

    @abstractmethod
    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        """Analyze an image and return text description."""
        ...
