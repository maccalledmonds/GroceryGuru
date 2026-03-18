# PantryPal Core Library

PantryPal in this repository is the core Python recommendation engine used by the FastAPI backend in the parent project. The production runtime is FastAPI plus React (not Streamlit).

## What This Package Provides

- Recipe data models and config utilities
- Deterministic ingredient normalization with canonical mappings
- Database retrieval and scoring logic
- Hybrid recommendation flow that combines database + LLM generation
- RAG index/retrieval helpers for semantic candidate selection
- Nutrition lookup/cache helpers
- Unit and integration tests for core recommendation behavior

## Current Structure

```text
pantrypal/
├── app/
│   ├── config.py
│   ├── models.py
│   └── utils/
│       ├── ai_recommender.py
│       ├── database_engine.py
│       ├── groq_client.py
│       ├── hybrid_engine.py
│       ├── llm_engine.py
│       ├── normalization.py
│       ├── nutrition.py
│       ├── rag_index.py
│       ├── rag_retriever.py
│       ├── ranking.py
│       └── scoring.py
├── data/
│   ├── canonical_ingredients.json
│   ├── nutrition_cache.json
│   ├── recipes.faiss
│   ├── recipes.json
│   └── recipes_rag_metadata.json
├── tests/
├── requirements.txt
└── README.md
```

Archived exploratory notebooks are now stored under `docs/archive/notebooks/` at repository root.

## Setup

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r pantrypal/requirements.txt
pip install -r backend/requirements.txt
```

Optional spaCy model for enhanced tokenization paths:

```bash
python -m spacy download en_core_web_sm
```

## Running Tests

From repository root:

```bash
PYTHONPATH=. pytest -q pantrypal/tests
PYTHONPATH=. pytest -q backend/tests
```

## API Runtime

Start backend from repository root:

```bash
uvicorn backend.main:app --reload
```

Key endpoints:

- `POST /api/recommend`
- `POST /api/recommend/ai`

## Notes

- The recommendation stack relies on local data artifacts under `pantrypal/data/`.
- `canonical_ingredients.json` is the source of truth for deterministic ingredient mapping.
- If LLM generation fails, the hybrid engine returns deterministic database-backed recommendations.
