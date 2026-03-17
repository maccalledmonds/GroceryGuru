"""Application configuration for PantryPal."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Final

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

# Assumed pantry staples that should always be treated as available.
DEFAULT_PANTRY_INGREDIENTS: tuple[str, ...] = ("salt", "black pepper", "water")

# Ingredient weighting configuration for recommendation scoring.
HIGH_IMPORTANCE_INGREDIENT_KEYWORDS: tuple[str, ...] = (
    # Protein-forward terms
    "chicken",
    "turkey",
    "beef",
    "pork",
    "salmon",
    "shrimp",
    "tuna",
    "cod",
    "tilapia",
    "egg",
    "tofu",
    "lentil",
    "chickpea",
    "bean",
    "yogurt",
    "cheese",
    # Carb/starch foundations
    "rice",
    "quinoa",
    "pasta",
    "spaghetti",
    "noodle",
    "bread",
    "potato",
    "oat",
    "barley",
    "couscous",
    "farro",
)

LOW_IMPORTANCE_INGREDIENT_KEYWORDS: tuple[str, ...] = (
    "salt",
    "pepper",
    "water",
    "garlic",
    "ginger",
    "turmeric",
    "basil",
    "parsley",
    "cilantro",
    "cinnamon",
    "nutmeg",
    "cumin",
    "paprika",
    "oregano",
    "thyme",
    "rosemary",
    "dill",
    "bay leaf",
)

HIGH_IMPORTANCE_WEIGHT = 2.0
NORMAL_IMPORTANCE_WEIGHT = 1.0
LOW_IMPORTANCE_WEIGHT = 0.35

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# AI / RAG configuration
GROQ_API_KEY_ENV: Final[str] = "GROQ_API_KEY"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
RAG_TOP_N = int(os.getenv("RAG_TOP_N", "12"))
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_INDEX_PATH = DATA_DIR / "recipes.faiss"
RAG_METADATA_PATH = DATA_DIR / "recipes_rag_metadata.json"
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "8.0"))


def get_groq_api_key() -> str | None:
    """Return GROQ API key if configured, otherwise None."""

    value = os.getenv(GROQ_API_KEY_ENV)
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_ai_runtime_config() -> list[str]:
    """Return startup validation errors for AI runtime configuration."""

    errors: list[str] = []
    if RAG_TOP_N < 1:
        errors.append("RAG_TOP_N must be >= 1")
    if GROQ_TIMEOUT_SECONDS <= 0:
        errors.append("GROQ_TIMEOUT_SECONDS must be > 0")
    return errors

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
