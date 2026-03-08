"""Application configuration for PantryPal."""

from __future__ import annotations

import logging
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RECIPES_PATH = DATA_DIR / "recipes.json"
INGREDIENT_VOCAB_PATH = DATA_DIR / "ingredients_vocab.json"
NUTRITION_CACHE_PATH = DATA_DIR / "nutrition_cache.json"

USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_API_KEY_ENV = "USDA_API_KEY"
FUZZY_THRESHOLD = 80

DEFAULT_TOP_K = 5
SUPPORTED_FILTERS = {"vegetarian", "vegan", "gluten_free", "high_protein"}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
