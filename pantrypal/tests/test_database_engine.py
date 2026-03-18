"""Tests for database engine canonical integrity behavior."""

from __future__ import annotations

from pantrypal.app.utils.database_engine import (
    _RecipeSearchRecord,
    _validated_recipe_normalized_ingredients,
    get_canonical_integrity_metrics,
    search_recipes,
    warm_recipe_cache,
)


def test_validated_recipe_normalized_ingredients_canonicalizes_alias_forms() -> None:
    values = ["garlic cloves", "extra virgin olive oil", "tomatoes", "garlic"]

    normalized = _validated_recipe_normalized_ingredients(values)

    assert "garlic" in normalized
    assert "olive oil" in normalized
    assert "tomato" in normalized
    assert normalized.count("garlic") == 1


def test_validated_recipe_normalized_ingredients_updates_metrics_accumulator() -> None:
    metrics = {
        "recipes_indexed": 0,
        "recipes_with_repairs": 0,
        "canonicalized_values": 0,
        "unknown_values": 0,
    }

    _ = _validated_recipe_normalized_ingredients(["garlic cloves", "mystery ingredient"], metrics=metrics)

    assert metrics["recipes_with_repairs"] == 1
    assert metrics["canonicalized_values"] >= 1
    assert metrics["unknown_values"] >= 1


def test_get_canonical_integrity_metrics_returns_structured_counts() -> None:
    warm_recipe_cache()
    metrics = get_canonical_integrity_metrics()

    assert set(metrics.keys()) == {
        "recipes_indexed",
        "recipes_with_repairs",
        "canonicalized_values",
        "unknown_values",
    }
    assert metrics["recipes_indexed"] >= 0


def test_search_recipes_excludes_non_meal_titles(monkeypatch) -> None:
    fake_index = (
        _RecipeSearchRecord(
            id=1,
            title="Quick Garlic Sauce",
            ingredients=["garlic", "olive oil", "salt"],
            instructions="mix",
            diet_tags=["vegan"],
            ingredient_set={"garlic", "olive oil", "salt"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Garlic Spinach Bowl",
            ingredients=["garlic", "spinach", "olive oil"],
            instructions="cook",
            diet_tags=["vegan"],
            ingredient_set={"garlic", "spinach", "olive oil"},
        ),
    )

    monkeypatch.setattr(
        "pantrypal.app.utils.database_engine._recipe_search_index",
        lambda: fake_index,
    )

    results = search_recipes(["garlic", "spinach"], top_k=5)

    assert results
    assert all("sauce" not in item["title"].lower() for item in results)
    assert results[0]["title"] == "Garlic Spinach Bowl"


def test_search_recipes_ranks_by_overlap_then_missing(monkeypatch) -> None:
    fake_index = (
        _RecipeSearchRecord(
            id=1,
            title="Spinach Egg Skillet",
            ingredients=["spinach", "egg", "olive oil"],
            instructions="cook",
            diet_tags=["vegetarian"],
            ingredient_set={"spinach", "egg", "olive oil"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Spinach Egg Toast",
            ingredients=["spinach", "egg", "bread", "olive oil"],
            instructions="cook",
            diet_tags=["vegetarian"],
            ingredient_set={"spinach", "egg", "bread", "olive oil"},
        ),
    )

    monkeypatch.setattr(
        "pantrypal.app.utils.database_engine._recipe_search_index",
        lambda: fake_index,
    )

    results = search_recipes(["spinach", "egg", "olive oil"], top_k=5)

    assert results
    assert results[0]["title"] == "Spinach Egg Skillet"
    assert len(results[0]["missing_ingredients"]) <= len(results[1]["missing_ingredients"])
