"""FastAPI backend for PantryPal recipe recommendations."""

from __future__ import annotations

import sys
from pathlib import Path

# Make the monorepo root importable so `pantrypal` is on the path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pantrypal.app.config import DEFAULT_TOP_K, SUPPORTED_FILTERS
from pantrypal.app.models import load_recipes
from pantrypal.app.utils.normalization import normalize_ingredients
from pantrypal.app.utils.scoring import recommend_recipes

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PantryPal API",
    version="1.0.0",
    description="Recipe recommendation API backed by ingredient matching and USDA nutrition data.",
)

# Allow any Vercel deployment preview URL plus localhost dev origins.
# In production set ALLOWED_ORIGINS env var (comma-separated).
import os

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
)
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class RecommendRequest(BaseModel):
    ingredients: list[str] = Field(..., min_length=1, description="Raw ingredient names")
    filters: list[str] = Field(default_factory=list, description="Dietary filter keys")
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20, description="Number of results")


class NutritionOut(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float


class RecipeResult(BaseModel):
    id: int
    title: str
    score: float
    match_percentage: float
    exact_match_count: int
    coverage: float
    ingredient_match_ratio: float
    ingredients: list[str]
    instructions: str
    diet_tags: list[str]
    nutrition: NutritionOut


class RecommendResponse(BaseModel):
    recipes: list[RecipeResult]
    normalized_ingredients: list[str]


class FiltersResponse(BaseModel):
    filters: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness probe for Render health checks."""
    return {"status": "ok"}


@app.get("/api/filters", response_model=FiltersResponse, tags=["meta"])
def get_filters() -> FiltersResponse:
    """Return the list of supported dietary filter keys."""
    return FiltersResponse(filters=sorted(SUPPORTED_FILTERS))


@app.post("/api/recommend", response_model=RecommendResponse, tags=["recommend"])
def recommend(body: RecommendRequest) -> RecommendResponse:
    """
    Accept a list of raw ingredient strings (and optional dietary filters),
    normalize them, score recipes, and return the top-K matches.
    """
    # Validate filters early so the client gets a clear 400 error.
    invalid = set(body.filters) - SUPPORTED_FILTERS
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown filter(s): {sorted(invalid)}. Valid filters: {sorted(SUPPORTED_FILTERS)}",
        )

    # Strip blank / whitespace-only entries.
    raw = [i.strip() for i in body.ingredients if i.strip()]
    if not raw:
        raise HTTPException(status_code=400, detail="ingredients list must not be empty after stripping whitespace")

    normalized = normalize_ingredients(raw)
    if not normalized:
        raise HTTPException(
            status_code=422,
            detail="None of the provided ingredients could be recognized. Try different names.",
        )

    recipes = load_recipes()
    results: list[dict[str, Any]] = recommend_recipes(
        user_ingredients=normalized,
        recipes=recipes,
        top_k=body.top_k,
        filters=body.filters or None,
    )

    recipe_results = [
        RecipeResult(
            id=r["id"],
            title=r["title"],
            score=r["score"],
            match_percentage=r["match_percentage"],
            exact_match_count=r["exact_match_count"],
            coverage=r["coverage"],
            ingredient_match_ratio=r["ingredient_match_ratio"],
            ingredients=r["ingredients"],
            instructions=r["instructions"],
            diet_tags=r["diet_tags"],
            nutrition=NutritionOut(**r["nutrition"]),
        )
        for r in results
    ]

    return RecommendResponse(recipes=recipe_results, normalized_ingredients=normalized)
