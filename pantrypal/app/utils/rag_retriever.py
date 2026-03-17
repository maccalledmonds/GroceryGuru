"""Semantic retriever wrapper for recipe candidates."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time

from ..models import Recipe
from .rag_index import RecipeRAGIndex

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievedRecipe:
    recipe_id: int
    similarity: float


class SemanticRecipeRetriever:
    """Retrieves recipe candidates from the RAG index."""

    def __init__(self, rag_index: RecipeRAGIndex, recipes: list[Recipe]) -> None:
        self.rag_index = rag_index
        self._recipes_by_id = {recipe.id: recipe for recipe in recipes}

    def retrieve(self, query: str, top_n: int, filters: list[str] | None = None) -> list[RetrievedRecipe]:
        start = time.perf_counter()
        hits = self.rag_index.search(query=query, top_n=top_n)

        selected: list[RetrievedRecipe] = []
        for hit in hits:
            recipe = self._recipes_by_id.get(hit.recipe_id)
            if recipe is None:
                continue
            if filters and not set(filters).issubset(set(recipe.diet_tags)):
                continue
            selected.append(RetrievedRecipe(recipe_id=hit.recipe_id, similarity=hit.similarity))

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        LOGGER.info("RAG retrieval returned %d candidates in %dms", len(selected), elapsed_ms)
        return selected
