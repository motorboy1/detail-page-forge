"""Naver SmartStore HTML renderer.

Sanitizes HTML for Naver SmartStore editor compatibility:
- Removes forbidden tags (script, link, meta, iframe, etc.)
- Removes event handler attributes
- Converts <style> rules to inline CSS
- Replaces web fonts with Naver-safe alternatives
- Resolves CSS custom properties (var(--df-*)) to actual values
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag


@dataclass
class NaverHTML:
    """Output from NaverRenderer."""

    html: str
    warnings: list[str] = field(default_factory=list)
    size_bytes: int = 0

    def __post_init__(self) -> None:
        if self.size_bytes == 0 and self.html:
            self.size_bytes = len(self.html.encode("utf-8"))


class NaverRenderer:
    """Converts HTML to Naver SmartStore-compatible format."""

    FORBIDDEN_TAGS = {"script", "link", "meta", "iframe", "object", "embed", "form", "input"}
    FORBIDDEN_ATTRS = {"onclick", "onload", "onerror", "onmouseover"}
    SAFE_FONTS = {
        "'Noto Sans KR'": "맑은 고딕, Malgun Gothic, sans-serif",
        '"Noto Sans KR"': "맑은 고딕, Malgun Gothic, sans-serif",
        "'Playfair Display'": "Georgia, serif",
        '"Playfair Display"': "Georgia, serif",
        "'Space Grotesk'": "Arial, sans-serif",
        '"Space Grotesk"': "Arial, sans-serif",
    }
    # CSS custom property detection pattern (kept for detection, not for empty substitution)
    _CSS_VAR_RE = re.compile(r"var\(--[^)]+\)")

    def render(self, html: str) -> NaverHTML:
        """Convert HTML to Naver SmartStore-compatible format.

        Steps:
        1. Build CSS variable map from all <style> blocks
        2. Remove forbidden tags
        3. Remove forbidden event attributes
        4. Extract and inline <style> CSS onto elements (with var() resolved)
        5. Replace web fonts with safe alternatives
        6. Resolve remaining CSS custom properties in inline styles
        """
        warnings: list[str] = []
        soup = BeautifulSoup(html, "html.parser")

        # Step 1: Build a global var_map from ALL style blocks before any removal
        all_css = "\n".join(
            style_tag.get_text() for style_tag in soup.find_all("style")
        )
        var_map = self._build_var_map(all_css)

        # Step 2: Extract style rules (with var() resolved) before removing tags
        style_map = self._extract_style_map(soup, var_map)

        # Step 3: Remove forbidden tags
        for tag_name in self.FORBIDDEN_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Step 4: Remove forbidden attributes
        for tag in soup.find_all(True):
            for attr in list(self.FORBIDDEN_ATTRS):
                if tag.has_attr(attr):
                    del tag[attr]
                    warnings.append(f"Removed forbidden attribute: {attr}")

        # Step 5: Apply inline styles from style_map
        self._apply_inline_styles(soup, style_map)

        # Step 6: Replace web fonts
        self._replace_web_fonts(soup)

        # Step 7: Resolve remaining var() references in inline styles using var_map
        for tag in soup.find_all(True):
            if tag.has_attr("style"):
                tag["style"] = self._resolve_css_vars(tag["style"], var_map)

        # Render to string
        result_html = str(soup)
        return NaverHTML(
            html=result_html,
            warnings=warnings,
            size_bytes=len(result_html.encode("utf-8")),
        )

    def _build_var_map(self, css_text: str) -> dict[str, str]:
        """Extract CSS custom property declarations into a name->value map.

        Scans the full CSS text (including :root and any other blocks) for
        --name: value; declarations and returns a lookup dict.
        """
        var_map: dict[str, str] = {}
        for match in re.finditer(r"(--[a-zA-Z][\w-]*)\s*:\s*([^;]+);", css_text):
            var_map[match.group(1)] = match.group(2).strip()
        return var_map

    def _resolve_css_vars(self, css_text: str, var_map: dict[str, str]) -> str:
        """Replace var(--name) and var(--name, fallback) with resolved values.

        If the variable name exists in var_map, uses that value.
        Falls back to the declared fallback value if the variable is unknown.
        """
        def replacer(m: re.Match) -> str:
            inner = m.group(1)  # contents inside var(...)
            parts = inner.split(",", 1)
            var_name = parts[0].strip()
            fallback = parts[1].strip() if len(parts) > 1 else ""
            return var_map.get(var_name, fallback)

        return re.sub(r"var\(([^)]+)\)", replacer, css_text)

    def _extract_style_map(
        self, soup: BeautifulSoup, var_map: dict[str, str]
    ) -> dict[str, dict[str, str]]:
        """Parse <style> blocks and return a simple selector->property map.

        Only handles basic element selectors (e.g., h1, p, body) for
        deterministic inline style application.

        var() references are resolved to actual values using var_map before
        parsing rules. Custom property declarations are stripped afterward.
        """
        style_map: dict[str, dict[str, str]] = {}
        for style_tag in soup.find_all("style"):
            css_text = style_tag.get_text()
            # Replace web fonts in CSS text first
            for web_font, safe_font in self.SAFE_FONTS.items():
                css_text = css_text.replace(web_font, safe_font)
            # Resolve var() references to actual values BEFORE stripping declarations
            css_text = self._resolve_css_vars(css_text, var_map)
            # Strip CSS custom property declarations (--name: value;)
            # The values are already resolved above so we only remove the declarations
            css_text = re.sub(r"--[a-zA-Z][^:]*:[^;]+;", "", css_text)
            # Parse rules
            rules = re.findall(r"([^{]+)\{([^}]*)\}", css_text)
            for selector_block, props_block in rules:
                selectors = [s.strip() for s in selector_block.split(",")]
                props = self._parse_css_props(props_block)
                for sel in selectors:
                    # Only handle simple tag/class selectors
                    if sel and not sel.startswith(":") and not sel.startswith("@"):
                        if sel not in style_map:
                            style_map[sel] = {}
                        style_map[sel].update(props)
            style_tag.decompose()
        return style_map

    def _parse_css_props(self, props_block: str) -> dict[str, str]:
        """Parse CSS property declarations into a dict."""
        props: dict[str, str] = {}
        for decl in props_block.split(";"):
            decl = decl.strip()
            if ":" in decl:
                prop, _, value = decl.partition(":")
                prop = prop.strip()
                value = value.strip()
                if prop and value:
                    props[prop] = value
        return props

    def _apply_inline_styles(
        self, soup: BeautifulSoup, style_map: dict[str, dict[str, str]]
    ) -> None:
        """Apply style_map rules as inline style attributes."""
        for selector, props in style_map.items():
            if not props:
                continue
            try:
                elements = soup.select(selector)
            except Exception:
                continue
            for el in elements:
                if not isinstance(el, Tag):
                    continue
                existing = el.get("style", "")
                new_style = "; ".join(f"{k}: {v}" for k, v in props.items())
                if existing:
                    el["style"] = existing + "; " + new_style
                else:
                    el["style"] = new_style

    def _replace_web_fonts(self, soup: BeautifulSoup) -> None:
        """Replace web font references in inline style attributes."""
        for tag in soup.find_all(True):
            if tag.has_attr("style"):
                style = tag["style"]
                for web_font, safe_font in self.SAFE_FONTS.items():
                    style = style.replace(web_font, safe_font)
                tag["style"] = style
