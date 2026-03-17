"""FAISS-backed recipe index for semantic retrieval."""
# pyright: reportMissingImports=false

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any

import numpy as np

try:  # pragma: no cover - exercised in integration environments
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None

try:  # pragma: no cover - exercised in integration environments
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    SentenceTransformer = None

from ..models import Recipe

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RAGDocument:
    recipe_id: int
    title: str
    text: str


@dataclass(slots=True)
class RetrievalHit:
    recipe_id: int
    title: str
    text: str
    similarity: float


class RAGDependencyError(RuntimeError):
    """Raised when FAISS or sentence-transformers is unavailable."""


class RecipeRAGIndex:
    """Build and query a local recipe embedding index with FAISS."""

    def __init__(self, model_name: str, index_path: Path, metadata_path: Path) -> None:
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path

        self._encoder: Any | None = None
        self._index: Any | None = None
        self._documents: list[RAGDocument] = []
        self._dataset_signature: str = ""

    def load_or_build(self, recipes: list[Recipe]) -> None:
        """Load cached index if compatible; otherwise build and persist."""

        if self._can_load_cached(recipes):
            self._load_cached()
            LOGGER.info("Loaded cached RAG index with %d documents", len(self._documents))
            return

        self._build(recipes)
        self._persist()
        LOGGER.info("Built and cached RAG index with %d documents", len(self._documents))

    def search(self, query: str, top_n: int) -> list[RetrievalHit]:
        """Search semantically similar recipe documents."""

        if not query.strip() or top_n <= 0:
            return []
        if self._index is None:
            raise RuntimeError("RAG index is not initialized")

        query_vec = self._embed([query])
        distances, indices = self._index.search(query_vec, min(top_n, len(self._documents)))

        hits: list[RetrievalHit] = []
        if len(indices) == 0:
            return hits

        for idx, score in zip(indices[0], distances[0], strict=False):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            hits.append(
                RetrievalHit(
                    recipe_id=doc.recipe_id,
                    title=doc.title,
                    text=doc.text,
                    similarity=float(score),
                )
            )
        return hits

    def _build(self, recipes: list[Recipe]) -> None:
        self._validate_dependencies()

        build_start = time.perf_counter()
        self._documents = [self._build_document(recipe) for recipe in recipes]
        self._dataset_signature = self._dataset_signature_from_recipes(recipes)
        text_batch = [doc.text for doc in self._documents]

        vectors = self._embed(text_batch)
        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)
        self._index = index

        elapsed_ms = int((time.perf_counter() - build_start) * 1000)
        LOGGER.info("RAG index build complete in %dms", elapsed_ms)

    def _persist(self) -> None:
        if self._index is None:
            raise RuntimeError("Cannot persist index before building it")

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))

        metadata = {
            "model_name": self.model_name,
            "dataset_signature": self._dataset_signature,
            "documents": [
                {"recipe_id": doc.recipe_id, "title": doc.title, "text": doc.text}
                for doc in self._documents
            ],
        }
        self.metadata_path.write_text(json.dumps(metadata, ensure_ascii=True), encoding="utf-8")

    def _load_cached(self) -> None:
        self._validate_dependencies()

        self._index = faiss.read_index(str(self.index_path))
        raw_metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self._documents = [
            RAGDocument(
                recipe_id=int(item["recipe_id"]),
                title=str(item["title"]),
                text=str(item["text"]),
            )
            for item in raw_metadata.get("documents", [])
        ]
        self._dataset_signature = str(raw_metadata.get("dataset_signature", ""))

    def _can_load_cached(self, recipes: list[Recipe]) -> bool:
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False

        try:
            raw_metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False

        if raw_metadata.get("model_name") != self.model_name:
            return False

        cached_signature = str(raw_metadata.get("dataset_signature", ""))
        return cached_signature == self._dataset_signature_from_recipes(recipes)

    def _build_document(self, recipe: Recipe) -> RAGDocument:
        instructions = recipe.instructions.strip()
        instructions_snippet = instructions[:360] + ("..." if len(instructions) > 360 else "")

        ingredient_values = recipe.ingredients_normalized or recipe.ingredients
        text = "\n".join(
            [
                f"title: {recipe.title}",
                f"diet_tags: {', '.join(recipe.diet_tags) if recipe.diet_tags else 'none'}",
                f"ingredients: {', '.join(ingredient_values)}",
                f"instructions: {instructions_snippet}",
                (
                    "nutrition: "
                    f"calories={recipe.nutrition.calories}, "
                    f"protein={recipe.nutrition.protein}, "
                    f"fat={recipe.nutrition.fat}, "
                    f"carbs={recipe.nutrition.carbs}"
                ),
            ]
        )
        return RAGDocument(recipe_id=recipe.id, title=recipe.title, text=text)

    def _embed(self, texts: list[str]) -> np.ndarray:
        encoder = self._get_encoder()
        vectors = encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        faiss.normalize_L2(matrix)
        return matrix

    def _get_encoder(self) -> Any:
        self._validate_dependencies()
        if self._encoder is None:
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    def _validate_dependencies(self) -> None:
        if faiss is None:
            raise RAGDependencyError("faiss is not installed; install faiss-cpu to enable RAG retrieval")
        if SentenceTransformer is None:
            raise RAGDependencyError(
                "sentence-transformers is not installed; install sentence-transformers to enable RAG retrieval"
            )

    @staticmethod
    def _dataset_signature_from_recipes(recipes: list[Recipe]) -> str:
        payload = "|".join(
            f"{recipe.id}:{recipe.title}:{len(recipe.ingredients)}:{len(recipe.instructions)}"
            for recipe in sorted(recipes, key=lambda item: item.id)
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

