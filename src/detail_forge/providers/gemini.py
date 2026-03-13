"""Google Gemini provider — primary for image generation."""

from __future__ import annotations

import base64

from google import genai
from google.genai import types

from detail_forge.config import get_settings
from detail_forge.providers.base import (
    AIProviderBase,
    CopyRequest,
    CopyResponse,
    ImageRequest,
    ImageResponse,
)


class GeminiProvider(AIProviderBase):
    """Google Gemini provider — primary image generation."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_api_key)
        self.text_model = "gemini-2.0-flash"
        self.image_model = "gemini-2.0-flash-preview-image-generation"

    async def generate_copy(self, request: CopyRequest) -> CopyResponse:
        """Generate copy using Gemini (fallback)."""
        prompt = f"""상품명: {request.product_name}
특징: {', '.join(request.product_features)}
섹션: {request.section_type}
경쟁사 카피: {request.competitor_copy or '(없음)'}

이커머스 상세페이지용 카피를 작성해 주세요.
헤드라인, 서브헤드라인, 본문, CTA 형식으로."""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=prompt,
        )
        raw = response.text or ""
        return CopyResponse(raw_text=raw, headline=raw.split("\n")[0] if raw else "")

    async def generate_images(self, request: ImageRequest) -> ImageResponse:
        """Generate images using Gemini's image generation."""
        images: list[bytes] = []
        prompts_used: list[str] = []

        for _ in range(request.n):
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=request.prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    images.append(part.inline_data.data)
                    prompts_used.append(request.prompt)

        return ImageResponse(images=images, prompts_used=prompts_used)

    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        """Analyze image using Gemini vision."""
        b64 = base64.standard_b64encode(image_data).decode("utf-8")

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type="image/png"),
                prompt,
            ],
        )
        return response.text or ""
