"""Groq-powered recipe generation for hybrid recommendations."""
# pyright: reportMissingImports=false

from __future__ import annotations

from functools import lru_cache
import json
import logging
import os
import random
import re
from typing import Any, Literal
import weave

from pydantic import BaseModel, Field, ValidationError

try:  # pragma: no cover - exercised only when Groq package is available
    from groq import Groq  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Groq = None

LOGGER = logging.getLogger(__name__)

_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_MAX_ATTEMPTS_MULTIPLIER = 4
_MIN_NOVELTY_SCORE = 0.45
_FORM_CHANGE_RULES: dict[str, tuple[str, ...]] = {
    "rice": ("wrapper", "wrappers", "dough", "pastry", "dumpling skin", "spring roll"),
    "pasta": ("dough", "pastry", "wrapper", "wrappers", "spring roll"),
}


class LLMRecipeEngineError(RuntimeError):
    """Raised when the Groq generation flow fails."""


class IngredientFormIntegrityError(LLMRecipeEngineError):
    """Raised when the model transforms ingredients into disallowed forms."""


class GeneratedRecipePayload(BaseModel):
    """Validated generated recipe payload contract."""

    type: Literal["generated"] = "generated"
    title: str = Field(..., min_length=1)
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)


def _normalize_title(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _normalize_text_token_set(value: str) -> set[str]:
    return set(_WORD_PATTERN.findall(value.lower()))


def _normalize_ingredient_set(values: list[str]) -> set[str]:
    return {" ".join(_WORD_PATTERN.findall(item.lower())).strip() for item in values if item and item.strip()}


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left.intersection(right))
    union = len(left.union(right))
    return intersection / union if union else 0.0


def _recipe_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_ingredients = _normalize_ingredient_set(left.get("ingredients", []))
    right_ingredients = _normalize_ingredient_set(right.get("ingredients", []))
    left_title = _normalize_text_token_set(str(left.get("title", "")))
    right_title = _normalize_text_token_set(str(right.get("title", "")))

    ingredient_similarity = _jaccard_similarity(left_ingredients, right_ingredients)
    title_similarity = _jaccard_similarity(left_title, right_title)
    return max(ingredient_similarity, 0.6 * title_similarity)


def _coverage_score(recipe: dict[str, Any], user_ingredients: list[str]) -> float:
    user_set = _normalize_ingredient_set(user_ingredients)
    recipe_set = _normalize_ingredient_set(recipe.get("ingredients", []))
    if not user_set or not recipe_set:
        return 0.0
    return len(user_set.intersection(recipe_set)) / len(user_set)


