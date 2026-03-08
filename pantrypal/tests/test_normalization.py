"""Tests for ingredient normalization."""

from __future__ import annotations

from app.utils.normalization import normalize_ingredients


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
