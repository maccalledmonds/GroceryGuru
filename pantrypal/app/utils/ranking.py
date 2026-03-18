"""Ranking and partitioning for hybrid recipe recommendations."""

from __future__ import annotations

from typing import Any

from .normalization import normalize_ingredient

ANIMAL_INGREDIENT_HINTS = {
    "beef",
    "pork",
    "chicken",
    "turkey",
    "lamb",
    "bacon",
    "sausage",
    "salmon",
    "tuna",
    "shrimp",
    "cod",
    "tilapia",
    "crab",
    "egg",
    "butter",
    "ghee",
    "lard",
    "fish sauce",
    "worcestershire sauce",
    "mayonnaise",
    "honey",
    "ice cream",
}

MEAT_SEAFOOD_HINTS = {
    "beef",
    "pork",
    "chicken",
    "turkey",
    "lamb",
    "bacon",
    "sausage",
    "salmon",
    "tuna",
    "shrimp",
    "cod",
    "tilapia",
    "crab",
    "fish sauce",
    "worcestershire sauce",
    "lard",
}

GLUTEN_HINTS = {
    "flour",
    "whole wheat flour",
    "pasta",
    "noodle",
    "bread",
    "barley",
    "couscous",
    "tortilla",
    "breadcrumb",
}

HIGH_PROTEIN_HINTS = {
    "beef",
    "pork",
    "chicken",
    "turkey",
    "lamb",
    "salmon",
    "tuna",
    "shrimp",
    "cod",
    "tilapia",
    "crab",
    "egg",
    "tofu",
    "tempeh",
    "chickpea",
    "black bean",
    "kidney bean",
    "lentil",
    "peanut butter",
}


def _score_database_item(item: dict[str, Any]) -> float:
    match_score = float(item.get("match_score", 0.0))
    missing_count = len(item.get("missing_ingredients", []))
    penalty = min(0.25, 0.05 * missing_count)
    return max(0.0, min(1.0, match_score - penalty))


def _score_generated_item(item: dict[str, Any], user_ingredients: list[str]) -> float:
    user_set = {ingredient.strip().lower() for ingredient in user_ingredients if ingredient.strip()}
    generated_ingredients: set[str] = set()
    for ingredient in item.get("ingredients", []):
        if not isinstance(ingredient, str) or not ingredient.strip():
            continue
        mapped = normalize_ingredient(ingredient)
        canonical_value = mapped.canonical_name or mapped.normalized
        if canonical_value:
            generated_ingredients.add(canonical_value)

    overlap = len(user_set.intersection(generated_ingredients))
    total_required = len(generated_ingredients)
    coverage = overlap / total_required if total_required else 0.0
    missing_count = len(item.get("missing_ingredients", []))
    missing_penalty = min(0.20, 0.04 * missing_count)
    score = coverage - missing_penalty
    return max(0.0, min(1.0, score))


def _canonicalized_item_ingredients(item: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for ingredient in item.get("ingredients", []):
        if not isinstance(ingredient, str) or not ingredient.strip():
            continue
        mapped = normalize_ingredient(ingredient)
        canonical_value = mapped.canonical_name or mapped.normalized
        if canonical_value:
            values.add(canonical_value)
    return values


def _infer_diet_tags_from_item(item: dict[str, Any]) -> set[str]:
    ingredients = _canonicalized_item_ingredients(item)
    inferred: set[str] = set()

    if not ingredients.intersection(ANIMAL_INGREDIENT_HINTS):
        inferred.add("vegan")
    if not ingredients.intersection(MEAT_SEAFOOD_HINTS):
        inferred.add("vegetarian")
    if not ingredients.intersection(GLUTEN_HINTS):
        inferred.add("gluten_free")
    if ingredients.intersection(HIGH_PROTEIN_HINTS):
        inferred.add("high_protein")

    return inferred


def _matches_filters(item: dict[str, Any], filters: list[str] | None) -> bool:
    if not filters:
        return True

    tags = item.get("diet_tags", [])
    tag_set = set()
    if isinstance(tags, list):
        tag_set = {str(tag).strip().lower() for tag in tags if str(tag).strip()}
    inferred_tag_set = _infer_diet_tags_from_item(item)
    combined_tags = tag_set.union(inferred_tag_set)
    return set(filters).issubset(combined_tags)


def rank_and_partition(
    user_ingredients: list[str],
    database_results: list[dict[str, Any]],
    generated_recipes: list[dict[str, Any]],
    top_k: int = 5,
    on_hand_target: int = 5,
    filters: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Rank hybrid results and split into on-hand and related sections."""

    on_hand: list[dict[str, Any]] = []
    related: list[dict[str, Any]] = []

    for db_item in database_results:
        if not _matches_filters(db_item, filters):
            continue
        enriched = dict(db_item)
        enriched["score"] = round(_score_database_item(enriched), 4)
        related.append(enriched)

    for generated_recipe in generated_recipes:
        if not _matches_filters(generated_recipe, filters):
            continue
        generated = dict(generated_recipe)
        generated["score"] = round(_score_generated_item(generated, user_ingredients), 4)
        on_hand.append(generated)

    on_hand.sort(
        key=lambda item: (
            float(item.get("score", 0.0)),
            -len(item.get("missing_ingredients", [])),
            item.get("title", "").lower(),
        ),
        reverse=True,
    )
    related.sort(
        key=lambda item: (
            float(item.get("score", 0.0)),
            -len(item.get("missing_ingredients", [])),
            item.get("title", "").lower(),
        ),
        reverse=True,
    )

    return {
        "on_hand_recipes": on_hand[: max(1, on_hand_target)],
        "related_recipes": related[: max(1, top_k)],
    }
