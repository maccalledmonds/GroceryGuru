"""Database-backed recipe retrieval for hybrid recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from typing import Any

from ..models import load_recipes
from .normalization import normalize_ingredient

LOGGER = logging.getLogger(__name__)

_NON_MEAL_TITLE_HINTS = {
    "sauce",
    "dressing",
    "dip",
    "marinade",
    "condiment",
    "drink",
    "smoothie",
    "juice",
    "cocktail",
    "tea",
    "coffee",
}

_CANONICAL_INTEGRITY_METRICS: dict[str, int] = {
    "recipes_indexed": 0,
    "recipes_with_repairs": 0,
    "canonicalized_values": 0,
    "unknown_values": 0,
}


@dataclass(frozen=True, slots=True)
class _RecipeSearchRecord:
    """Preprocessed recipe fields for fast overlap scoring."""

    id: int
    title: str
    ingredients: list[str]
    instructions: str
    diet_tags: list[str]
    ingredient_set: set[str]


def _canonicalize_recipe_ingredients(recipe_ingredients: list[str]) -> list[str]:
    """Canonicalize recipe ingredient phrases for strict matching integrity."""

    canonicalized: list[str] = []
    seen: set[str] = set()
    for ingredient in recipe_ingredients:
        mapped = normalize_ingredient(ingredient)
        value = mapped.canonical_name or mapped.normalized
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        canonicalized.append(value)
    return canonicalized


def _validated_recipe_normalized_ingredients(
    recipe_ingredients: list[str],
    metrics: dict[str, int] | None = None,
) -> list[str]:
    """Validate/repair pre-normalized ingredients to canonical forms when possible."""

    validated: list[str] = []
    seen: set[str] = set()
    canonicalized_count = 0
    unknown_count = 0

    for ingredient in recipe_ingredients:
        value = ingredient.strip().lower()
        if not value:
            continue

        mapped = normalize_ingredient(value)
        canonical_value = mapped.canonical_name or mapped.normalized
        if not canonical_value:
            continue

        if mapped.canonical_name is None:
            unknown_count += 1
        elif canonical_value != value:
            canonicalized_count += 1

        if canonical_value in seen:
            continue
        seen.add(canonical_value)
        validated.append(canonical_value)

    if canonicalized_count or unknown_count:
        LOGGER.info(
            "Recipe normalized ingredients integrity pass: canonicalized=%d unknown=%d",
            canonicalized_count,
            unknown_count,
        )
        if metrics is not None:
            metrics["recipes_with_repairs"] += 1

    if metrics is not None:
        metrics["canonicalized_values"] += canonicalized_count
        metrics["unknown_values"] += unknown_count

    return validated


def _matches_filters(recipe_tags: list[str], filters: list[str] | None) -> bool:
    if not filters:
        return True
    return set(filters).issubset(set(recipe_tags))


def _is_meal_candidate(record: _RecipeSearchRecord) -> bool:
    """Filter out non-meal/trivial recipe candidates for similar retrieval."""

    title_tokens = set(record.title.strip().lower().split())
    if title_tokens.intersection(_NON_MEAL_TITLE_HINTS):
        return False

    # Trivial recipes (very low ingredient count) are poor "similar meal" suggestions.
    if len(record.ingredient_set) < 3:
        return False

    return True


@lru_cache(maxsize=1)
def _recipe_search_index() -> tuple[_RecipeSearchRecord, ...]:
    """Load and preprocess recipe data once for repeated searches."""

    recipes = load_recipes()
    indexed: list[_RecipeSearchRecord] = []
    metrics = {
        "recipes_indexed": 0,
        "recipes_with_repairs": 0,
        "canonicalized_values": 0,
        "unknown_values": 0,
    }

    for recipe in recipes:
        ingredient_source = (
            _validated_recipe_normalized_ingredients(recipe.ingredients_normalized, metrics=metrics)
            if recipe.ingredients_normalized
            else _canonicalize_recipe_ingredients(recipe.ingredients)
        )
        ingredient_set = {item for item in ingredient_source if item}
        if not ingredient_set:
            continue
        indexed.append(
            _RecipeSearchRecord(
                id=recipe.id,
                title=recipe.title,
                ingredients=list(ingredient_source),
                instructions=recipe.instructions,
                diet_tags=list(recipe.diet_tags),
                ingredient_set=ingredient_set,
            )
        )
        metrics["recipes_indexed"] += 1

    _CANONICAL_INTEGRITY_METRICS.update(metrics)
    LOGGER.info("canonical_integrity_metrics=%s", _CANONICAL_INTEGRITY_METRICS)

    LOGGER.info("Database recipe index warmed with %d recipes", len(indexed))
    return tuple(indexed)


def warm_recipe_cache() -> None:
    """Eagerly warm recipe index at startup to reduce first-request latency."""

    _ = _recipe_search_index()


def get_canonical_integrity_metrics() -> dict[str, int]:
    """Return last recorded canonical integrity metrics from index warm-up."""

    return dict(_CANONICAL_INTEGRITY_METRICS)


def _score_recipe(record: _RecipeSearchRecord, user_set: set[str]) -> dict[str, Any] | None:
    overlap_set = user_set.intersection(record.ingredient_set)
    overlap = len(overlap_set)
    total_recipe_ingredients = len(record.ingredient_set)

    if overlap == 0 or total_recipe_ingredients == 0:
        return None

    missing_ingredients = sorted(record.ingredient_set.difference(user_set))
    match_score = overlap / total_recipe_ingredients

    return {
        "id": record.id,
        "type": "database",
        "title": record.title,
        "ingredients": record.ingredients,
        "instructions": record.instructions,
        "missing_ingredients": missing_ingredients,
        "match_score": round(match_score, 4),
    }


def search_recipes(
    user_ingredients: list[str],
    top_k: int = 5,
    filters: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search local recipes by ingredient overlap and return top matches.

    Args:
        user_ingredients: Normalized ingredient names supplied by the user.
        top_k: Maximum number of recipes to return.

    Returns:
        Ranked recipe dictionaries with overlap-derived match scores.
    """

    cleaned = [item.strip().lower() for item in user_ingredients if item and item.strip()]
    if not cleaned:
        LOGGER.warning("search_recipes called with empty ingredient list")
        return []

    user_set = set(cleaned)
    ranked: list[dict[str, Any]] = []

    for recipe_record in _recipe_search_index():
        if not _matches_filters(recipe_record.diet_tags, filters):
            continue
        if not _is_meal_candidate(recipe_record):
            continue
        scored = _score_recipe(recipe_record, user_set)
        if scored is not None:
            ranked.append(scored)

    ranked.sort(
        key=lambda item: (
            float(item["match_score"]),
            -len(item["missing_ingredients"]),
            item["title"].lower(),
        ),
        reverse=True,
    )
    return ranked[: max(1, top_k)]
