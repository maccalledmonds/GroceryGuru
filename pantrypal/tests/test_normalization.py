"""Tests for ingredient normalization."""

from __future__ import annotations

from pantrypal.app.utils.normalization import normalize_ingredients, with_default_pantry_ingredients


def test_normalize_typo_heavy_input() -> None:
    raw = ["2 Tomatoes", "cheddar chese", "chikn breast"]
    normalized = normalize_ingredients(raw)

    assert "tomato" in normalized
    assert "cheddar cheese" in normalized
    assert "chicken breast" in normalized


def test_normalize_empty_input() -> None:
    assert normalize_ingredients([]) == []


def test_normalize_preserves_unmatched_but_cleaned() -> None:
    raw = ["1 xyzingredient"]
    normalized = normalize_ingredients(raw)

    assert normalized
    assert normalized[0] == "xyzingredient"


def test_with_default_pantry_ingredients_adds_staples() -> None:
    ingredients = ["Egg", " spinach "]

    merged = with_default_pantry_ingredients(ingredients)

    assert "Egg" in merged
    assert "spinach" in merged
    assert "salt" in merged
    assert "black pepper" in merged
    assert "water" in merged


def test_with_default_pantry_ingredients_deduplicates_case_insensitive() -> None:
    ingredients = ["salt", "Salt", "black pepper", "WATER"]

    merged = with_default_pantry_ingredients(ingredients)

    lowered = [item.lower() for item in merged]
    assert lowered.count("salt") == 1
    assert lowered.count("black pepper") == 1
    assert lowered.count("water") == 1


def test_normalize_chicken_prefers_whole_word_match_over_chickpea() -> None:
    normalized = normalize_ingredients(["chicken"])

    assert normalized
    assert normalized[0] == "chicken breast"
