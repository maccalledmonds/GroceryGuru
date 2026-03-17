"""Database-backed recipe retrieval for hybrid recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from typing import Any

from ..models import load_recipes

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _RecipeSearchRecord:
    """Preprocessed recipe fields for fast overlap scoring."""

    id: int
    title: str
    ingredients: list[str]
    instructions: str
    ingredient_set: set[str]


@lru_cache(maxsize=1)
def _recipe_search_index() -> tuple[_RecipeSearchRecord, ...]:
    """Load and preprocess recipe data once for repeated searches."""

    recipes = load_recipes()
    indexed: list[_RecipeSearchRecord] = []
    for recipe in recipes:
        ingredient_source = recipe.ingredients_normalized or recipe.ingredients
        ingredient_set = {item.strip().lower() for item in ingredient_source if item.strip()}
        if not ingredient_set:
            continue
        indexed.append(
            _RecipeSearchRecord(
                id=recipe.id,
                title=recipe.title,
                ingredients=list(ingredient_source),
                instructions=recipe.instructions,
                ingredient_set=ingredient_set,
            )
        )

    LOGGER.info("Database recipe index warmed with %d recipes", len(indexed))
    return tuple(indexed)


def warm_recipe_cache() -> None:
    """Eagerly warm recipe index at startup to reduce first-request latency."""

    _ = _recipe_search_index()


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


def search_recipes(user_ingredients: list[str], top_k: int = 5) -> list[dict[str, Any]]:
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
