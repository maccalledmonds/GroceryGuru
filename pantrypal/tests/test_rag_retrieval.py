"""Tests for semantic retrieval candidate selection."""

from __future__ import annotations

from pantrypal.app.models import load_recipes
from pantrypal.app.utils.rag_retriever import SemanticRecipeRetriever


class _HeuristicRagIndex:
    """Test double that mimics semantic similarity with token overlap."""

    def __init__(self, recipes):
        self._docs = []
        for recipe in recipes:
            text = " ".join([recipe.title] + (recipe.ingredients_normalized or recipe.ingredients)).lower()
            self._docs.append((recipe.id, text))

    def search(self, query: str, top_n: int):
        query_tokens = {token.strip().lower() for token in query.split() if token.strip()}
        scored = []
        for recipe_id, text in self._docs:
            score = sum(1 for token in query_tokens if token in text)
            if score > 0:
                scored.append((recipe_id, float(score)))
        scored.sort(key=lambda item: item[1], reverse=True)

        hits = []
        for recipe_id, similarity in scored[:top_n]:
            hits.append(type("Hit", (), {"recipe_id": recipe_id, "similarity": similarity})())
        return hits


def test_retrieval_returns_relevant_candidates() -> None:
    recipes = load_recipes()
    retriever = SemanticRecipeRetriever(rag_index=_HeuristicRagIndex(recipes), recipes=recipes)

    results = retriever.retrieve(query="spinach feta egg", top_n=5)

    assert results
    top_ids = [item.recipe_id for item in results[:3]]
    top_titles = {recipe.title.lower() for recipe in recipes if recipe.id in top_ids}
    assert any("spinach" in title or "omelette" in title for title in top_titles)
