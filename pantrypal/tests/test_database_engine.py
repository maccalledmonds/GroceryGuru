"""Tests for database engine canonical integrity behavior."""

from __future__ import annotations

from pantrypal.app.utils.database_engine import (
    _RecipeSearchRecord,
    _ingredient_weight,
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


def test_validated_recipe_normalized_ingredients_excludes_special_equipment() -> None:
    values = ["special equipment: blender", "egg", "equipment: sheet pan"]

    normalized = _validated_recipe_normalized_ingredients(values)

    assert normalized == ["egg"]


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
            display_ingredients=["garlic", "olive oil", "salt"],
            normalized_ingredients=["garlic", "olive oil", "salt"],
            instructions="mix",
            diet_tags=["vegan"],
            servings=2,
            ingredient_set={"garlic", "olive oil", "salt"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Garlic Spinach Bowl",
            display_ingredients=["garlic", "spinach", "olive oil"],
            normalized_ingredients=["garlic", "spinach", "olive oil"],
            instructions="cook",
            diet_tags=["vegan"],
            servings=2,
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
            display_ingredients=["spinach", "egg", "olive oil"],
            normalized_ingredients=["spinach", "egg", "olive oil"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
            ingredient_set={"spinach", "egg", "olive oil"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Spinach Egg Toast",
            display_ingredients=["spinach", "egg", "bread", "olive oil"],
            normalized_ingredients=["spinach", "egg", "bread", "olive oil"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
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


def test_ingredient_weight_prefers_high_importance_over_low_importance() -> None:
    assert _ingredient_weight("salt") < _ingredient_weight("chicken")
    assert _ingredient_weight("water") < _ingredient_weight("rice")


def test_search_recipes_diversifies_similar_candidates(monkeypatch) -> None:
    fake_index = (
        _RecipeSearchRecord(
            id=1,
            title="Egg Fried Rice",
            display_ingredients=["egg", "rice", "salt", "black pepper"],
            normalized_ingredients=["egg", "rice", "salt", "black pepper"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
            ingredient_set={"egg", "rice", "salt", "black pepper"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Steamed Jasmine Rice and Egg",
            display_ingredients=["egg", "rice", "water", "salt"],
            normalized_ingredients=["egg", "rice", "water", "salt"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
            ingredient_set={"egg", "rice", "water", "salt"},
        ),
        _RecipeSearchRecord(
            id=3,
            title="Egg Noodle Bowl",
            display_ingredients=["egg", "noodle", "scallion", "sesame oil"],
            normalized_ingredients=["egg", "noodle", "scallion", "sesame oil"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
            ingredient_set={"egg", "noodle", "scallion", "sesame oil"},
        ),
    )

    monkeypatch.setattr(
        "pantrypal.app.utils.database_engine._recipe_search_index",
        lambda: fake_index,
    )

    results = search_recipes(["egg", "rice", "water", "salt"], top_k=2)

    assert len(results) == 2
    titles = {item["title"] for item in results}
    assert "Egg Noodle Bowl" in titles


def test_search_recipes_prefers_multi_core_overlap_over_side_only_match(monkeypatch) -> None:
    fake_index = (
        _RecipeSearchRecord(
            id=1,
            title="Steamed Rice",
            display_ingredients=["rice", "salt", "water"],
            normalized_ingredients=["rice", "salt", "water"],
            instructions="cook",
            diet_tags=["vegetarian"],
            servings=2,
            ingredient_set={"rice", "salt", "water"},
        ),
        _RecipeSearchRecord(
            id=2,
            title="Chicken Rice Skillet",
            display_ingredients=["chicken", "rice", "garlic", "olive oil"],
            normalized_ingredients=["chicken", "rice", "garlic", "olive oil"],
            instructions="cook",
            diet_tags=[],
            servings=2,
            ingredient_set={"chicken", "rice", "garlic", "olive oil"},
        ),
    )

    monkeypatch.setattr(
        "pantrypal.app.utils.database_engine._recipe_search_index",
        lambda: fake_index,
    )

    results = search_recipes(["chicken", "rice", "salt", "water"], top_k=2)

    assert results
    assert results[0]["title"] == "Chicken Rice Skillet"
