"""Web renderer — creates responsive standalone HTML.

Ensures:
- Proper DOCTYPE, viewport meta tag, charset
- Responsive media queries (@media max-width: 768px)
- Images have max-width: 100%
- Print-friendly CSS
- Google Fonts CDN links preserved
- Self-contained output
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class WebHTML:
    """Output from WebRenderer."""

    html: str
    has_media_queries: bool = False
    viewport_meta: bool = False


# Responsive CSS injected into every output
_RESPONSIVE_CSS = """
/* Responsive — detail-forge */
img { max-width: 100%; height: auto; }
@media (max-width: 768px) {
  body { padding: 0 12px; }
  img { max-width: 100%; }
  table { width: 100% !important; }
}
@media print {
  body { margin: 0; }
  img { max-width: 100%; page-break-inside: avoid; }
  a::after { content: " (" attr(href) ")"; }
}
"""

_VIEWPORT_META = '<meta name="viewport" content="width=device-width, initial-scale=1">'
_CHARSET_META = '<meta charset="utf-8">'


class WebRenderer:
    """Converts HTML to a responsive standalone web page."""

    def render(self, html: str, product_name: str = "") -> WebHTML:
        """Render HTML as a complete responsive standalone page.

        Ensures DOCTYPE, viewport, charset, responsive CSS, and print styles.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Ensure <html> element exists
        html_tag = soup.find("html")
        if html_tag is None:
            # Wrap everything in proper structure
            wrapper = BeautifulSoup(
                "<!DOCTYPE html><html><head></head><body></body></html>", "html.parser"
            )
            wrapper.body.clear()
            for child in list(soup.children):
                wrapper.body.append(child)
            soup = wrapper
            html_tag = soup.find("html")

        head = soup.find("head")
        if head is None:
            head = soup.new_tag("head")
            html_tag.insert(0, head)

        body = soup.find("body")
        if body is None:
            body = soup.new_tag("body")
            html_tag.append(body)

        # Ensure charset meta
        charset_present = bool(
            soup.find("meta", attrs={"charset": True})
            or soup.find("meta", attrs={"http-equiv": "Content-Type"})
        )
        if not charset_present:
            charset_tag = BeautifulSoup(_CHARSET_META, "html.parser").find("meta")
            head.insert(0, charset_tag)

        # Ensure viewport meta
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        viewport_present = viewport_tag is not None
        if not viewport_present:
            vp_tag = BeautifulSoup(_VIEWPORT_META, "html.parser").find("meta")
            # Insert after charset
            head.insert(1, vp_tag)
            viewport_present = True

        # Ensure product title if provided
        title_tag = soup.find("title")
        if product_name:
            if title_tag is None:
                title_tag = soup.new_tag("title")
                head.append(title_tag)
            if product_name not in title_tag.get_text():
                title_tag.string = product_name
        else:
            if title_tag is None:
                title_tag = soup.new_tag("title")
                title_tag.string = "Product Detail Page"
                head.append(title_tag)

        # Inject responsive + print CSS
        responsive_style = soup.new_tag("style")
        responsive_style.string = _RESPONSIVE_CSS
        head.append(responsive_style)

        # Build final HTML string with DOCTYPE
        html_str = str(soup)
        if not html_str.lower().startswith("<!doctype"):
            html_str = "<!DOCTYPE html>\n" + html_str

        has_mq = "@media" in html_str

        return WebHTML(
            html=html_str,
            has_media_queries=has_mq,
            viewport_meta=viewport_present,
        )
