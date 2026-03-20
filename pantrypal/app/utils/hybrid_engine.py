"""Hybrid recommendation pipeline combining database and LLM engines."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import logging
from typing import Any

from .database_engine import search_recipes
from .llm_engine import LLMRecipeEngine, LLMRecipeEngineError
from .normalization import normalize_ingredients, with_default_pantry_ingredients
from .ranking import rank_and_partition
import weave

LOGGER = logging.getLogger(__name__)

ON_HAND_LLM_TARGET = 5


@dataclass(slots=True)
class HybridRecommendationResult:
    """Return contract for hybrid recommendation orchestration."""

    normalized_ingredients: list[str]
    on_hand_recipes: list[dict[str, Any]]
    related_recipes: list[dict[str, Any]]
    used_fallback: bool
    fallback_reason: str | None = None


class HybridRecommendationEngine:
    """Coordinates normalization, retrieval/generation, and ranking."""

    def __init__(self, llm_engine: LLMRecipeEngine | None = None) -> None:
        self.llm_engine = llm_engine

    @weave.op()
    def recommend_recipes(
        self,
        user_ingredients: list[str],
        top_k: int = 5,
        filters: list[str] | None = None,
    ) -> HybridRecommendationResult:
        cleaned = [item.strip() for item in user_ingredients if item and item.strip()]
        if not cleaned:
            raise ValueError("ingredients list must not be empty")

        normalized = normalize_ingredients(with_default_pantry_ingredients(cleaned))
        if not normalized:
            raise ValueError("No valid ingredients were recognized")

        on_hand_target = ON_HAND_LLM_TARGET

        fallback_reason: str | None = None
        generated_recipes: list[dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=2) as executor:
            db_future = executor.submit(
                search_recipes,
                normalized,
                max(top_k * 2, top_k),
                filters,
            )
            llm_future = executor.submit(self._safe_generate_many, normalized, on_hand_target)

            database_results = db_future.result()
            generated_recipes, fallback_reason = llm_future.result()

        ranked = rank_and_partition(
            user_ingredients=normalized,
            database_results=database_results,
            generated_recipes=generated_recipes,
            top_k=top_k,
            on_hand_target=on_hand_target,
            filters=filters,
        )

        return HybridRecommendationResult(
            normalized_ingredients=normalized,
            on_hand_recipes=ranked["on_hand_recipes"],
            related_recipes=ranked["related_recipes"],
            used_fallback=fallback_reason is not None,
            fallback_reason=fallback_reason,
        )

    @weave.op()
    def _safe_generate_many(
        self,
        normalized_ingredients: list[str],
        target_count: int,
    ) -> tuple[list[dict[str, Any]], str | None]:
        if self.llm_engine is None:
            return [], "missing_api_key"

        try:
            return self.llm_engine.generate_recipes(normalized_ingredients, count=target_count), None
        except LLMRecipeEngineError as exc:
            LOGGER.warning("LLM generation failed; using database-only fallback: %s", exc)
            return [], "llm_generation_failed"
