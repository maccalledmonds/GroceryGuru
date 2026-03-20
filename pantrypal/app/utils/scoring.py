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
from .normalization import normalize_ingredient


def _matches_filter(recipe: Recipe, filters: list[str] | None) -> bool:
    if not filters:
        return True
    recipe_tags = set(recipe.diet_tags)
    return set(filters).issubset(recipe_tags)


_MISSING_PENALTY_PER_INGREDIENT = 0.05
_MAX_MISSING_PENALTY = 0.25
_HIGH_IMPORTANCE_KEYWORDS = tuple(keyword.lower() for keyword in HIGH_IMPORTANCE_INGREDIENT_KEYWORDS)
_LOW_IMPORTANCE_KEYWORDS = tuple(keyword.lower() for keyword in LOW_IMPORTANCE_INGREDIENT_KEYWORDS)


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

    weighted_overlap = sum(_ingredient_weight(ingredient) for ingredient in matched_set)
    weighted_total = sum(_ingredient_weight(ingredient) for ingredient in recipe_set)
    weighted_user_total = sum(_ingredient_weight(ingredient) for ingredient in user_set)

    recipe_coverage = weighted_overlap / weighted_total if weighted_total else 0.0
    user_coverage = weighted_overlap / weighted_user_total if weighted_user_total else 0.0
    base_score = (recipe_coverage + user_coverage) / 2.0

    core_query_terms = {ingredient for ingredient in user_set if _ingredient_weight(ingredient) >= HIGH_IMPORTANCE_WEIGHT}
    if len(core_query_terms) >= 2:
        core_overlap = len(matched_set.intersection(core_query_terms))
        core_coverage = core_overlap / len(core_query_terms)
        base_score *= core_coverage
    missing_penalty = min(_MAX_MISSING_PENALTY, _MISSING_PENALTY_PER_INGREDIENT * missing_count)
    score = max(0.0, min(1.0, base_score - missing_penalty))

    return {
        "exact_match_count": overlap,
        "coverage": base_score,
        "ingredient_match_ratio": base_score,
        "missing_count": missing_count,
        "score": score,
    }


def _ingredient_weight(ingredient: str) -> float:
    value = ingredient.strip().lower()
    if not value:
        return NORMAL_IMPORTANCE_WEIGHT

    if any(keyword in value for keyword in _LOW_IMPORTANCE_KEYWORDS):
        return LOW_IMPORTANCE_WEIGHT
    if any(keyword in value for keyword in _HIGH_IMPORTANCE_KEYWORDS):
        return HIGH_IMPORTANCE_WEIGHT
    return NORMAL_IMPORTANCE_WEIGHT


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
