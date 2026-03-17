"""Recipe ranking and scoring utilities."""

from __future__ import annotations

from typing import Any

from ..config import (
    HIGH_IMPORTANCE_INGREDIENT_KEYWORDS,
    HIGH_IMPORTANCE_WEIGHT,
    LOW_IMPORTANCE_INGREDIENT_KEYWORDS,
    LOW_IMPORTANCE_WEIGHT,
    NORMAL_IMPORTANCE_WEIGHT,
)
from ..models import Recipe, recipe_to_dict


def _matches_filter(recipe: Recipe, filters: list[str] | None) -> bool:
    if not filters:
        return True
    recipe_tags = set(recipe.diet_tags)
    return set(filters).issubset(recipe_tags)


def _ingredient_weight(ingredient: str) -> float:
    normalized = ingredient.strip().lower()
    if not normalized:
        return NORMAL_IMPORTANCE_WEIGHT

    if any(keyword in normalized for keyword in HIGH_IMPORTANCE_INGREDIENT_KEYWORDS):
        return HIGH_IMPORTANCE_WEIGHT

    if any(keyword in normalized for keyword in LOW_IMPORTANCE_INGREDIENT_KEYWORDS):
        return LOW_IMPORTANCE_WEIGHT

    return NORMAL_IMPORTANCE_WEIGHT


def _weighted_sum(ingredients: set[str]) -> float:
    return sum(_ingredient_weight(item) for item in ingredients)


def _compute_recipe_score(recipe: Recipe, user_ingredients: list[str]) -> dict[str, float | int]:
    user_set = set(user_ingredients)
    # Prefer pre-normalized ingredients (covers scraped recipes whose raw
    # `ingredients` list contains full quantity strings like "2 cups chopped
    # onion" which would never exact-match user input).
    recipe_ingredients = recipe.ingredients_normalized or recipe.ingredients
    recipe_set = set(recipe_ingredients)
    matched_set = user_set.intersection(recipe_set)

    overlap = len(matched_set)
    recipe_total = len(recipe_set)
    user_total = len(user_set)

    recipe_weight_total = _weighted_sum(recipe_set)
    matched_recipe_weight = _weighted_sum(matched_set)
    user_weight_total = _weighted_sum(user_set)
    matched_user_weight = _weighted_sum(matched_set)

    coverage = matched_recipe_weight / recipe_weight_total if recipe_weight_total else 0.0
    ingredient_match_ratio = matched_user_weight / user_weight_total if user_weight_total else 0.0
    score = 0.75 * coverage + 0.25 * ingredient_match_ratio

    return {
        "exact_match_count": overlap,
        "coverage": coverage,
        "ingredient_match_ratio": ingredient_match_ratio,
        "score": score,
    }


def recommend_recipes(
    user_ingredients: list[str],
    recipes: list[Recipe],
    top_k: int = 5,
    filters: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Rank recipes by ingredient overlap and return top results."""

    normalized_user = [item for item in user_ingredients if item]
    if not normalized_user:
        return []

    ranked: list[dict[str, Any]] = []

    for recipe in recipes:
        if not _matches_filter(recipe, filters):
            continue

        metrics = _compute_recipe_score(recipe, normalized_user)
        if metrics["exact_match_count"] == 0:
            continue

        recipe_dict = recipe_to_dict(recipe)
        recipe_dict.update(metrics)
        recipe_dict["match_percentage"] = round(float(metrics["coverage"]) * 100.0, 1)
        ranked.append(recipe_dict)

    ranked.sort(
        key=lambda item: (
            float(item["score"]),
            int(item["exact_match_count"]),
            float(item["coverage"]),
        ),
        reverse=True,
    )
    return ranked[:top_k]
