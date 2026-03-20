"""Tests for ranking and partitioning logic."""

from __future__ import annotations

from pantrypal.app.utils.ranking import rank_and_partition


def test_generated_overlap_uses_canonicalized_ingredients() -> None:
    user_ingredients = ["chicken", "olive oil"]
    generated = [
        {
            "type": "generated",
            "title": "Test Chicken Dish",
            "ingredients": ["chicken breasts", "extra virgin olive oil"],
            "missing_ingredients": [],
            "instructions": ["Cook"],
        }
    ]

    ranked = rank_and_partition(
        user_ingredients=user_ingredients,
        database_results=[],
        generated_recipes=generated,
        top_k=3,
        on_hand_target=3,
    )

    assert ranked["on_hand_recipes"]
    assert ranked["on_hand_recipes"][0]["score"] > 0.9


def test_generated_filter_inference_allows_vegan_when_tags_missing() -> None:
    ranked = rank_and_partition(
        user_ingredients=["tofu", "olive oil"],
        database_results=[],
        generated_recipes=[
            {
                "type": "generated",
                "title": "Tofu Skillet",
                "ingredients": ["tofu", "olive oil", "spinach"],
                "missing_ingredients": [],
                "instructions": ["Cook"],
            }
        ],
        filters=["vegan"],
    )

    assert ranked["on_hand_recipes"]
    assert ranked["on_hand_recipes"][0]["title"] == "Tofu Skillet"


def test_generated_filter_inference_blocks_non_vegan_when_tags_missing() -> None:
    ranked = rank_and_partition(
        user_ingredients=["egg", "olive oil"],
        database_results=[],
        generated_recipes=[
            {
                "type": "generated",
                "title": "Egg Skillet",
                "ingredients": ["egg", "olive oil"],
                "missing_ingredients": [],
                "instructions": ["Cook"],
            }
        ],
        filters=["vegan"],
    )

    assert ranked["on_hand_recipes"] == []


def test_generated_score_penalizes_missing_ingredients() -> None:
    ranked = rank_and_partition(
        user_ingredients=["chicken", "olive oil"],
        database_results=[],
        generated_recipes=[
            {
                "type": "generated",
                "title": "Chicken Bowl",
                "ingredients": ["chicken", "olive oil"],
                "missing_ingredients": ["salt", "pepper"],
                "instructions": ["Cook"],
            }
        ],
    )

    assert ranked["on_hand_recipes"]
    # Base coverage is 1.0 (2/2); missing penalty is 0.08.
    assert abs(float(ranked["on_hand_recipes"][0]["score"]) - 0.92) < 1e-6


def test_database_score_ignores_low_importance_missing_ingredients() -> None:
    ranked = rank_and_partition(
        user_ingredients=["chicken", "rice", "salt", "black pepper", "water"],
        database_results=[
            {
                "type": "database",
                "title": "Chicken Rice Bowl",
                "ingredients": ["chicken", "rice", "salt", "black pepper", "water"],
                "missing_ingredients": ["salt", "black pepper", "water"],
                "match_score": 0.8,
            }
        ],
        generated_recipes=[],
    )

    assert ranked["related_recipes"]
    assert abs(float(ranked["related_recipes"][0]["score"]) - 0.8) < 1e-6
