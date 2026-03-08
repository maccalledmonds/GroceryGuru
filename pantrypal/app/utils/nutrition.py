"""USDA nutrition integration with local JSON caching."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import time
from typing import Any

import requests

from ..config import NUTRITION_CACHE_PATH, USDA_API_KEY_ENV, USDA_API_URL

LOGGER = logging.getLogger(__name__)


def _ensure_cache_file(cache_path: Path = NUTRITION_CACHE_PATH) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if not cache_path.exists():
        cache_path.write_text("{}", encoding="utf-8")


def _load_cache(cache_path: Path = NUTRITION_CACHE_PATH) -> dict[str, Any]:
    _ensure_cache_file(cache_path)
    with cache_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _save_cache(cache: dict[str, Any], cache_path: Path = NUTRITION_CACHE_PATH) -> None:
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2)


def _extract_macros(food_nutrients: list[dict[str, Any]]) -> dict[str, float]:
    values = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for nutrient in food_nutrients:
        name = str(nutrient.get("nutrientName", "")).lower()
        amount = float(nutrient.get("value", 0.0) or 0.0)
        if "energy" in name and values["calories"] == 0.0:
            values["calories"] = amount
        elif "protein" in name:
            values["protein"] = amount
        elif "total lipid" in name or name == "fat":
            values["fat"] = amount
        elif "carbohydrate" in name:
            values["carbs"] = amount
    return values


def get_nutrition_data(ingredient_name: str) -> dict[str, float]:
    """Fetch nutrition data for an ingredient from cache or USDA API."""

    normalized_name = ingredient_name.strip().lower()
    if not normalized_name:
        return {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    cache = _load_cache()
    if normalized_name in cache:
        return cache[normalized_name]

    api_key = os.getenv(USDA_API_KEY_ENV)
    if not api_key:
        LOGGER.warning("USDA API key is not configured; returning zero nutrition values.")
        return {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    params = {
        "api_key": api_key,
        "query": normalized_name,
        "pageSize": 1,
    }

    try:
        response = requests.get(USDA_API_URL, params=params, timeout=12)
        if response.status_code == 429:
            LOGGER.warning("USDA rate limit reached; sleeping briefly and retrying once.")
            time.sleep(1.0)
            response = requests.get(USDA_API_URL, params=params, timeout=12)
        response.raise_for_status()

        payload = response.json()
        foods = payload.get("foods", [])
        if not foods:
            LOGGER.info("No USDA nutrition record found for ingredient: %s", normalized_name)
            result = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        else:
            nutrients = foods[0].get("foodNutrients", [])
            result = _extract_macros(nutrients)

        cache[normalized_name] = result
        _save_cache(cache)
        time.sleep(0.2)
        return result
    except requests.RequestException as exc:
        LOGGER.exception("USDA request failed for %s: %s", normalized_name, exc)
        return {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}


def aggregate_nutrition_totals(ingredients: list[str]) -> dict[str, float]:
    """Aggregate per-ingredient nutrition into totals."""

    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for ingredient in ingredients:
        nutrition = get_nutrition_data(ingredient)
        for key in totals:
            totals[key] += float(nutrition.get(key, 0.0))
    return {key: round(value, 2) for key, value in totals.items()}
