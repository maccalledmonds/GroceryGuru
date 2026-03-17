"""Ranking and partitioning for hybrid recipe recommendations."""

from __future__ import annotations

from typing import Any


def _score_database_item(item: dict[str, Any]) -> float:
    match_score = float(item.get("match_score", 0.0))
    missing_count = len(item.get("missing_ingredients", []))
    penalty = min(0.25, 0.05 * missing_count)
    return max(0.0, min(1.0, match_score - penalty))


def _score_generated_item(item: dict[str, Any], user_ingredients: list[str]) -> float:
    user_set = {ingredient.strip().lower() for ingredient in user_ingredients if ingredient.strip()}
    generated_ingredients = {
        ingredient.strip().lower() for ingredient in item.get("ingredients", []) if ingredient.strip()
    }

    overlap = len(user_set.intersection(generated_ingredients))
    coverage = overlap / len(user_set) if user_set else 0.0
    missing_count = len(item.get("missing_ingredients", []))
    missing_penalty = min(0.20, 0.04 * missing_count)
    score = 0.85 * coverage + 0.15 * (1.0 - missing_penalty)
    return max(0.0, min(1.0, score))


def rank_and_partition(
    user_ingredients: list[str],
    database_results: list[dict[str, Any]],
    generated_recipes: list[dict[str, Any]],
    top_k: int = 5,
    on_hand_target: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Rank hybrid results and split into on-hand and related sections."""

    on_hand: list[dict[str, Any]] = []
    related: list[dict[str, Any]] = []

    for db_item in database_results:
        enriched = dict(db_item)
        enriched["score"] = round(_score_database_item(enriched), 4)
        related.append(enriched)

    for generated_recipe in generated_recipes:
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
