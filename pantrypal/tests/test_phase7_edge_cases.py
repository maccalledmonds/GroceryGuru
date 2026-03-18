"""Phase 7 edge-case hardening tests."""

from __future__ import annotations

import pytest

from pantrypal.app.utils.database_engine import search_recipes
from pantrypal.app.utils.hybrid_engine import HybridRecommendationEngine
from pantrypal.app.utils.normalization import normalize_ingredient, normalize_ingredients


class _EchoLLMEngine:
    def generate_recipes(self, user_ingredients: list[str], count: int = 5):
        _ = count
        return [
            {
                "type": "generated",
                "title": "Echo Recipe",
                "ingredients": list(user_ingredients),
                "instructions": ["Mix"],
                "missing_ingredients": [],
            }
        ]


def test_phase7_empty_pantry_rejected() -> None:
    engine = HybridRecommendationEngine(llm_engine=_EchoLLMEngine())

    with pytest.raises(ValueError, match="ingredients list must not be empty"):
        engine.recommend_recipes(user_ingredients=["   ", ""], top_k=3)


def test_phase7_large_ingredient_list_deterministic_and_deduped() -> None:
    large_inputs = [f"ingredient_{idx}" for idx in range(200)]
    large_inputs.extend(["Tomatoes", "tomato", "fresh tomatoes", "Tomatoes"])

    normalized = normalize_ingredients(large_inputs)

    assert normalized
    assert "tomato" in normalized
    assert normalized.count("tomato") == 1
    # Ensure broad list processing remains stable (dedupe should reduce count).
    assert len(normalized) <= len(large_inputs)


def test_phase7_unknown_ingredient_fallback_is_preserved() -> None:
    mapped = normalize_ingredient("mystery powder")

    assert mapped.normalized == "mystery powder"
    assert mapped.canonical_name is None
    assert mapped.canonical_id is None


def test_phase7_ambiguous_ingredient_not_force_mapped() -> None:
    mapped = normalize_ingredient("pepper")

    assert mapped.normalized == "pepper"
    assert mapped.canonical_name is None
    assert mapped.canonical_id is None


def test_phase7_database_requires_at_least_one_overlap() -> None:
    results = search_recipes(["zzqv_ingredient", "xxk9_ingredient"], top_k=5)

    assert results == []
