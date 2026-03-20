"""FastAPI backend for PantryPal recipe recommendations."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import sys
import time
from pathlib import Path

# Make the monorepo root importable so `pantrypal` is on the path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import weave

from pantrypal.app.config import DEFAULT_TOP_K, SUPPORTED_FILTERS
from pantrypal.app.config import (
    GROQ_TIMEOUT_SECONDS,
    get_groq_api_key,
    validate_ai_runtime_config,
)
from pantrypal.app.utils.database_engine import warm_recipe_cache
from pantrypal.app.utils.hybrid_engine import HybridRecommendationEngine
from pantrypal.app.utils.llm_engine import LLMRecipeEngine, LLMRecipeEngineError

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

# Load local backend/.env for development; existing shell env vars win.
load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env", override=False)
weave.init("GroceryGuru")

def _initialize_hybrid_services(app: FastAPI) -> None:
    """Initialize and cache hybrid recommendation dependencies."""

    config_errors = validate_ai_runtime_config()
    if config_errors:
        raise RuntimeError(f"Invalid AI runtime configuration: {config_errors}")

    app.state.hybrid_recommender = None
    app.state.ai_config_error = None

    try:
        warm_recipe_cache()

        api_key = get_groq_api_key()
        llm_engine = None
        if not api_key:
            app.state.ai_config_error = "Missing GROQ_API_KEY. Hybrid endpoint will return database-only results."
            LOGGER.warning(app.state.ai_config_error)
        else:
            llm_engine = LLMRecipeEngine(
                api_key=api_key,
                model="llama-3.1-8b-instant",
                timeout_seconds=GROQ_TIMEOUT_SECONDS,
            )

        app.state.hybrid_recommender = HybridRecommendationEngine(llm_engine=llm_engine)
        LOGGER.info("Hybrid services initialized successfully")
    except (LLMRecipeEngineError, RuntimeError) as exc:
        app.state.ai_config_error = str(exc)
        app.state.hybrid_recommender = HybridRecommendationEngine(llm_engine=None)
        LOGGER.exception("Hybrid services initialization failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _initialize_hybrid_services(app)
    yield


app = FastAPI(
    title="PantryPal API",
    version="1.0.0",
    description="Recipe recommendation API backed by ingredient matching and USDA nutrition data.",
    lifespan=lifespan,
)

# Allow any Vercel deployment preview URL plus localhost dev origins.
# In production set ALLOWED_ORIGINS env var (comma-separated).
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


class RecipeResult(BaseModel):
    id: int | None = None
    type: str
    title: str
    ingredients: list[str]
    missing_ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] | str | None = None
    score: float
    match_score: float | None = None


class RecommendResponse(BaseModel):
    on_hand_recipes: list[RecipeResult]
    related_recipes: list[RecipeResult]
    normalized_ingredients: list[str]
    used_fallback: bool
    fallback_reason: str | None = None


class FiltersResponse(BaseModel):
    filters: list[str]


LOGGER = logging.getLogger(__name__)


def _validate_and_normalize_request(body: RecommendRequest) -> tuple[list[str], list[str]]:
    normalized_filters: list[str] = []
    seen_filters: set[str] = set()
    for value in body.filters:
        candidate = value.strip().lower()
        if not candidate or candidate in seen_filters:
            continue
        seen_filters.add(candidate)
        normalized_filters.append(candidate)

    invalid = set(normalized_filters) - SUPPORTED_FILTERS
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown filter(s): {sorted(invalid)}. Valid filters: {sorted(SUPPORTED_FILTERS)}",
        )

    raw = [i.strip() for i in body.ingredients if i.strip()]
    if not raw:
        raise HTTPException(status_code=400, detail="ingredients list must not be empty after stripping whitespace")

    return raw, normalized_filters


def _to_recipe_response_item(raw_recipe: dict[str, Any]) -> RecipeResult:
    return RecipeResult(
        id=raw_recipe.get("id"),
        type=raw_recipe["type"],
        title=raw_recipe["title"],
        ingredients=raw_recipe.get("ingredients", []),
        missing_ingredients=raw_recipe.get("missing_ingredients", []),
        instructions=raw_recipe.get("instructions"),
        score=raw_recipe["score"],
        match_score=raw_recipe.get("match_score"),
    )


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

@weave.op()
@app.post("/api/recommend", response_model=RecommendResponse, tags=["recommend"])
def recommend(body: RecommendRequest) -> RecommendResponse:
    """
    Accept a list of raw ingredient strings (and optional dietary filters),
    normalize them, score recipes, and return the top-K matches.
    """
    raw_ingredients, normalized_filters = _validate_and_normalize_request(body)

    hybrid_recommender: HybridRecommendationEngine | None = getattr(
        app.state,
        "hybrid_recommender",
        None,
    )
    if hybrid_recommender is None:
        raise HTTPException(status_code=503, detail="Hybrid recommender is not initialized")

    start = time.perf_counter()
    result = hybrid_recommender.recommend_recipes(
        user_ingredients=raw_ingredients,
        top_k=body.top_k,
        filters=normalized_filters,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    LOGGER.info(
        "Hybrid endpoint completed (fallback=%s, reason=%s, latency_ms=%d)",
        result.used_fallback,
        result.fallback_reason,
        elapsed_ms,
    )

    return RecommendResponse(
        on_hand_recipes=[_to_recipe_response_item(item) for item in result.on_hand_recipes],
        related_recipes=[_to_recipe_response_item(item) for item in result.related_recipes],
        normalized_ingredients=result.normalized_ingredients,
        used_fallback=result.used_fallback,
        fallback_reason=result.fallback_reason,
    )


@app.post("/api/recommend/ai", response_model=RecommendResponse, tags=["recommend"])
def recommend_ai(body: RecommendRequest) -> RecommendResponse:
    """Alias endpoint for hybrid recommendations with database + LLM merge."""

    return recommend(body)
