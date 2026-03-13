"""Design Token System for detail-page-forge.

Maps D1000 50 design principles to CSS Custom Properties.
Provides DesignToken data models and DesignTokenSet with factory methods
for principle-based, category-based, and style keyword-based token generation.

CSS Custom Property naming: --df-{category}-{name}
Categories: color, typography (font), spacing, effect (shadow, blur, gradient)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.designer.d1000_principles import (
    CATEGORY_PROFILES,
    STYLE_KEYWORDS,
    STYLE_PRESETS,
)

# ─── Token category constants ─────────────────────────────────────

CATEGORY_COLOR = "color"
CATEGORY_TYPOGRAPHY = "typography"
CATEGORY_SPACING = "spacing"
CATEGORY_EFFECT = "effect"


# ─── D1000 principle ID -> CSS token override mapping ────────────
# Each principle can override specific token values.
# Keys: principle ID, Values: dict of css_name -> css_value

_PRINCIPLE_TOKEN_OVERRIDES: dict[int, dict[str, str]] = {
    # Principle 3: Minimal strong impression — huge whitespace, mono color
    3: {
        "--df-color-primary": "#111111",
        "--df-color-accent": "#111111",
        "--df-color-bg": "#ffffff",
        "--df-spacing-section": "120px 80px",
        "--df-spacing-element": "60px",
        "--df-font-heading": "'Noto Sans KR', -apple-system, sans-serif",
    },
    # Principle 15: 6:3:1 color formula — warm professional red
    15: {
        "--df-color-primary": "#e74c3c",
        "--df-color-accent": "#f39c12",
        "--df-color-bg": "#fafafa",
    },
    # Principle 21: Dawn colors — black+white+point
    21: {
        "--df-color-primary": "#1a1a2e",
        "--df-color-accent": "#e74c3c",
        "--df-color-bg": "#ffffff",
        "--df-font-heading": "'Noto Sans KR', -apple-system, sans-serif",
    },
    # Principle 28: Metal texture — dark metallic gradient
    28: {
        "--df-color-primary": "#2c2c3e",
        "--df-color-accent": "#d4af37",
        "--df-color-bg": "#0c0c16",
        "--df-font-heading": "'Space Grotesk', -apple-system, sans-serif",
        "--df-shadow-card": "0 20px 60px rgba(0,0,0,0.6)",
        "--df-shadow-button": "0 8px 32px rgba(212,175,55,0.3)",
    },
    # Principle 36: Blur background — mesh gradient trendy
    36: {
        "--df-color-primary": "#9333ea",
        "--df-color-accent": "#3b82f6",
        "--df-color-bg": "#0a0a12",
        "--df-gradient-mesh": "radial-gradient(circle at 20% 30%, rgba(147,51,234,0.35) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgba(59,130,246,0.3) 0%, transparent 50%)",  # noqa: E501
        "--df-font-heading": "'Playfair Display', serif",
        "--df-blur-effect": "blur(60px)",
    },
    # Principle 47: Faded color — vintage, low contrast
    47: {
        "--df-color-primary": "#8B7355",
        "--df-color-accent": "#D4AF37",
        "--df-color-bg": "#FFF8E7",
        "--df-font-heading": "'Playfair Display', serif",
        "--df-font-body": "'Noto Sans KR', serif",
    },
    # Principle 50: Blueprint style — technical professional
    50: {
        "--df-color-primary": "#4fc3f7",
        "--df-color-accent": "#0288d1",
        "--df-color-bg": "#0a1628",
    },
    # Principle 39: Unexpected blur — depth and focus
    39: {
        "--df-blur-effect": "blur(8px)",
        "--df-blur-strong": "blur(24px)",
        "--df-shadow-depth": "0 8px 32px rgba(0,0,0,0.15)",
    },
    # Principle 6: S-line composition — flowing curves
    6: {
        "--df-gradient-mesh": "radial-gradient(ellipse at 30% 60%, rgba(147,51,234,0.2) 0%, transparent 60%)",  # noqa: E501
    },
    # Principle 27: Natural landscape — warm nature tones
    27: {
        "--df-color-primary": "#e07b39",
        "--df-color-accent": "#2d8a4e",
        "--df-color-bg": "#faf5ee",
    },
    # Principle 29: Font mixing — hip mixed typography
    29: {
        "--df-font-heading": "'Playfair Display', serif",
        "--df-font-body": "'Space Grotesk', -apple-system, sans-serif",
    },
    # Principle 33: Text stroke — retro border style
    33: {
        "--df-color-primary": "#1a1a2e",
        "--df-color-accent": "#e74c3c",
    },
    # Principle 48: Circle decoration — organic shapes
    48: {
        "--df-gradient-mesh": "radial-gradient(circle, rgba(236,72,153,0.2) 0%, transparent 70%)",
    },
    # Principle 49: Droplet connection — organic flow
    49: {
        "--df-gradient-mesh": "radial-gradient(ellipse, rgba(99,102,241,0.15) 0%, transparent 60%)",
    },
}

# Default base token values (always included)
_DEFAULT_TOKENS: dict[str, tuple[str, str]] = {
    # (css_value, category)
    "--df-color-primary":    ("#e74c3c", CATEGORY_COLOR),
    "--df-color-accent":     ("#f39c12", CATEGORY_COLOR),
    "--df-color-bg":         ("#ffffff", CATEGORY_COLOR),
    "--df-color-text":       ("#333333", CATEGORY_COLOR),
    "--df-color-muted":      ("#999999", CATEGORY_COLOR),
    "--df-font-heading":     ("'Noto Sans KR', -apple-system, sans-serif", CATEGORY_TYPOGRAPHY),
    "--df-font-body":        ("'Noto Sans KR', -apple-system, sans-serif", CATEGORY_TYPOGRAPHY),
    "--df-font-size-xs":     ("11px", CATEGORY_TYPOGRAPHY),
    "--df-font-size-sm":     ("13px", CATEGORY_TYPOGRAPHY),
    "--df-font-size-base":   ("15px", CATEGORY_TYPOGRAPHY),
    "--df-font-size-lg":     ("20px", CATEGORY_TYPOGRAPHY),
    "--df-font-size-xl":     ("32px", CATEGORY_TYPOGRAPHY),
    "--df-font-size-2xl":    ("52px", CATEGORY_TYPOGRAPHY),
    "--df-spacing-section":  ("70px 44px", CATEGORY_SPACING),
    "--df-spacing-element":  ("24px", CATEGORY_SPACING),
    "--df-spacing-gap":      ("16px", CATEGORY_SPACING),
    "--df-shadow-card":      ("0 2px 8px rgba(0,0,0,0.06)", CATEGORY_EFFECT),
    "--df-shadow-button":    ("0 8px 24px rgba(231,76,60,0.35)", CATEGORY_EFFECT),
    "--df-shadow-depth":     ("0 16px 40px rgba(0,0,0,0.1)", CATEGORY_EFFECT),
    "--df-blur-effect":      ("blur(0px)", CATEGORY_EFFECT),
    "--df-blur-strong":      ("blur(4px)", CATEGORY_EFFECT),
    "--df-gradient-mesh":    ("none", CATEGORY_EFFECT),
}


@dataclass
class DesignToken:
    """A single CSS Custom Property token.

    Attributes:
        css_name: The CSS custom property name, e.g. --df-color-primary
        css_value: The CSS value, e.g. #e74c3c
        category: One of 'color', 'typography', 'spacing', 'effect'
    """

    css_name: str
    css_value: str
    category: str = CATEGORY_COLOR

    def to_declaration(self) -> str:
        """Return CSS declaration string: --df-name: value;"""
        return f"  {self.css_name}: {self.css_value};"


@dataclass
class DesignTokenSet:
    """A collection of DesignToken instances representing a complete design system.

    Factory methods:
        from_principles(ids): Build from D1000 principle IDs
        from_category(name): Build from CATEGORY_PROFILES key
        from_style_keyword(keyword): Build from STYLE_KEYWORDS key
        from_style_preset(name): Build from STYLE_PRESETS key
    """

    tokens: list[DesignToken] = field(default_factory=list)

    # ─── Output ─────────────────────────────────────────────────

    def to_css(self) -> str:
        """Generate :root { ... } CSS block with all custom properties."""
        if not self.tokens:
            return ":root {}"
        declarations = "\n".join(t.to_declaration() for t in self.tokens)
        return f":root {{\n{declarations}\n}}"

    # ─── Lookup ─────────────────────────────────────────────────

    def get_token(self, css_name: str) -> DesignToken | None:
        """Return the token with the given css_name, or None."""
        for t in self.tokens:
            if t.css_name == css_name:
                return t
        return None

    def tokens_by_category(self, category: str) -> list[DesignToken]:
        """Return all tokens belonging to the given category."""
        return [t for t in self.tokens if t.category == category]

    # ─── Composition ────────────────────────────────────────────

    def merge(self, other: DesignTokenSet) -> DesignTokenSet:
        """Merge two token sets. Tokens from 'other' override tokens in self with same name."""
        merged: dict[str, DesignToken] = {t.css_name: t for t in self.tokens}
        for t in other.tokens:
            merged[t.css_name] = t
        return DesignTokenSet(tokens=list(merged.values()))

    # ─── Factory methods ─────────────────────────────────────────

    @classmethod
    def from_principles(cls, principle_ids: list[int]) -> DesignTokenSet:
        """Build a DesignTokenSet from D1000 principle IDs.

        Starts from default tokens and applies principle-specific overrides
        in the order the principles appear in the ID list.
        """
        # Start with defaults
        token_values: dict[str, tuple[str, str]] = dict(_DEFAULT_TOKENS)

        # Apply overrides from each principle
        for pid in principle_ids:
            overrides = _PRINCIPLE_TOKEN_OVERRIDES.get(pid, {})
            for css_name, css_value in overrides.items():
                # Determine category from the css_name prefix
                category = _infer_category(css_name)
                token_values[css_name] = (css_value, category)

        # Convert to DesignToken instances
        tokens = [
            DesignToken(css_name=name, css_value=value, category=category)
            for name, (value, category) in token_values.items()
        ]
        return cls(tokens=tokens)

    @classmethod
    def from_category(cls, category_name: str) -> DesignTokenSet:
        """Build a DesignTokenSet from a CATEGORY_PROFILES key.

        Args:
            category_name: One of food, electronics, fashion, beauty, health, lifestyle

        Raises:
            ValueError: If category_name is not in CATEGORY_PROFILES
        """
        if category_name not in CATEGORY_PROFILES:
            raise ValueError(
                f"Unknown category: '{category_name}'. "
                f"Valid options: {list(CATEGORY_PROFILES.keys())}"
            )
        profile = CATEGORY_PROFILES[category_name]
        principle_ids = profile["key_principles"]
        return cls.from_principles(principle_ids)

    @classmethod
    def from_style_keyword(cls, keyword: str) -> DesignTokenSet:
        """Build a DesignTokenSet from a STYLE_KEYWORDS key.

        If the keyword is not found, returns the default token set.

        Args:
            keyword: A Korean style keyword, e.g. '프리미엄', '미니멀', '트렌디'
        """
        principle_ids = STYLE_KEYWORDS.get(keyword, [])
        return cls.from_principles(principle_ids)

    @classmethod
    def from_style_preset(cls, preset_name: str) -> DesignTokenSet:
        """Build a DesignTokenSet from a STYLE_PRESETS key.

        Args:
            preset_name: One of '고급 미니멀', '따뜻한 자연', '트렌디 힙', etc.

        Raises:
            ValueError: If preset_name is not in STYLE_PRESETS
        """
        if preset_name not in STYLE_PRESETS:
            raise ValueError(
                f"Unknown style preset: '{preset_name}'. "
                f"Valid options: {list(STYLE_PRESETS.keys())}"
            )
        principle_ids = STYLE_PRESETS[preset_name]
        return cls.from_principles(principle_ids)


# ─── Helper functions ─────────────────────────────────────────────

def _infer_category(css_name: str) -> str:
    """Infer token category from CSS custom property name prefix."""
    if css_name.startswith("--df-color-") or css_name.startswith("--df-gradient-"):
        return CATEGORY_COLOR
    if css_name.startswith("--df-font-"):
        return CATEGORY_TYPOGRAPHY
    if css_name.startswith("--df-spacing-"):
        return CATEGORY_SPACING
    # shadow, blur, gradient-mesh -> effect
    return CATEGORY_EFFECT
