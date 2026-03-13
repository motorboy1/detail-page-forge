"""AI image generator — Gemini-powered product images for detail pages."""

from __future__ import annotations

import base64
from dataclasses import dataclass


@dataclass
class GeneratedImage:
    """A generated product image."""
    section_type: str = ""
    prompt: str = ""
    image_data: bytes = b""
    mime_type: str = "image/png"
    error: str = ""

    @property
    def data_uri(self) -> str:
        if not self.image_data:
            return ""
        b64 = base64.b64encode(self.image_data).decode()
        return f"data:{self.mime_type};base64,{b64}"


# Section-specific image prompts
IMAGE_PROMPTS = {
    "hero": "Professional studio product photo, {product}, center frame, dramatic lighting, premium feel, white and warm background, e-commerce hero shot, high resolution",
    "benefits": "Lifestyle product photo, {product} being used in modern Korean kitchen, warm natural lighting, cozy atmosphere, editorial style",
    "specs": "Detail close-up shot of {product}, showing material texture and craftsmanship, macro photography, clean background",
}


def generate_section_images(
    product_name: str,
    section_types: list[str],
    api_key: str,
) -> dict[str, GeneratedImage]:
    """Generate images for specified sections using Gemini."""
    results: dict[str, GeneratedImage] = {}

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
    except Exception as e:
        for st in section_types:
            results[st] = GeneratedImage(section_type=st, error=f"Gemini init failed: {e}")
        return results

    for section_type in section_types:
        if section_type not in IMAGE_PROMPTS:
            continue

        prompt = IMAGE_PROMPTS[section_type].format(product=product_name)
        img = GeneratedImage(section_type=section_type, prompt=prompt)

        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=f"Generate this image: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    img.image_data = part.inline_data.data
                    img.mime_type = part.inline_data.mime_type or "image/png"
                    break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                img.error = "quota_exhausted"
            else:
                img.error = str(e)[:100]

        results[section_type] = img

    return results
