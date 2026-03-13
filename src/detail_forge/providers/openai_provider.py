"""OpenAI (GPT + DALL-E) provider."""

from __future__ import annotations

import base64

import openai

from detail_forge.config import get_settings
from detail_forge.providers.base import (
    AIProviderBase,
    CopyRequest,
    CopyResponse,
    ImageRequest,
    ImageResponse,
)


class OpenAIProvider(AIProviderBase):
    """OpenAI GPT/DALL-E provider — fallback for copy, option for images."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.chat_model = "gpt-4o"
        self.image_model = "dall-e-3"

    async def generate_copy(self, request: CopyRequest) -> CopyResponse:
        """Generate copy using GPT-4o."""
        system_prompt = (
            "당신은 이커머스 상세페이지 전문 카피라이터입니다. "
            "한국어로 설득력 있는 상세페이지 카피를 작성합니다."
        )

        user_prompt = f"""상품명: {request.product_name}
특징: {', '.join(request.product_features)}
섹션: {request.section_type}
경쟁사 카피: {request.competitor_copy or '(없음)'}

헤드라인, 서브헤드라인, 본문, CTA 형식으로 작성해 주세요."""

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
        )

        raw = response.choices[0].message.content or ""
        return CopyResponse(raw_text=raw, headline=raw.split("\n")[0] if raw else "")

    async def generate_images(self, request: ImageRequest) -> ImageResponse:
        """Generate images using DALL-E 3."""
        images: list[bytes] = []
        prompts_used: list[str] = []

        for i in range(request.n):
            response = self.client.images.generate(
                model=self.image_model,
                prompt=request.prompt,
                size="1024x1792",
                quality="hd",
                response_format="b64_json",
                n=1,
            )

            b64_data = response.data[0].b64_json or ""
            images.append(base64.b64decode(b64_data))
            prompts_used.append(response.data[0].revised_prompt or request.prompt)

        return ImageResponse(images=images, prompts_used=prompts_used)

    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        """Analyze image using GPT-4o vision."""
        b64 = base64.standard_b64encode(image_data).decode("utf-8")

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""
