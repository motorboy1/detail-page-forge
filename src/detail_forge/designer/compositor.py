"""Product photo compositor — background removal + image compositing."""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont


class Compositor:
    """Composite product photos onto generated design images."""

    def remove_background(self, image_data: bytes) -> bytes:
        """Remove background from product photo using rembg."""
        from rembg import remove
        return remove(image_data)

    def composite(
        self,
        background: bytes,
        product_photo: bytes,
        position: tuple[int, int] = (0, 0),
        scale: float = 1.0,
    ) -> bytes:
        """Composite product photo onto background image."""
        bg = Image.open(io.BytesIO(background)).convert("RGBA")
        fg = Image.open(io.BytesIO(product_photo)).convert("RGBA")

        # Scale product photo
        if scale != 1.0:
            new_size = (int(fg.width * scale), int(fg.height * scale))
            fg = fg.resize(new_size, Image.Resampling.LANCZOS)

        # Auto-center if position is (0, 0)
        if position == (0, 0):
            x = (bg.width - fg.width) // 2
            y = (bg.height - fg.height) // 2
            position = (x, y)

        # Composite
        bg.paste(fg, position, fg)

        output = io.BytesIO()
        bg.save(output, format="PNG")
        return output.getvalue()

    def add_text_overlay(
        self,
        image_data: bytes,
        headline: str,
        subheadline: str = "",
        position: str = "top",  # top, center, bottom
    ) -> bytes:
        """Add Korean text overlay to image (avoids AI text generation issues)."""
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load a Korean font, fall back to default
        font_size_headline = img.width // 15
        font_size_sub = img.width // 25

        try:
            font_headline = ImageFont.truetype(
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
                font_size_headline,
            )
            font_sub = ImageFont.truetype(
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                font_size_sub,
            )
        except (OSError, IOError):
            font_headline = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Calculate text position
        if position == "top":
            y_start = img.height // 10
        elif position == "center":
            y_start = img.height // 3
        else:  # bottom
            y_start = img.height * 2 // 3

        # Draw semi-transparent background for text
        text_bbox = draw.textbbox((0, 0), headline, font=font_headline)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        padding = 20
        x_center = (img.width - text_w) // 2

        draw.rectangle(
            [x_center - padding, y_start - padding,
             x_center + text_w + padding, y_start + text_h + padding * 2],
            fill=(0, 0, 0, 120),
        )

        # Draw headline
        draw.text((x_center, y_start), headline, font=font_headline, fill=(255, 255, 255, 255))

        # Draw subheadline
        if subheadline:
            sub_y = y_start + text_h + padding
            draw.text(
                ((img.width - draw.textlength(subheadline, font=font_sub)) // 2, sub_y),
                subheadline,
                font=font_sub,
                fill=(255, 255, 255, 220),
            )

        result = Image.alpha_composite(img, overlay).convert("RGB")
        output = io.BytesIO()
        result.save(output, format="PNG")
        return output.getvalue()
