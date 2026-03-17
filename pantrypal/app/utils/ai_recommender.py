"""AI recommendation orchestration using semantic retrieval + Groq ranking."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import time
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from ..config import RAG_TOP_N
from ..models import Recipe, recipe_to_dict
from .groq_client import GroqClient, GroqClientError, GroqTimeoutError
from .rag_retriever import SemanticRecipeRetriever
from .scoring import recommend_recipes

LOGGER = logging.getLogger(__name__)


class RankedRecipe(BaseModel):
    recipe_id: int = Field(..., description="Recipe id from candidate list")
    explanation: str = Field(..., min_length=1, max_length=300)


class RankedRecipePayload(BaseModel):
    recommendations: list[RankedRecipe]


@dataclass(slots=True)
class AIRecommendResult:
    recipes: list[dict[str, Any]]
    used_fallback: bool
    fallback_reason: str | None = None


class AIRecommender:
    """Coordinates retrieval, grounded prompting, JSON parsing, and fallback."""

    def __init__(
        self,
        retriever: SemanticRecipeRetriever,
        groq_client: GroqClient,
        rag_top_n: int = RAG_TOP_N,
    ) -> None:
        self.retriever = retriever
        self.groq_client = groq_client
        self.rag_top_n = max(1, rag_top_n)

    def recommend(
        self,
        user_ingredients: list[str],
        recipes: list[Recipe],
        top_k: int,
        filters: list[str] | None,
    ) -> AIRecommendResult:
        deterministic = recommend_recipes(
            user_ingredients=user_ingredients,
            recipes=recipes,
            top_k=top_k,
            filters=filters,
        )

        retrieval_query = ", ".join(user_ingredients)
        candidates = self.retriever.retrieve(
            query=retrieval_query,
            top_n=max(top_k, self.rag_top_n),
            filters=filters,
        )
        if not candidates:
            LOGGER.warning("AI fallback triggered: no RAG candidates")
            return AIRecommendResult(recipes=deterministic, used_fallback=True, fallback_reason="no_candidates")

        recipes_by_id = {recipe.id: recipe for recipe in recipes}
        candidate_recipes: list[Recipe] = []
        for candidate in candidates:
            recipe = recipes_by_id.get(candidate.recipe_id)
            if recipe is not None:
                candidate_recipes.append(recipe)

        if not candidate_recipes:
            LOGGER.warning("AI fallback triggered: no candidate recipes after id mapping")
            return AIRecommendResult(recipes=deterministic, used_fallback=True, fallback_reason="missing_candidates")

        try:
            generation_start = time.perf_counter()
            generated = self.groq_client.generate_rankings(
                system_prompt=self._system_prompt(),
                user_prompt=self._user_prompt(
                    user_ingredients=user_ingredients,
                    filters=filters,
                    top_k=top_k,
                    candidate_recipes=candidate_recipes,
                ),
            )
            elapsed_ms = int((time.perf_counter() - generation_start) * 1000)
            LOGGER.info("Groq generation completed in %dms", elapsed_ms)

            ranked_ids_with_reason = self._parse_ranked_ids(generated, {recipe.id for recipe in candidate_recipes})
            ai_ranked = self._hydrate_ranked_results(
                ranked_ids_with_reason=ranked_ids_with_reason,
                recipes_by_id=recipes_by_id,
                user_ingredients=user_ingredients,
                top_k=top_k,
                fallback=deterministic,
            )
            return AIRecommendResult(recipes=ai_ranked, used_fallback=False)
        except (GroqClientError, GroqTimeoutError, ValidationError, ValueError) as exc:
            LOGGER.warning("AI fallback triggered due to Groq/parsing issue: %s", exc)
            return AIRecommendResult(recipes=deterministic, used_fallback=True, fallback_reason="groq_failure")

    def _parse_ranked_ids(
        self,
        payload: dict[str, Any],
        allowed_recipe_ids: set[int],
    ) -> list[tuple[int, str]]:
        parsed = RankedRecipePayload.model_validate(payload)

        seen: set[int] = set()
        ranked: list[tuple[int, str]] = []
        for item in parsed.recommendations:
            if item.recipe_id in seen:
                continue
            if item.recipe_id not in allowed_recipe_ids:
                continue
            seen.add(item.recipe_id)
            ranked.append((item.recipe_id, item.explanation.strip()))

        if not ranked:
            raise ValueError("No valid recipe ids in model response")
        return ranked

    def _hydrate_ranked_results(
        self,
        ranked_ids_with_reason: list[tuple[int, str]],
        recipes_by_id: dict[int, Recipe],
        user_ingredients: list[str],
        top_k: int,
        fallback: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        added_ids: set[int] = set()

        for recipe_id, explanation in ranked_ids_with_reason:
            recipe = recipes_by_id.get(recipe_id)
            if recipe is None:
                continue
            rendered = self._render_recipe(recipe=recipe, user_ingredients=user_ingredients)
            rendered["explanation"] = explanation
            results.append(rendered)
            added_ids.add(recipe_id)
            if len(results) >= top_k:
                return results

        for item in fallback:
            if item["id"] in added_ids:
                continue
            fallback_copy = dict(item)
            fallback_copy.setdefault("explanation", None)
            results.append(fallback_copy)
            if len(results) >= top_k:
                break

        return results

    def _render_recipe(self, recipe: Recipe, user_ingredients: list[str]) -> dict[str, Any]:
        base = recipe_to_dict(recipe)

        user_set = set(user_ingredients)
        recipe_set = set(recipe.ingredients_normalized or recipe.ingredients)
        matched = user_set.intersection(recipe_set)

        exact_match_count = len(matched)
        coverage = (len(matched) / len(recipe_set)) if recipe_set else 0.0
        ingredient_match_ratio = (len(matched) / len(user_set)) if user_set else 0.0
        score = 0.75 * coverage + 0.25 * ingredient_match_ratio

        base.update(
            {
                "exact_match_count": exact_match_count,
                "coverage": coverage,
                "ingredient_match_ratio": ingredient_match_ratio,
                "score": score,
                "match_percentage": round(coverage * 100.0, 1),
                "explanation": None,
            }
        )
        return base

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a recipe ranking engine. "
            "Use only the provided candidate recipes. "
            "Never invent new recipes or ids. "
            "Return strict JSON with key recommendations."
        )

    @staticmethod
    def _user_prompt(
        user_ingredients: list[str],
        filters: list[str] | None,
        top_k: int,
        candidate_recipes: list[Recipe],
    ) -> str:
        candidates_payload = [
            {
                "recipe_id": recipe.id,
                "title": recipe.title,
                "ingredients": recipe.ingredients_normalized or recipe.ingredients,
                "diet_tags": recipe.diet_tags,
                "instructions": recipe.instructions,
                "nutrition": {
                    "calories": recipe.nutrition.calories,
                    "protein": recipe.nutrition.protein,
                    "fat": recipe.nutrition.fat,
                    "carbs": recipe.nutrition.carbs,
                },
            }
            for recipe in candidate_recipes
        ]

        request_payload = {
            "ingredients": user_ingredients,
            "filters": filters or [],
            "top_k": top_k,
            "instructions": (
                "Rank the best recipes for the user and explain each in one concise sentence. "
                "Only return recipe ids from the candidate list."
            ),
            "response_schema": {
                "recommendations": [
                    {
                        "recipe_id": "integer from candidate list",
                        "explanation": "short grounded reason",
                    }
                ]
            },
            "candidates": candidates_payload,
        }

        return json.dumps(request_payload, ensure_ascii=True)
