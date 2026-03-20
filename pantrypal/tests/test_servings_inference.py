from __future__ import annotations

from pantrypal.data.enrich_servings import infer_servings


def test_infer_servings_prefers_explicit_instruction_yield() -> None:
    recipe = {
        "title": "Simple Pasta",
        "instructions": "Bring water to a boil. Makes 6 servings.",
        "ingredients": ["1 lb spaghetti", "2 tbsp olive oil", "salt"],
    }

    servings, rule = infer_servings(recipe)

    assert servings == 6
    assert rule == "explicit_yield"


def test_infer_servings_uses_type_and_amount_signal_when_no_explicit_yield() -> None:
    recipe = {
        "title": "Chocolate Cake",
        "instructions": "Mix and bake until done.",
        "ingredients": [
            "2 cups flour",
            "1 cup sugar",
            "3 eggs",
            "1/2 cup butter",
            "1 tsp baking powder",
            "1 cup milk",
        ],
    }

    servings, rule = infer_servings(recipe)

    assert servings >= 8
    assert rule == "type_plus_amount"


def test_infer_servings_falls_back_to_ingredient_count() -> None:
    recipe = {
        "title": "Green Medley",
        "instructions": "Combine ingredients and serve.",
        "ingredients": ["spinach", "kale", "olive oil", "lemon", "salt"],
    }

    servings, rule = infer_servings(recipe)

    assert servings == 3
    assert rule == "ingredient_count_fallback"
