"""Tests for LLM recipe generation diversity selection."""

from __future__ import annotations

from types import MethodType

from pantrypal.app.utils.llm_engine import LLMRecipeEngine, _recipe_similarity


def _build_engine_with_stubbed_generator(recipes: list[dict[str, object]]) -> LLMRecipeEngine:
    engine = LLMRecipeEngine.__new__(LLMRecipeEngine)
    cursor = {"index": 0}

    def _fake_generate_recipe(self, user_ingredients: list[str], avoid_recipes: list[dict[str, object]] | None = None):
        _ = user_ingredients
        _ = avoid_recipes
        idx = cursor["index"]
        cursor["index"] += 1
        return dict(recipes[idx % len(recipes)])

    engine.generate_recipe = MethodType(_fake_generate_recipe, engine)
    return engine


def test_generate_recipes_prefers_diverse_results() -> None:
    recipe_stream = [
        {
            "type": "generated",
            "title": "Creamy Garlic Pasta",
            "ingredients": ["pasta", "garlic", "cream", "parmesan"],
            "instructions": ["Boil pasta", "Stir in sauce"],
            "missing_ingredients": [],
        },
        {
            "type": "generated",
            "title": "Buttery Parmesan Pasta",
            "ingredients": ["pasta", "garlic", "butter", "parmesan"],
            "instructions": ["Boil pasta", "Add butter"],
            "missing_ingredients": [],
        },
        {
            "type": "generated",
            "title": "Spicy Lentil Curry",
            "ingredients": ["lentils", "onion", "tomato", "curry powder"],
            "instructions": ["Simmer lentils", "Finish curry"],
            "missing_ingredients": ["curry powder"],
        },
        {
            "type": "generated",
            "title": "Crunchy Chickpea Salad",
            "ingredients": ["chickpeas", "cucumber", "tomato", "lemon"],
            "instructions": ["Chop ingredients", "Toss"],
            "missing_ingredients": ["lemon"],
        },
    ]

    engine = _build_engine_with_stubbed_generator(recipe_stream)

    generated = engine.generate_recipes(
        user_ingredients=["pasta", "garlic", "tomato", "chickpeas", "lentils"],
        count=3,
    )

    assert len(generated) == 3

    max_pair_similarity = 0.0
    for left_idx, left_recipe in enumerate(generated):
        for right_recipe in generated[left_idx + 1 :]:
            max_pair_similarity = max(max_pair_similarity, _recipe_similarity(left_recipe, right_recipe))

    assert max_pair_similarity < 0.7


def test_generate_recipes_passes_prior_candidates_for_diversity_prompting() -> None:
    engine = LLMRecipeEngine.__new__(LLMRecipeEngine)
    avoid_lengths: list[int] = []

    def _fake_generate_recipe(self, user_ingredients: list[str], avoid_recipes: list[dict[str, object]] | None = None):
        _ = user_ingredients
        avoid_lengths.append(len(avoid_recipes or []))
        return {
            "type": "generated",
            "title": f"Recipe {len(avoid_lengths)}",
            "ingredients": ["egg", f"spice-{len(avoid_lengths)}"],
            "instructions": ["Cook"],
            "missing_ingredients": [],
        }

    engine.generate_recipe = MethodType(_fake_generate_recipe, engine)

    generated = engine.generate_recipes(user_ingredients=["egg", "rice"], count=3)

    assert len(generated) == 3
    assert avoid_lengths[0] == 0
    assert max(avoid_lengths) >= 1
