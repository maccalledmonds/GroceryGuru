"""Recipe ranking and scoring utilities."""

from __future__ import annotations

from typing import Any

from ..models import Recipe, recipe_to_dict


def _matches_filter(recipe: Recipe, filters: list[str] | None) -> bool:
    if not filters:
        return True
    recipe_tags = set(recipe.diet_tags)
    return set(filters).issubset(recipe_tags)


def _compute_recipe_score(recipe: Recipe, user_ingredients: list[str]) -> dict[str, float | int]:
    user_set = set(user_ingredients)
    # Prefer pre-normalized ingredients (covers scraped recipes whose raw
    # `ingredients` list contains full quantity strings like "2 cups chopped
    # onion" which would never exact-match user input).
    recipe_ingredients = recipe.ingredients_normalized or recipe.ingredients
    recipe_set = set(recipe_ingredients)

    overlap = len(user_set.intersection(recipe_set))
    recipe_total = len(recipe_set)
    user_total = len(user_set)

    coverage = overlap / recipe_total if recipe_total else 0.0
    ingredient_match_ratio = overlap / user_total if user_total else 0.0
    score = 0.7 * coverage + 0.3 * ingredient_match_ratio

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
