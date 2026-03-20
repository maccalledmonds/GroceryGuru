"""Infer and add servings metadata for recipe dataset records.

Usage:
    python -m pantrypal.data.enrich_servings
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

RECIPES_PATH = Path(__file__).resolve().parent / "recipes.json"

# Handles phrases like:
# "makes 6 servings", "serves 4", "yield: 8", "12 portions", "for 2"
_EXPLICIT_SERVINGS_PATTERNS = [
    re.compile(r"\b(?:serves?|serve)\s*(?:about\s*)?(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"\b(?:makes?|yields?)\s*(?:about\s*)?(\d{1,2})\s*(?:servings?|portions?)?\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*(?:servings?|portions?)\b", re.IGNORECASE),
    re.compile(r"\bfor\s+(\d{1,2})\b", re.IGNORECASE),
]

_RECIPE_TYPE_BASE_SERVINGS: list[tuple[tuple[str, ...], int]] = [
    (("cake", "brownie", "cookie", "muffin", "cupcake", "pie", "tart"), 8),
    (("soup", "stew", "chili", "curry", "casserole"), 6),
    (("pasta", "lasagna", "noodle", "risotto", "paella"), 4),
    (("salad", "bowl", "omelette", "omelet", "sandwich", "burger", "taco", "wrap"), 2),
]

_AMOUNT_HINT_PATTERN = re.compile(
    r"(^|\s)(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+|[¼½¾⅓⅔⅛⅜⅝⅞])(?=\s)",
    re.IGNORECASE,
)

MIN_SERVINGS = 1
MAX_SERVINGS = 12


def _extract_explicit_servings(text: str) -> int | None:
    if not text.strip():
        return None

    for pattern in _EXPLICIT_SERVINGS_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        value = int(match.group(1))
        if MIN_SERVINGS <= value <= MAX_SERVINGS:
            return value
    return None


def _title_type_servings(title: str) -> int | None:
    lowered = title.strip().lower()
    if not lowered:
        return None

    for keywords, servings in _RECIPE_TYPE_BASE_SERVINGS:
        if any(keyword in lowered for keyword in keywords):
            return servings
    return None


def _ingredient_amount_signal(ingredients: list[str]) -> int:
    if not ingredients:
        return 0

    amount_lines = sum(1 for item in ingredients if _AMOUNT_HINT_PATTERN.search(item))
    if amount_lines >= 10:
        return 8
    if amount_lines >= 7:
        return 6
    if amount_lines >= 4:
        return 4
    if amount_lines >= 2:
        return 3
    return 0


def _ingredient_count_fallback(ingredients: list[str]) -> int:
    count = len([item for item in ingredients if item and item.strip()])
    if count >= 12:
        return 6
    if count >= 8:
        return 4
    if count >= 5:
        return 3
    return 2


def infer_servings(recipe: dict[str, Any]) -> tuple[int, str]:
    """Infer servings for a recipe and return (servings, rule_name)."""

    title = str(recipe.get("title", ""))
    instructions = str(recipe.get("instructions", ""))
    ingredients_raw = recipe.get("ingredients", [])
    ingredients = [str(item) for item in ingredients_raw if isinstance(item, str) or item is not None]

    explicit = _extract_explicit_servings(f"{title}\n{instructions}")
    if explicit is not None:
        return explicit, "explicit_yield"

    type_guess = _title_type_servings(title)
    amount_guess = _ingredient_amount_signal(ingredients)

    if type_guess is not None and amount_guess:
        return max(type_guess, amount_guess), "type_plus_amount"
    if type_guess is not None:
        return type_guess, "type_only"
    if amount_guess:
        return amount_guess, "amount_only"

    return _ingredient_count_fallback(ingredients), "ingredient_count_fallback"


def enrich_servings(recipes: list[dict[str, Any]]) -> Counter[str]:
    """Mutate recipes by adding inferred servings and return rule counts."""

    rule_counts: Counter[str] = Counter()
    for recipe in recipes:
        servings, rule = infer_servings(recipe)
        servings = max(MIN_SERVINGS, min(MAX_SERVINGS, servings))
        recipe["servings"] = servings
        rule_counts[rule] += 1
    return rule_counts


def main() -> None:
    with RECIPES_PATH.open("r", encoding="utf-8") as handle:
        recipes = json.load(handle)

    if not isinstance(recipes, list):
        raise ValueError("recipes.json must contain a top-level list")

    rule_counts = enrich_servings(recipes)

    with RECIPES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(recipes, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Updated {len(recipes)} recipes with servings.")
    for rule_name in sorted(rule_counts):
        print(f"- {rule_name}: {rule_counts[rule_name]}")


if __name__ == "__main__":
    main()
