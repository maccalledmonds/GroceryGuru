"""Parse Epicurious recipe pages via schema.org/Recipe JSON-LD."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from bs4 import BeautifulSoup

from .config import NON_MEAL_TOKENS, MEAL_CATEGORY_HINTS

LOGGER = logging.getLogger(__name__)

# Servings extraction from recipeYield strings like "Makes 4 servings",
# "Serves 6 to 8", "4 servings", "Yields 2 to 3".
SERVINGS_PATTERN = re.compile(r"(\d+)\s*(?:to\s*\d+\s*)?(?:servings|people|portions)?", re.IGNORECASE)


@dataclass(slots=True)
class ParsedRecipe:
    """Output of the JSON-LD parser before ingredient extraction."""

    source_url: str
    title: str
    ingredients_raw: list[str]
    instructions: str
    servings: int | None
    recipe_category: list[str] = field(default_factory=list)
    nutrition: dict[str, float] = field(default_factory=dict)
    rejection_reason: str | None = None

    @property
    def is_meal_candidate(self) -> bool:
        return self.rejection_reason is None


def _iter_recipe_json_blocks(soup: BeautifulSoup) -> Iterable[dict[str, Any]]:
    """Yield every JSON-LD object on the page whose @type is Recipe."""

    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            LOGGER.debug("Skipping non-JSON ld+json block")
            continue

        yield from _walk_for_recipes(data)


def _walk_for_recipes(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        node_type = node.get("@type")
        if _matches_recipe_type(node_type):
            yield node
        graph = node.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _walk_for_recipes(item)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_for_recipes(item)


def _matches_recipe_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "recipe"
    if isinstance(value, list):
        return any(isinstance(item, str) and item.lower() == "recipe" for item in value)
    return False


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, str):
                items.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("name")
                if isinstance(text, str):
                    items.append(text)
        return items
    return []


def _parse_servings(value: Any) -> int | None:
    candidates: list[str] = []
    if isinstance(value, str):
        candidates.append(value)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                candidates.append(item)
    elif isinstance(value, (int, float)):
        return int(value) if value else None
    for candidate in candidates:
        match = SERVINGS_PATTERN.search(candidate)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                continue
    return None


def _parse_nutrition(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    key_map = {
        "calories": "calories",
        "proteinContent": "protein",
        "fatContent": "fat",
        "carbohydrateContent": "carbs",
    }
    for ld_key, our_key in key_map.items():
        value = raw.get(ld_key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            out[our_key] = float(value)
            continue
        if isinstance(value, str):
            match = re.search(r"[-+]?\d*\.?\d+", value)
            if match:
                try:
                    out[our_key] = float(match.group(0))
                except ValueError:
                    continue
    return out


def _normalize_categories(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().lower()]
    if isinstance(value, list):
        return [item.strip().lower() for item in value if isinstance(item, str)]
    return []


def _title_rejects_meal(title: str, categories: list[str]) -> Optional[str]:
    title_tokens = {tok for tok in re.findall(r"[a-z]+", title.lower()) if tok}
    title_bad = title_tokens.intersection(NON_MEAL_TOKENS)
    if title_bad:
        # If the page also tags itself with an explicit meal category, allow it.
        if any(cat in MEAL_CATEGORY_HINTS for cat in categories):
            return None
        return f"title contains non-meal tokens: {sorted(title_bad)}"
    return None


def parse_recipe_html(html: str, source_url: str) -> ParsedRecipe | None:
    """Parse an Epicurious recipe page. Returns ``None`` if no Recipe block found."""

    soup = BeautifulSoup(html, "html.parser")
    for recipe in _iter_recipe_json_blocks(soup):
        title = (recipe.get("name") or "").strip()
        if not title:
            continue
        ingredients = _coerce_str_list(recipe.get("recipeIngredient"))
        instructions_items = _coerce_str_list(recipe.get("recipeInstructions"))
        instructions = " ".join(item.strip() for item in instructions_items if item.strip())
        servings = _parse_servings(recipe.get("recipeYield"))
        categories = _normalize_categories(recipe.get("recipeCategory"))
        nutrition = _parse_nutrition(recipe.get("nutrition"))

        parsed = ParsedRecipe(
            source_url=source_url,
            title=title,
            ingredients_raw=ingredients,
            instructions=instructions,
            servings=servings,
            recipe_category=categories,
            nutrition=nutrition,
        )
        parsed.rejection_reason = _title_rejects_meal(title, categories)
        return parsed
    LOGGER.debug("No Recipe JSON-LD found at %s", source_url)
    return None
