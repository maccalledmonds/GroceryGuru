"""Tests for AI recommender parsing and fallback behavior."""

from __future__ import annotations

from pantrypal.app.models import load_recipes
from pantrypal.app.utils.ai_recommender import AIRecommender
from pantrypal.app.utils.groq_client import GroqClientError


class _FakeRetriever:
    def __init__(self, recipe_ids: list[int]):
        self._recipe_ids = recipe_ids

    def retrieve(self, query: str, top_n: int, filters: list[str] | None = None):
        selected = self._recipe_ids[:top_n]
        return [type("Retrieved", (), {"recipe_id": rid, "similarity": 0.9})() for rid in selected]


class _FakeGroqClient:
    def __init__(self, payload):
        self._payload = payload

    def generate_rankings(self, system_prompt: str, user_prompt: str):
        return self._payload


class _FailingGroqClient:
    def generate_rankings(self, system_prompt: str, user_prompt: str):
        raise GroqClientError("simulated failure")


def test_ai_recommender_parses_ranked_output() -> None:
    recipes = load_recipes()
    candidate_ids = [recipe.id for recipe in recipes[:4]]

    groq_payload = {
        "recommendations": [
            {"recipe_id": candidate_ids[1], "explanation": "Best protein match from available ingredients."},
            {"recipe_id": candidate_ids[0], "explanation": "Uses several pantry staples effectively."},
        ]
    }

    recommender = AIRecommender(
        retriever=_FakeRetriever(candidate_ids),
        groq_client=_FakeGroqClient(groq_payload),
        rag_top_n=4,
    )

    result = recommender.recommend(
        user_ingredients=["egg", "spinach", "feta cheese"],
        recipes=recipes,
        top_k=2,
        filters=None,
    )

    assert result.used_fallback is False
    assert len(result.recipes) == 2
    assert result.recipes[0]["id"] == candidate_ids[1]
    assert result.recipes[0]["explanation"]


def test_ai_recommender_invalid_payload_falls_back() -> None:
    recipes = load_recipes()
    candidate_ids = [recipe.id for recipe in recipes[:3]]

    recommender = AIRecommender(
        retriever=_FakeRetriever(candidate_ids),
        groq_client=_FakeGroqClient({"wrong_key": []}),
        rag_top_n=3,
    )

    result = recommender.recommend(
        user_ingredients=["salmon", "asparagus"],
        recipes=recipes,
        top_k=2,
        filters=None,
    )

    assert result.used_fallback is True
    assert result.fallback_reason == "groq_failure"
    assert result.recipes


def test_ai_recommender_groq_failure_falls_back() -> None:
    recipes = load_recipes()
    candidate_ids = [recipe.id for recipe in recipes[:3]]

    recommender = AIRecommender(
        retriever=_FakeRetriever(candidate_ids),
        groq_client=_FailingGroqClient(),
        rag_top_n=3,
    )

    result = recommender.recommend(
        user_ingredients=["tomato", "basil"],
        recipes=recipes,
        top_k=2,
        filters=None,
    )

    assert result.used_fallback is True
    assert result.fallback_reason == "groq_failure"
    assert len(result.recipes) <= 2