def _recipe_fingerprint(recipe: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    title_key = _normalize_title(str(recipe.get("title", "")))
    ingredient_key = tuple(sorted(_normalize_ingredient_set(recipe.get("ingredients", []))))
    return title_key, ingredient_key


def _select_diverse_recipes(
    candidates: list[dict[str, Any]],
    user_ingredients: list[str],
    target: int,
) -> list[dict[str, Any]]:
    if len(candidates) <= target:
        return candidates

    remaining = list(candidates)
    remaining.sort(key=lambda item: _coverage_score(item, user_ingredients), reverse=True)

    selected = [remaining.pop(0)]

    while remaining and len(selected) < target:
        best_recipe: dict[str, Any] | None = None
        best_score = -1.0
        for recipe in remaining:
            novelty = min(1.0 - _recipe_similarity(recipe, chosen) for chosen in selected)
            relevance = _coverage_score(recipe, user_ingredients)
            score = 0.65 * novelty + 0.35 * relevance
            if score > best_score:
                best_score = score
                best_recipe = recipe

        if best_recipe is None:
            break

        if best_score < _MIN_NOVELTY_SCORE:
            break

        selected.append(best_recipe)
        remaining.remove(best_recipe)

    # Fill remaining slots by relevance if novelty threshold prevents full target.
    if len(selected) < target and remaining:
        remaining.sort(key=lambda item: _coverage_score(item, user_ingredients), reverse=True)
        selected.extend(remaining[: target - len(selected)])

    return selected[:target]


def _extract_json_object(raw_text: str) -> str:
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise LLMRecipeEngineError("LLM response did not contain a JSON object")
    return raw_text[start : end + 1]


def _validate_ingredient_form_integrity(recipe: dict[str, Any], user_ingredients: list[str]) -> None:
    """Block recipes that reinterpret core ingredients into unrelated base products."""

    user_text = " ".join(user_ingredients).lower()
    recipe_text = " ".join(
        [
            str(recipe.get("title", "")),
            *[str(item) for item in recipe.get("ingredients", [])],
            *[str(step) for step in recipe.get("instructions", [])],
        ]
    ).lower()

    violations: list[str] = []
    for base_ingredient, blocked_terms in _FORM_CHANGE_RULES.items():
        if base_ingredient not in user_text:
            continue
        for term in blocked_terms:
            if term in recipe_text and term not in user_text:
                violations.append(f"{base_ingredient}->{term}")

    if violations:
        joined = ", ".join(sorted(set(violations)))
        raise IngredientFormIntegrityError(f"Recipe changed ingredient form unexpectedly ({joined})")


class LLMRecipeEngine:
    """Encapsulates Groq client lifecycle and recipe JSON generation."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama3-8b-8192",
        timeout_seconds: float = 8.0,
    ) -> None:
        if Groq is None:
            raise LLMRecipeEngineError("groq package is not installed")
        if not api_key.strip():
            raise LLMRecipeEngineError("GROQ_API_KEY is missing")

        self.model = model
        self.timeout_seconds = timeout_seconds
        try:
            self._client = Groq(api_key=api_key)
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            raise LLMRecipeEngineError(f"Failed to initialize Groq client: {exc}") from exc

    @weave.op()
    def generate_recipe(
        self,
        user_ingredients: list[str],
        avoid_recipes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate one recipe in strict JSON format from user ingredients.

        Retries exactly once when JSON parsing/validation fails.
        """

        cleaned = [item.strip() for item in user_ingredients if item and item.strip()]
        if not cleaned:
            raise LLMRecipeEngineError("ingredients list must not be empty")

        prompt = self._build_prompt(cleaned, avoid_recipes=avoid_recipes or [])
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            content = self._generate_raw(prompt)
            try:
                parsed = json.loads(_extract_json_object(content))
                payload = GeneratedRecipePayload.model_validate(parsed)
                recipe = payload.model_dump()
                _validate_ingredient_form_integrity(recipe, cleaned)
                return recipe
            except IngredientFormIntegrityError as exc:
                LOGGER.warning(
                    "Rejected LLM recipe on attempt %d/%d due to ingredient form policy: %s",
                    attempt,
                    max_attempts,
                    exc,
                )
                if attempt >= max_attempts:
                    raise LLMRecipeEngineError("Failed to generate recipe that preserves ingredient form") from exc
            except (json.JSONDecodeError, ValidationError, LLMRecipeEngineError) as exc:
                LOGGER.warning("Invalid LLM JSON payload on attempt %d/%d: %s", attempt, max_attempts, exc)
                if attempt >= max_attempts:
                    raise LLMRecipeEngineError("Failed to parse valid LLM recipe JSON") from exc

        raise LLMRecipeEngineError("Exhausted LLM retry attempts")

    @weave.op()
    def generate_recipes(self, user_ingredients: list[str], count: int = 5) -> list[dict[str, Any]]:
        """Generate approximately ``count`` unique recipes from user ingredients.

        The method tries a few extra attempts to handle occasional duplicate titles.
        """

        target = max(1, count)
        max_attempts = max(target + 3, target * _MAX_ATTEMPTS_MULTIPLIER)
        candidate_pool: list[dict[str, Any]] = []
        seen_fingerprints: set[tuple[str, tuple[str, ...]]] = set()

        # Small shuffle helps reduce repeat outputs for deterministic prompts.
        base_ingredients = list(user_ingredients)

        for _ in range(max_attempts):
            random.shuffle(base_ingredients)
            recipe = self.generate_recipe(base_ingredients, avoid_recipes=candidate_pool)
            fingerprint = _recipe_fingerprint(recipe)
            title_key = fingerprint[0]
            if not title_key or fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)
            candidate_pool.append(recipe)

        if not candidate_pool:
            return []

        return _select_diverse_recipes(candidate_pool, user_ingredients=base_ingredients, target=target)

    @weave.op()
    def _generate_raw(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are a professional chef.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "max_tokens": 900,
        }

        try:
            completion = self._client.chat.completions.create(**kwargs, timeout=self.timeout_seconds)
        except TypeError:
            completion = self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise LLMRecipeEngineError(f"Groq API request failed: {exc}") from exc

        content = completion.choices[0].message.content if completion.choices else ""
        if not content:
            raise LLMRecipeEngineError("Groq returned empty content")
        return content

    @staticmethod
    @weave.op()
    def _build_prompt(user_ingredients: list[str], avoid_recipes: list[dict[str, Any]]) -> str:
        ingredients_text = ", ".join(user_ingredients)
        avoid_text = ""
        if avoid_recipes:
            avoid_lines = []
            for recipe in avoid_recipes[-5:]:
                title = str(recipe.get("title", "")).strip()
                ingredient_preview = ", ".join(recipe.get("ingredients", [])[:6])
                avoid_lines.append(f"- {title}: {ingredient_preview}")
            avoid_text = (
                "\n\nAlready generated recipes. Avoid creating near-duplicates of these:\n"
                + "\n".join(avoid_lines)
            )

        return (
            "User ingredients:\n"
            f"{ingredients_text}\n\n"
            "Your job is to generate SIMPLE, QUICK, and PRACTICAL recipes using the user's available ingredients.\n"
            "The recipe must be meaningfully different in dish style, flavor profile, or cooking method "
            "from other likely options.\n\n"
            "Requirements:\n"
            "- minimize additional ingredients\n"
            "- maximize diversity from previously generated options\n"
            "- do not reinterpret a provided ingredient into a different base product "
            "(e.g., rice into wrappers/dough, pasta into dough) unless that transformed product is explicitly provided\n"
            "- provide ingredient list\n"
            "- provide step-by-step instructions\n"
            "- return JSON\n\n"
            f"{avoid_text}"
            "\n\n"
            "Expected JSON response:\n"
            "{\n"
            '  "type": "generated",\n'
            '  "title": "...",\n'
            '  "ingredients": ["..."],\n'
            '  "instructions": ["..."],\n'
            '  "missing_ingredients": ["..."]\n'
            "}"
        )


@lru_cache(maxsize=1)
def _default_engine() -> LLMRecipeEngine:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise LLMRecipeEngineError("GROQ_API_KEY is missing")
    return LLMRecipeEngine(api_key=api_key)


def generate_recipe(user_ingredients: list[str]) -> dict[str, Any]:
    """Generate a recipe using a cached default Groq engine."""

    return _default_engine().generate_recipe(user_ingredients)


def generate_recipes(user_ingredients: list[str], count: int = 5) -> list[dict[str, Any]]:
    """Generate multiple recipes using a cached default Groq engine."""

    return _default_engine().generate_recipes(user_ingredients, count=count)
