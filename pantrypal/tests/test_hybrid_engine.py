"""Tests for hybrid recommendation orchestration."""

from __future__ import annotations

from pantrypal.app.utils.hybrid_engine import HybridRecommendationEngine
from pantrypal.app.utils.llm_engine import LLMRecipeEngineError


class _FakeLLMEngine:
    def generate_recipes(self, user_ingredients: list[str], count: int = 5):
        return [
            {
                "type": "generated",
                "title": f"Ingredient Stir Fry {idx + 1}",
                "ingredients": list(user_ingredients),
                "instructions": ["Heat pan", "Cook ingredients", "Serve"],
                "missing_ingredients": [],
            }
            for idx in range(count)
        ]


class _FailingLLMEngine:
    def generate_recipes(self, user_ingredients: list[str], count: int = 5):
        _ = user_ingredients
        _ = count
        raise LLMRecipeEngineError("simulated failure")


def test_hybrid_engine_returns_partitioned_results() -> None:
    engine = HybridRecommendationEngine(llm_engine=_FakeLLMEngine())

    result = engine.recommend_recipes(user_ingredients=["eggs", "spinach"], top_k=3)

    assert result.normalized_ingredients
    assert isinstance(result.on_hand_recipes, list)
    assert isinstance(result.related_recipes, list)
    assert result.on_hand_recipes
    assert len(result.on_hand_recipes) == 5
    assert {item["type"] for item in result.on_hand_recipes} == {"generated"}


def test_hybrid_engine_falls_back_to_database() -> None:
    engine = HybridRecommendationEngine(llm_engine=_FailingLLMEngine())

    result = engine.recommend_recipes(user_ingredients=["eggs", "spinach"], top_k=3)

    assert result.used_fallback is True
    assert result.fallback_reason == "llm_generation_failed"
    assert result.related_recipes or result.on_hand_recipes
