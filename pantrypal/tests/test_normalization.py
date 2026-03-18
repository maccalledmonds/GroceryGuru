"""Tests for ingredient normalization."""

from __future__ import annotations

from pantrypal.app.utils.normalization import (
    normalize_ingredient,
    normalize_ingredients,
    with_default_pantry_ingredients,
)


def test_normalize_required_edge_cases() -> None:
    raw = [
        "Fresh Tomatoes",
        "chopped onions",
        "garlic cloves",
        "chicken breasts",
        "extra virgin olive oil",
        "soy sauce",
        "ice cream",
    ]
    normalized = normalize_ingredients(raw)

    assert "tomato" in normalized
    assert "onion" in normalized
    assert "garlic" in normalized
    assert "chicken" in normalized
    assert "olive oil" in normalized
    assert "soy sauce" in normalized
    assert "ice cream" in normalized


def test_normalize_empty_input() -> None:
    assert normalize_ingredients([]) == []


def test_normalize_preserves_unmatched_but_cleaned() -> None:
    raw = ["xyzingredient"]
    normalized = normalize_ingredients(raw)

    assert normalized
    assert normalized[0] == "xyzingredient"


def test_normalize_ingredient_internal_contract_when_unmapped() -> None:
    result = normalize_ingredient("mystery component")

    assert result.raw == "mystery component"
    assert result.normalized == "mystery component"
    assert result.canonical_name is None
    assert result.canonical_id is None


def test_normalize_ingredient_internal_contract_when_mapped() -> None:
    result = normalize_ingredient("garlic cloves")

    assert result.normalized == "garlic clove"
    assert result.canonical_name == "garlic"
    assert result.canonical_id is not None


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


def test_deduplicate_after_normalization() -> None:
    normalized = normalize_ingredients(["Tomatoes", "tomato", "fresh tomatoes"])

    assert normalized
    assert normalized == ["tomato"]
