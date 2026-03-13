"""Export manager — packages rendered outputs into downloadable ZIP archives.

File structure inside ZIP:
  {product_name}/
    coupang/
      image_01.png
      image_02.png
      ...
    naver/
      index.html
    web/
      index.html
    metadata.json
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ExportPackage:
    """Result of an export operation."""

    zip_bytes: bytes
    file_count: int
    total_size_bytes: int
    manifest: dict[str, str] = field(default_factory=dict)


def _sanitize_name(name: str) -> str:
    """Sanitize a product name for use as a directory name inside a ZIP."""
    # Replace path separators and other dangerous chars with underscores
    sanitized = re.sub(r'[/\\:*?"<>|]', "_", name)
    # Collapse runs of whitespace/underscores
    sanitized = re.sub(r"[\s_]+", "_", sanitized)
    # Strip leading/trailing underscores
    sanitized = sanitized.strip("_")
    return sanitized or "export"


class ExportManager:
    """Creates ZIP archives containing rendered output files."""

    def export(
        self,
        product_name: str,
        coupang_images: Optional[list[bytes]] = None,
        naver_html: Optional[str] = None,
        web_html: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ExportPackage:
        """Package all provided outputs into a single ZIP archive.

        Args:
            product_name: Used as the root directory name inside the ZIP.
            coupang_images: List of PNG image bytes for Coupang image strips.
            naver_html: HTML string for Naver SmartStore.
            web_html: HTML string for responsive web output.
            metadata: Additional metadata to include in metadata.json.

        Returns:
            ExportPackage with zip_bytes, file_count, total_size_bytes, manifest.
        """
        dir_name = _sanitize_name(product_name)
        buf = io.BytesIO()
        manifest: dict[str, str] = {}

        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Coupang images
            if coupang_images:
                for idx, img_bytes in enumerate(coupang_images, start=1):
                    filename = f"{dir_name}/coupang/image_{idx:02d}.png"
                    zf.writestr(filename, img_bytes)
                    manifest[filename] = f"Coupang image strip #{idx}"

            # Naver HTML
            if naver_html is not None:
                filename = f"{dir_name}/naver/index.html"
                zf.writestr(filename, naver_html.encode("utf-8"))
                manifest[filename] = "Naver SmartStore-compatible HTML"

            # Web HTML
            if web_html is not None:
                filename = f"{dir_name}/web/index.html"
                zf.writestr(filename, web_html.encode("utf-8"))
                manifest[filename] = "Responsive standalone web HTML"

            # metadata.json
            meta: dict = {
                "product_name": product_name,
                "generation_date": datetime.now(timezone.utc).isoformat(),
                "file_count": len(manifest),
            }
            if metadata:
                meta.update(metadata)
            meta_filename = f"{dir_name}/metadata.json"
            meta_bytes = json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")
            zf.writestr(meta_filename, meta_bytes)
            manifest[meta_filename] = "Export metadata (generation date, quality scores, settings)"

        zip_bytes = buf.getvalue()

        return ExportPackage(
            zip_bytes=zip_bytes,
            file_count=len(manifest),
            total_size_bytes=len(zip_bytes),
            manifest=manifest,
        )
