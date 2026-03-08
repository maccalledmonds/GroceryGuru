"""Data models and data-loading helpers for PantryPal."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .config import RECIPES_PATH


@dataclass(slots=True)
class Nutrition:
    """Nutrition values for a recipe."""

    calories: float
    protein: float
    fat: float
    carbs: float


@dataclass(slots=True)
class Recipe:
    """Recipe domain model."""

    id: int
    title: str
    ingredients: list[str]
    instructions: str
    diet_tags: list[str]
    nutrition: Nutrition
    ingredients_normalized: list[str]


def recipe_from_dict(raw: dict[str, Any]) -> Recipe:
    """Create a `Recipe` from a dictionary."""

    nutrition_raw = raw.get("nutrition", {})
    nutrition = Nutrition(
        calories=float(nutrition_raw.get("calories", 0.0)),
        protein=float(nutrition_raw.get("protein", 0.0)),
        fat=float(nutrition_raw.get("fat", 0.0)),
        carbs=float(nutrition_raw.get("carbs", 0.0)),
    )

    return Recipe(
        id=int(raw["id"]),
        title=str(raw["title"]),
        ingredients=[str(item) for item in raw.get("ingredients", [])],
        instructions=str(raw.get("instructions", "")),
        diet_tags=[str(tag) for tag in raw.get("diet_tags", [])],
        nutrition=nutrition,
        ingredients_normalized=[str(item) for item in raw.get("ingredients_normalized", [])],
    )


def recipe_to_dict(recipe: Recipe) -> dict[str, Any]:
    """Convert `Recipe` to dictionary for rendering."""

    return {
        "id": recipe.id,
        "title": recipe.title,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "diet_tags": recipe.diet_tags,
        "nutrition": {
            "calories": recipe.nutrition.calories,
            "protein": recipe.nutrition.protein,
            "fat": recipe.nutrition.fat,
            "carbs": recipe.nutrition.carbs,
        },
    }


def load_recipes(recipes_path: Path = RECIPES_PATH) -> list[Recipe]:
    """Load recipes from local static JSON file."""

    with recipes_path.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)

    if not isinstance(raw_data, list):
        raise ValueError("recipes.json must contain a top-level list")

    return [recipe_from_dict(item) for item in raw_data]
