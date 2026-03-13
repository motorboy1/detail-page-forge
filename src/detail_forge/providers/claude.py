"""Claude provider — uses Claude CLI subprocess for Max subscription."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from detail_forge.providers.base import (
    AIProviderBase,
    CopyRequest,
    CopyResponse,
    ImageRequest,
    ImageResponse,
)


def _call_claude(prompt: str, system: str = "", max_tokens: int = 4096) -> str:
    """Call Claude via CLI subprocess using Max subscription."""
    full_prompt = prompt
    if system:
        full_prompt = f"[System: {system}]\n\n{prompt}"

    env = {"PATH": "/home/motorboy/.local/bin:/usr/local/bin:/usr/bin:/bin", "HOME": str(Path.home())}
    result = subprocess.run(
        ["claude", "-p", full_prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr[:200]}")
    return result.stdout.strip()


class ClaudeProvider(AIProviderBase):
    """Claude provider using CLI subprocess — Claude Max subscription."""

    def __init__(self) -> None:
        self.model = "claude-max-cli"

    async def generate_copy(self, request: CopyRequest) -> CopyResponse:
        """Generate product detail page copy using Claude Max."""
        system_prompt = (
            "당신은 이커머스 상세페이지 전문 카피라이터입니다. "
            "한국 네이버 스마트스토어와 쿠팡에서 잘 팔리는 상세페이지의 카피를 작성합니다. "
            "톤앤매너는 경쟁사 레퍼런스와 유사하게 유지하면서, 더 설득력 있게 개선합니다."
        )

        user_prompt = f"""다음 상품의 상세페이지 '{request.section_type}' 섹션 카피를 작성해 주세요.

상품명: {request.product_name}
상품 특징:
{chr(10).join(f'- {f}' for f in request.product_features)}

섹션 타입: {request.section_type}
톤앤매너: {request.tone}

경쟁사 카피 레퍼런스:
{request.competitor_copy if request.competitor_copy else '(없음 - 자유롭게 작성)'}

다음 형식으로 응답해 주세요 (** 없이 플레인 텍스트, 다른 설명 없이):
헤드라인: (강렬한 한 줄)
서브헤드라인: (보조 설명)
본문: (2-3문장, 설득력 있게)
CTA: (행동 유도 문구)"""

        raw = _call_claude(user_prompt, system_prompt, 1024)
        return self._parse_copy_response(raw)

    async def generate_images(self, request: ImageRequest) -> ImageResponse:
        raise NotImplementedError("Claude does not support image generation.")

    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        """Analyze image using Claude's vision via CLI."""
        # Save image to temp file, reference in prompt
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(image_data)
            img_path = f.name

        try:
            full_prompt = f"{prompt}\n\n[Image at: {img_path}]"
            return _call_claude(full_prompt)
        finally:
            Path(img_path).unlink(missing_ok=True)

    def _parse_copy_response(self, raw: str) -> CopyResponse:
        """Parse structured copy from Claude's response."""
        # Strip MoAI formatting if present
        clean = re.sub(r'🤖.*?────+', '', raw, flags=re.DOTALL).strip()
        if not clean:
            clean = raw

        response = CopyResponse(raw_text=clean)
        lines = clean.strip().split("\n")

        label_re = re.compile(
            r"^\*{0,2}(헤드라인|서브헤드라인|본문|CTA)\s*[:：]\*{0,2}\s*(.+)",
            re.IGNORECASE,
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = label_re.match(line)
            if m:
                label = m.group(1)
                value = m.group(2).strip()
                if label == "헤드라인":
                    response.headline = value
                elif label == "서브헤드라인":
                    response.subheadline = value
                elif label == "본문":
                    response.body = value
                elif label == "CTA":
                    response.cta_text = value

        return response
