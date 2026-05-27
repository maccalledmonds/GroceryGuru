"""Scraper configuration constants."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"
HTTP_CACHE_DIR = DATA_DIR / "http_cache"

RECIPES_OUTPUT_PATH = DATA_DIR / "recipes.jsonl"
URLS_OUTPUT_PATH = DATA_DIR / "urls.txt"
UNMATCHED_REPORT_PATH = DATA_DIR / "unmatched_candidates.csv"

# Path to pantrypal's canonical ingredient dataset. The scraper reuses this
# file as the source of truth so curation feeds straight back into runtime.
CANONICAL_INGREDIENTS_PATH = PROJECT_ROOT / "pantrypal" / "data" / "canonical_ingredients.json"

EPICURIOUS_SITEMAP_INDEX = "https://www.epicurious.com/sitemap.xml"
EPICURIOUS_BASE = "https://www.epicurious.com"

USER_AGENT = (
    "GroceryGuruScraper/0.1 (+research; contact via repo issues; "
    "respects robots.txt and rate limits)"
)

# Fetcher tuning. Defaults are intentionally polite.
MAX_CONCURRENCY = 4
REQUEST_TIMEOUT_SECONDS = 30.0
MIN_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 2.5
MAX_RETRIES = 3

# Title/category tokens that signal a non-meal recipe. Mirrors and extends
# pantrypal.app.utils.database_engine._NON_MEAL_TITLE_HINTS.
NON_MEAL_TOKENS: frozenset[str] = frozenset(
    {
        # Sauces and dressings
        "sauce",
        "sauces",
        "dressing",
        "dressings",
        "dip",
        "dips",
        "marinade",
        "marinades",
        "condiment",
        "condiments",
        "vinaigrette",
        "vinaigrettes",
        "aioli",
        # Beverages
        "drink",
        "drinks",
        "smoothie",
        "smoothies",
        "juice",
        "juices",
        "cocktail",
        "cocktails",
        "tea",
        "coffee",
        "lemonade",
        "punch",
        # Spice and seasoning blends
        "rub",
        "rubs",
        "blend",
        "blends",
        "seasoning",
        "seasonings",
        "spice",  # only as standalone title token
        # Stocks and broths (when sole subject of the recipe)
        "stock",
        "broth",
        # Preserved and pickled components
        "pickle",
        "pickled",
        "preserved",
        "relish",
        "chutney",
        "jam",
        "marmalade",
        # Spreads and pastes
        "spread",
        "pesto",
        "tapenade",
        "hummus",  # debatable; user can revise
        # Sweet components and toppings (component, not full dessert)
        "syrup",
        "syrups",
        "glaze",
        "frosting",
        "icing",
        "ganache",
        "compote",
        "jelly",
        "curd",
        # Doughs and bases
        "dough",
        "roux",
        # Single-ingredient component recipes
        "butter",  # e.g. "Compound Butter"
        "oil",     # e.g. "Chili Oil"
        "salt",    # e.g. "Spiced Salt"
    }
)

# A small set of category strings (recipeCategory in JSON-LD) that should
# always be considered meals/snacks regardless of title quirks.
MEAL_CATEGORY_HINTS: frozenset[str] = frozenset(
    {
        "main course",
        "main dish",
        "main",
        "side dish",
        "side",
        "breakfast",
        "brunch",
        "lunch",
        "dinner",
        "snack",
        "snacks",
        "appetizer",
        "appetizers",
        "salad",
        "salads",
        "soup",
        "soups",
        "stew",
        "stews",
        "sandwich",
        "sandwiches",
        "pasta",
        "pizza",
        "bowl",
        "bowls",
        "casserole",
        "casseroles",
        "dessert",
        "desserts",
    }
)
