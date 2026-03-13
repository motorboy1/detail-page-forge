"""Theme Generator — generates complete design themes from D1000 principles.

Fully deterministic, no AI calls.
Combines predefined THEME_RECIPES with DesignTokenSet.from_principles().
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.designer.design_tokens import DesignTokenSet


@dataclass
class Theme:
    """A complete design theme derived from D1000 principles.

    Attributes:
        name: Unique recipe name or 'custom'.
        description: Human-readable description (Korean or English).
        principle_ids: D1000 principle IDs used to build this theme.
        tokens: Generated DesignTokenSet for CSS custom properties.
        mood: Emotional mood — 'warm', 'cool', 'neutral', 'bold', 'elegant'.
        category_affinity: Product categories this theme fits well.
    """

    name: str
    description: str
    principle_ids: list[int]
    tokens: DesignTokenSet
    mood: str = "neutral"
    category_affinity: list[str] = field(default_factory=list)


class ThemeGenerator:
    """Generates design themes from predefined recipes or arbitrary principle IDs.

    All methods are deterministic — no AI calls are made.
    """

    # Predefined theme recipes mapping recipe names to configuration dicts.
    THEME_RECIPES: dict[str, dict] = {
        "premium_minimal": {
            "principles": [3, 21],
            "mood": "elegant",
            "description": "고급 미니멀 — 극단적 여백, 모노톤",
            "affinity": ["beauty", "fashion", "lifestyle"],
        },
        "warm_nature": {
            "principles": [27, 47],
            "mood": "warm",
            "description": "따뜻한 자연 — 내추럴 톤, 빈티지",
            "affinity": ["food", "health", "lifestyle"],
        },
        "trendy_hip": {
            "principles": [36, 29, 33],
            "mood": "bold",
            "description": "트렌디 힙 — 메쉬 그라디언트, 믹스 폰트",
            "affinity": ["electronics", "fashion"],
        },
        "dark_luxury": {
            "principles": [28, 50],
            "mood": "cool",
            "description": "다크 럭셔리 — 메탈릭, 블루프린트",
            "affinity": ["electronics", "fashion"],
        },
        "classic_trust": {
            "principles": [15, 21],
            "mood": "neutral",
            "description": "클래식 신뢰 — 6:3:1 컬러, 전통적 레이아웃",
            "affinity": ["food", "health"],
        },
        "organic_flow": {
            "principles": [6, 48, 49],
            "mood": "warm",
            "description": "유기적 흐름 — S곡선, 원형 장식, 물방울",
            "affinity": ["beauty", "health", "lifestyle"],
        },
    }

    def generate(self, recipe_name: str) -> Theme:
        """Generate a theme from a predefined recipe.

        Args:
            recipe_name: Key in THEME_RECIPES (e.g. 'premium_minimal').

        Returns:
            Theme instance with tokens built from recipe's principle IDs.

        Raises:
            ValueError: If recipe_name is not found in THEME_RECIPES.
        """
        if recipe_name not in self.THEME_RECIPES:
            valid = list(self.THEME_RECIPES.keys())
            raise ValueError(f"Unknown theme recipe: '{recipe_name}'. Valid options: {valid}")

        recipe = self.THEME_RECIPES[recipe_name]
        principle_ids: list[int] = recipe["principles"]
        tokens = DesignTokenSet.from_principles(principle_ids)

        return Theme(
            name=recipe_name,
            description=recipe["description"],
            principle_ids=list(principle_ids),
            tokens=tokens,
            mood=recipe["mood"],
            category_affinity=list(recipe["affinity"]),
        )

    def generate_custom(
        self,
        principle_ids: list[int],
        name: str = "custom",
    ) -> Theme:
        """Generate a custom theme from arbitrary D1000 principle IDs.

        Args:
            principle_ids: List of D1000 principle IDs (1-50).
            name: Display name for the theme (default: 'custom').

        Returns:
            Theme instance with tokens built from the given principle IDs.
        """
        tokens = DesignTokenSet.from_principles(principle_ids)
        mood = _infer_mood(principle_ids)

        return Theme(
            name=name,
            description="",
            principle_ids=list(principle_ids),
            tokens=tokens,
            mood=mood,
            category_affinity=[],
        )

    def list_recipes(self) -> list[dict]:
        """Return available theme recipes with metadata.

        Returns:
            List of dicts each containing: name, mood, description, affinity.
        """
        return [
            {
                "name": name,
                "mood": recipe["mood"],
                "description": recipe["description"],
                "affinity": list(recipe["affinity"]),
            }
            for name, recipe in self.THEME_RECIPES.items()
        ]

    def recommend_for_category(self, category: str) -> list[Theme]:
        """Recommend themes for a product category.

        Args:
            category: Product category string (e.g. 'beauty', 'food',
                      'electronics', 'fashion', 'health', 'lifestyle').

        Returns:
            List of Theme objects whose category_affinity includes the given
            category. Returns an empty list if no match is found.
        """
        results: list[Theme] = []
        for recipe_name, recipe in self.THEME_RECIPES.items():
            if category in recipe["affinity"]:
                results.append(self.generate(recipe_name))
        return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _infer_mood(principle_ids: list[int]) -> str:
    """Infer mood from principle IDs using a simple heuristic.

    Dark/blueprint principles  → 'cool'
    Nature/vintage principles  → 'warm'
    Minimal/premium principles → 'elegant'
    Bold/trendy principles     → 'bold'
    Default                    → 'neutral'
    """
    dark_principles = {28, 50}
    warm_principles = {27, 47, 6, 48, 49}
    elegant_principles = {3, 21}
    bold_principles = {36, 29, 33}

    pid_set = set(principle_ids)

    if pid_set & dark_principles and not (pid_set & warm_principles):
        return "cool"
    if pid_set & warm_principles and not (pid_set & dark_principles):
        return "warm"
    if pid_set & elegant_principles and not (pid_set & bold_principles):
        return "elegant"
    if pid_set & bold_principles:
        return "bold"
    return "neutral"
