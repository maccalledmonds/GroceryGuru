"""Recipe ranking and scoring utilities."""

from __future__ import annotations

from typing import Any

from ..models import Recipe, recipe_to_dict
from .normalization import normalize_ingredient


def _matches_filter(recipe: Recipe, filters: list[str] | None) -> bool:
    if not filters:
        return True
    recipe_tags = set(recipe.diet_tags)
    return set(filters).issubset(recipe_tags)


_MISSING_PENALTY_PER_INGREDIENT = 0.05
_MAX_MISSING_PENALTY = 0.25


def _canonicalize_recipe_ingredients(recipe: Recipe) -> set[str]:
    if recipe.ingredients_normalized:
        return {item.strip().lower() for item in recipe.ingredients_normalized if item.strip()}

    canonicalized: set[str] = set()
    for ingredient in recipe.ingredients:
        mapped = normalize_ingredient(ingredient)
        value = mapped.canonical_name or mapped.normalized
        if value:
            canonicalized.add(value)
    return canonicalized


def _compute_recipe_score(recipe: Recipe, user_ingredients: list[str]) -> dict[str, float | int]:
    user_set = set(user_ingredients)
    recipe_set = _canonicalize_recipe_ingredients(recipe)
    matched_set = user_set.intersection(recipe_set)

    overlap = len(matched_set)
    recipe_total = len(recipe_set)
    missing_count = max(0, recipe_total - overlap)

    base_score = overlap / recipe_total if recipe_total else 0.0
    missing_penalty = min(_MAX_MISSING_PENALTY, _MISSING_PENALTY_PER_INGREDIENT * missing_count)
    score = max(0.0, min(1.0, base_score - missing_penalty))

    return {
        "exact_match_count": overlap,
        "coverage": base_score,
        "ingredient_match_ratio": base_score,
        "missing_count": missing_count,
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
