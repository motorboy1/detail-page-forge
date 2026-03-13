"""Quality gate — 5-dimension deterministic quality evaluation.

Evaluates HTML output across five dimensions:
  1. layout     — section count, heading hierarchy, image presence
  2. typography — font-size diversity, line-height, font-family
  3. color      — background-color, text color, no invisible text
  4. readability — text length per section, heading presence
  5. platform   — platform-specific compliance checks

All analysis is done with BeautifulSoup4 (no AI, fully deterministic).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class QualityDimension:
    """Single quality dimension result."""

    name: str
    score: float  # 0–10
    issues: list[str] = field(default_factory=list)


@dataclass
class OutputQuality:
    """Complete quality evaluation result."""

    dimensions: list[QualityDimension]
    total_score: float
    passed: bool  # total_score >= 7.0
    platform: str = "web"


_PASS_THRESHOLD = 7.0
_NAVER_FORBIDDEN = {"script", "link", "meta", "iframe", "object", "embed", "form", "input"}


class QualityGate:
    """Evaluates rendered HTML quality across 5 dimensions."""

    def evaluate(self, html: str, platform: str = "web") -> OutputQuality:
        """Run all 5 quality checks and compute overall score."""
        soup = BeautifulSoup(html, "html.parser")

        dimensions = [
            self._check_layout(soup),
            self._check_typography(soup),
            self._check_color(soup),
            self._check_readability(soup),
            self._check_platform(soup, platform),
        ]

        total = sum(d.score for d in dimensions) / len(dimensions)
        passed = total >= _PASS_THRESHOLD

        return OutputQuality(
            dimensions=dimensions,
            total_score=round(total, 2),
            passed=passed,
            platform=platform,
        )

    # ------------------------------------------------------------------
    # Dimension: layout
    # ------------------------------------------------------------------

    def _check_layout(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        # Check section count
        sections = soup.find_all(["section", "div", "article"])
        if len(sections) == 0:
            issues.append("No structural sections found (section/div/article)")
            score -= 2.0

        # Check heading hierarchy: h1 should appear before h2
        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        if headings:
            first_level = int(headings[0].name[1])
            if first_level > 1:
                issues.append(f"First heading is h{first_level}, expected h1")
                score -= 2.0
        else:
            issues.append("No headings found")
            score -= 1.0

        # Check h1 presence
        if not soup.find("h1"):
            if not any("No headings" in i for i in issues):
                issues.append("No h1 heading found")
            score -= 1.0

        # Check image presence
        images = soup.find_all("img")
        if not images:
            issues.append("No images found")
            score -= 2.0

        return QualityDimension(name="layout", score=max(0.0, score), issues=issues)

    # ------------------------------------------------------------------
    # Dimension: typography
    # ------------------------------------------------------------------

    def _check_typography(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        all_styles = self._collect_all_styles(soup)
        combined_css = " ".join(all_styles)

        # Check font-size diversity
        font_sizes = re.findall(r"font-size:\s*([^;]+)", combined_css)
        unique_sizes = {s.strip() for s in font_sizes}
        if len(unique_sizes) < 2:
            issues.append("Font sizes lack diversity (fewer than 2 distinct values)")
            score -= 2.0

        # Check line-height
        if "line-height" not in combined_css:
            issues.append("No line-height set — readability may suffer")
            score -= 1.5

        # Check font-family
        if "font-family" not in combined_css:
            issues.append("No font-family specified")
            score -= 1.5

        return QualityDimension(name="typography", score=max(0.0, score), issues=issues)

    # ------------------------------------------------------------------
    # Dimension: color
    # ------------------------------------------------------------------

    def _check_color(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        all_styles = self._collect_all_styles(soup)
        combined_css = " ".join(all_styles)

        # Check background-color
        if "background-color" not in combined_css and "background:" not in combined_css:
            issues.append("No background-color set")
            score -= 1.5

        # Check text color
        if "color:" not in combined_css:
            issues.append("No text color specified")
            score -= 1.5

        # Check for invisible text (color == background heuristic)
        # Simple check: white text on white, black on black
        white_on_white = "color: #fff" in combined_css and "background: #fff" in combined_css
        black_on_black = "color: #000" in combined_css and "background: #000" in combined_css
        if white_on_white or black_on_black:
            issues.append("Potential invisible text detected (same text/bg color)")
            score -= 3.0

        return QualityDimension(name="color", score=max(0.0, score), issues=issues)

    # ------------------------------------------------------------------
    # Dimension: readability
    # ------------------------------------------------------------------

    def _check_readability(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        # Check paragraph/text presence
        paragraphs = soup.find_all("p")
        if not paragraphs:
            issues.append("No paragraph elements found")
            score -= 2.0
        else:
            # Check text length per section — avoid too-short sections
            short_sections = 0
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) < 10:
                    short_sections += 1
            if short_sections > len(paragraphs) // 2:
                issues.append("Many paragraphs have very short text (< 10 chars)")
                score -= 1.5

        # Check heading presence for structure
        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        if not headings:
            issues.append("No headings found for content structure")
            score -= 2.0

        # Check total text length
        body = soup.find("body") or soup
        text = body.get_text(strip=True)
        if len(text) < 50:
            issues.append("Very little text content (< 50 characters)")
            score -= 2.0

        return QualityDimension(name="readability", score=max(0.0, score), issues=issues)

    # ------------------------------------------------------------------
    # Dimension: platform
    # ------------------------------------------------------------------

    def _check_platform(self, soup: BeautifulSoup, platform: str) -> QualityDimension:
        if platform == "coupang":
            return self._check_platform_coupang(soup)
        elif platform == "naver":
            return self._check_platform_naver(soup)
        else:
            return self._check_platform_web(soup)

    def _check_platform_coupang(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        images = soup.find_all("img")
        if not images:
            issues.append("Coupang: no images found — image strips required")
            score -= 4.0

        # Check for 860px width indication
        all_styles = self._collect_all_styles(soup)
        combined_css = " ".join(all_styles)
        has_860 = "860" in combined_css or any(str(img.get("width", "")) == "860" for img in images)
        if images and not has_860:
            issues.append("Coupang: no 860px width found in images or CSS")
            score -= 2.0

        return QualityDimension(name="platform", score=max(0.0, score), issues=issues)

    def _check_platform_naver(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        # Check for forbidden tags
        for tag_name in _NAVER_FORBIDDEN:
            found = soup.find_all(tag_name)
            if found:
                issues.append(f"Naver: forbidden tag <{tag_name}> found ({len(found)} times)")
                score -= 1.0

        # Check for inline CSS (style attributes)
        elements_with_style = soup.find_all(attrs={"style": True})
        if not elements_with_style:
            issues.append("Naver: no inline CSS found — external CSS not allowed")
            score -= 2.0

        # Check for web font references
        all_styles = self._collect_all_styles(soup)
        combined = " ".join(all_styles)
        web_fonts = ["'Noto Sans KR'", "'Playfair Display'", "'Space Grotesk'"]
        for wf in web_fonts:
            if wf in combined:
                issues.append(f"Naver: web font {wf} not replaced with safe font")
                score -= 1.0

        return QualityDimension(name="platform", score=max(0.0, score), issues=issues)

    def _check_platform_web(self, soup: BeautifulSoup) -> QualityDimension:
        issues: list[str] = []
        score = 10.0

        # Check viewport meta
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            issues.append("Web: missing viewport meta tag for mobile responsiveness")
            score -= 2.5

        # Check for responsive CSS
        all_styles = self._collect_all_styles(soup)
        combined = " ".join(all_styles)
        if "@media" not in combined:
            issues.append("Web: no media queries found — not responsive")
            score -= 2.5

        # Check DOCTYPE
        html_str = str(soup)
        if "<!doctype" not in html_str.lower():
            issues.append("Web: missing DOCTYPE declaration")
            score -= 1.0

        return QualityDimension(name="platform", score=max(0.0, score), issues=issues)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _collect_all_styles(self, soup: BeautifulSoup) -> list[str]:
        """Collect CSS text from <style> tags and inline style attributes."""
        styles = []
        for style_tag in soup.find_all("style"):
            styles.append(style_tag.get_text())
        for tag in soup.find_all(attrs={"style": True}):
            styles.append(str(tag.get("style", "")))
        return styles
