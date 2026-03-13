"""Coupang renderer — converts HTML to 860px image strips.

Uses Playwright for headless browser rendering. Playwright is imported
lazily so that unit tests can run without a browser installed.

For unit tests: mock the _screenshot_html() method.
For integration tests: a real Playwright browser is required.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Playwright types only for type-checker, not at runtime


@dataclass
class CoupangImageSet:
    """Result from CoupangRenderer — a set of image strip bytes."""

    images: list[bytes]
    widths: list[int]  # All should equal the renderer's image_width (default 860)
    total_height: int
    section_count: int


# Height of each image strip in pixels (approximate section height)
_STRIP_HEIGHT = 600


class CoupangRenderer:
    """Renders HTML pages as 860px-wide PNG image strips for Coupang."""

    def __init__(self, image_width: int = 860) -> None:
        self.image_width = image_width

    async def render(self, html: str) -> CoupangImageSet:
        """Render HTML to Coupang image strips using Playwright.

        Opens a headless browser at viewport width self.image_width,
        takes a full-page screenshot, and splits into section strips.

        For unit testing, patch _screenshot_html() to return fake bytes.
        """
        screenshot_bytes = await asyncio.get_event_loop().run_in_executor(
            None, self._screenshot_html, html
        )
        return self._split_into_strips(screenshot_bytes)

    def render_sync(self, html: str) -> CoupangImageSet:
        """Synchronous wrapper for render().

        Useful for non-async contexts. Uses _screenshot_html() internally
        so it can be mocked in unit tests without a browser.
        """
        screenshot_bytes = self._screenshot_html(html)
        return self._split_into_strips(screenshot_bytes)

    def _screenshot_html(self, html: str) -> bytes:
        """Capture a full-page screenshot of the given HTML using Playwright.

        This method is designed to be mockable in unit tests.
        In integration tests, it requires a real Playwright installation.

        Returns:
            Raw PNG bytes of the full-page screenshot.
        """
        try:
            from playwright.sync_api import sync_playwright  # lazy import
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install it with: "
                "pip install playwright && playwright install chromium"
            ) from exc

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": self.image_width, "height": 900})
            page.set_content(html, wait_until="networkidle")
            screenshot = page.screenshot(full_page=True)
            browser.close()
            return screenshot

    def _split_into_strips(self, screenshot_bytes: bytes) -> CoupangImageSet:
        """Split a full-page screenshot into vertical image strips.

        Uses Pillow for image splitting. Falls back to returning the whole
        screenshot as a single strip if Pillow is unavailable or if the
        bytes are not a valid image (e.g., stub data in unit tests).
        """
        try:
            import io as _io

            from PIL import Image  # lazy import

            try:
                img = Image.open(_io.BytesIO(screenshot_bytes))
                total_width, total_height = img.size
            except Exception:
                # Not a valid image — return as single strip (unit test path)
                return CoupangImageSet(
                    images=[screenshot_bytes],
                    widths=[self.image_width],
                    total_height=0,
                    section_count=1,
                )

            strips: list[bytes] = []
            widths: list[int] = []
            y = 0
            while y < total_height:
                strip_h = min(_STRIP_HEIGHT, total_height - y)
                box = (0, y, total_width, y + strip_h)
                strip = img.crop(box)
                buf = _io.BytesIO()
                strip.save(buf, format="PNG")
                strips.append(buf.getvalue())
                widths.append(self.image_width)
                y += strip_h

            return CoupangImageSet(
                images=strips,
                widths=widths,
                total_height=total_height,
                section_count=len(strips),
            )
        except ImportError:
            # Pillow not available — return as single strip
            return CoupangImageSet(
                images=[screenshot_bytes],
                widths=[self.image_width],
                total_height=0,
                section_count=1,
            )
