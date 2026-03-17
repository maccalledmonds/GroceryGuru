"""Tests for recipe scoring and recommendation."""

from __future__ import annotations

from pantrypal.app.models import load_recipes
from pantrypal.app.utils.scoring import recommend_recipes


RECIPES = load_recipes()


def test_recommend_empty_input_returns_empty() -> None:
    assert recommend_recipes([], RECIPES, top_k=5) == []


def test_recommend_no_matches_returns_empty() -> None:
    results = recommend_recipes(["zzqv_ingredient", "xxk9_ingredient"], RECIPES, top_k=5)
    assert results == []


def test_recommend_full_match_prioritized() -> None:
    query = ["egg", "spinach", "feta cheese", "olive oil", "salt", "black pepper"]
    results = recommend_recipes(query, RECIPES, top_k=3)

    assert results
    assert results[0]["title"] == "Spinach Feta Omelette"
    assert results[0]["exact_match_count"] >= 6


def test_recommend_partial_match_present() -> None:
    query = ["spinach", "feta cheese"]
    results = recommend_recipes(query, RECIPES, top_k=5)

    assert results
    assert any(item["exact_match_count"] >= 1 for item in results)


def test_recommend_respects_dietary_filters() -> None:
    query = ["egg", "spinach", "feta cheese"]
    results = recommend_recipes(query, RECIPES, top_k=5, filters=["vegan"])

    assert all("vegan" in item["diet_tags"] for item in results)


def test_recommend_prioritizes_core_ingredients_over_spices() -> None:
    query = ["salmon", "asparagus", "salt", "black pepper"]
    results = recommend_recipes(query, RECIPES, top_k=5)

    assert results
    assert results[0]["title"] == "Baked Salmon and Asparagus"
