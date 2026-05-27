"""Tests for scraper.parse — JSON-LD Recipe extraction & non-meal filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from scraper.parse import parse_recipe_html

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_meal_recipe_extracts_expected_fields() -> None:
    parsed = parse_recipe_html(
        _load("sample_recipe.html"),
        source_url="https://example.test/recipe",
    )
    assert parsed is not None
    assert parsed.title == "Roasted Chicken Thighs With Lemon and Herbs"
    assert parsed.is_meal_candidate is True
    assert parsed.servings == 4
    assert parsed.recipe_category == ["main course"]
    assert parsed.nutrition["calories"] == pytest.approx(520.0)
    assert parsed.nutrition["protein"] == pytest.approx(42.0)
    assert len(parsed.ingredients_raw) == 8
    assert parsed.ingredients_raw[0].startswith("8 bone-in")
    assert "Preheat the oven" in parsed.instructions


def test_parse_sauce_recipe_is_rejected() -> None:
    parsed = parse_recipe_html(
        _load("sample_sauce.html"),
        source_url="https://example.test/sauce",
    )
    assert parsed is not None
    assert parsed.is_meal_candidate is False
    assert parsed.rejection_reason is not None
    assert "sauce" in parsed.rejection_reason


def test_parse_page_without_recipe_returns_none() -> None:
    parsed = parse_recipe_html(
        _load("sample_no_recipe.html"),
        source_url="https://example.test/article",
    )
    assert parsed is None
