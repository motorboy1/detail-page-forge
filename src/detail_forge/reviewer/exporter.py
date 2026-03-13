"""Multi-format exporter — Coupang images + Naver HTML + standalone HTML."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from detail_forge.config import get_settings
from detail_forge.copywriter.generator import CopyResult
from detail_forge.designer.generator import SectionDesign


@dataclass
class ExportResult:
    """Result of export operation."""
    output_dir: Path = Path(".")
    coupang_images: list[Path] = None
    naver_html_path: Path = Path(".")
    standalone_html_path: Path = Path(".")
    total_files: int = 0

    def __post_init__(self):
        if self.coupang_images is None:
            self.coupang_images = []


class Exporter:
    """Export finalized detail page in multiple formats."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def export_all(
        self,
        copy_result: CopyResult,
        designs: list[SectionDesign],
        output_name: str = "output",
    ) -> ExportResult:
        """Export to all formats."""
        output_dir = self.settings.output_dir / output_name
        output_dir.mkdir(parents=True, exist_ok=True)

        result = ExportResult(output_dir=output_dir)

        # 1. Coupang image set
        result.coupang_images = self._export_coupang_images(designs, output_dir / "coupang")

        # 2. Naver Smart Store HTML
        result.naver_html_path = self._export_naver_html(copy_result, designs, output_dir / "naver")

        # 3. Standalone responsive HTML
        result.standalone_html_path = self._export_standalone_html(
            copy_result, designs, output_dir / "standalone"
        )

        # 4. Save copy data as JSON
        copy_json = output_dir / "copy_data.json"
        copy_json.write_text(json.dumps(copy_result.to_dict(), ensure_ascii=False, indent=2))

        result.total_files = (
            len(result.coupang_images) + 2 + 1  # coupang + naver + standalone + json
        )
        return result

    def _export_coupang_images(
        self, designs: list[SectionDesign], output_dir: Path
    ) -> list[Path]:
        """Export individual section images optimized for Coupang upload."""
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []

        for design in designs:
            img_data = design.selected_image
            if not img_data:
                continue

            img = Image.open(io.BytesIO(img_data))

            # Resize to Coupang standard width
            target_w = self.settings.coupang_image_width
            ratio = target_w / img.width
            target_h = int(img.height * ratio)
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # Save as JPEG for smaller file size
            path = output_dir / f"section_{design.section_index:02d}_{design.section_type}.jpg"
            img.convert("RGB").save(path, "JPEG", quality=90, optimize=True)
            paths.append(path)

        return paths

    def _export_naver_html(
        self,
        copy_result: CopyResult,
        designs: list[SectionDesign],
        output_dir: Path,
    ) -> Path:
        """Export as Naver Smart Store compatible HTML."""
        output_dir.mkdir(parents=True, exist_ok=True)
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Save images
        img_tags = []
        for design in designs:
            img_data = design.selected_image
            if not img_data:
                continue

            img_name = f"section_{design.section_index:02d}.jpg"
            img_path = images_dir / img_name
            img = Image.open(io.BytesIO(img_data))
            img.convert("RGB").save(img_path, "JPEG", quality=90)
            img_tags.append(f'<img src="images/{img_name}" alt="{design.section_type}" style="width:100%;display:block;">')

        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{copy_result.product.name} - 상세페이지</title>
<style>
body {{ margin: 0; padding: 0; background: #fff; }}
.detail-page {{ max-width: 860px; margin: 0 auto; }}
.detail-page img {{ width: 100%; display: block; }}
</style>
</head>
<body>
<div class="detail-page">
{chr(10).join(img_tags)}
</div>
</body>
</html>"""

        html_path = output_dir / "index.html"
        html_path.write_text(html, encoding="utf-8")
        return html_path

    def _export_standalone_html(
        self,
        copy_result: CopyResult,
        designs: list[SectionDesign],
        output_dir: Path,
    ) -> Path:
        """Export as standalone responsive HTML with embedded images."""
        output_dir.mkdir(parents=True, exist_ok=True)
        import base64

        sections_html = []
        for i, (design, copy_section) in enumerate(
            zip(designs, copy_result.sections)
        ):
            img_data = design.selected_image
            if not img_data:
                continue

            b64 = base64.b64encode(img_data).decode("utf-8")
            sections_html.append(f"""
<section class="detail-section" id="section-{i}">
  <div class="section-image">
    <img src="data:image/png;base64,{b64}" alt="{copy_section.section_type}">
  </div>
  <div class="section-text">
    <h2>{copy_section.headline}</h2>
    <h3>{copy_section.subheadline}</h3>
    <p>{copy_section.body}</p>
    {f'<a href="#" class="cta-button">{copy_section.cta_text}</a>' if copy_section.cta_text else ''}
  </div>
</section>""")

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{copy_result.product.name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Noto Sans KR', -apple-system, sans-serif; background: #f5f5f5; color: #333; }}
.detail-page {{ max-width: 860px; margin: 0 auto; background: #fff; }}
.detail-section {{ position: relative; }}
.section-image img {{ width: 100%; display: block; }}
.section-text {{
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 40px 30px; background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: #fff;
}}
.section-text h2 {{ font-size: 28px; margin-bottom: 8px; }}
.section-text h3 {{ font-size: 18px; font-weight: 400; margin-bottom: 12px; opacity: 0.9; }}
.section-text p {{ font-size: 15px; line-height: 1.6; opacity: 0.85; }}
.cta-button {{
  display: inline-block; margin-top: 16px; padding: 12px 32px;
  background: #ff6b35; color: #fff; text-decoration: none;
  border-radius: 6px; font-weight: 700; font-size: 16px;
}}
@media (max-width: 600px) {{
  .section-text h2 {{ font-size: 20px; }}
  .section-text h3 {{ font-size: 14px; }}
  .section-text p {{ font-size: 13px; }}
  .section-text {{ padding: 20px 16px; }}
}}
</style>
</head>
<body>
<div class="detail-page">
{chr(10).join(sections_html)}
</div>
</body>
</html>"""

        html_path = output_dir / "index.html"
        html_path.write_text(html, encoding="utf-8")
        return html_path
