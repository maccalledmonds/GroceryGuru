# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend / Pantrypal

```bash
# Run all tests (from repo root)
PYTHONPATH=. pytest -q pantrypal/tests
PYTHONPATH=. pytest -q backend/tests

# Run a single test file
PYTHONPATH=. pytest -q pantrypal/tests/test_normalization.py

# Run a single test
PYTHONPATH=. pytest -q pantrypal/tests/test_normalization.py::test_function_name

# Start the API server (dev)
uvicorn backend.main:app --reload

# Download spaCy model (required once)
python -m spacy download en_core_web_sm
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Start dev server
npm run build      # Production build
npm run lint       # ESLint
npm run typecheck  # TypeScript check
```

## No-Regression Rules

These are enforced by a pre-commit hook and must be followed:

- Treat backward compatibility as a hard requirement unless the user explicitly asks for a breaking change.
- When changing logic, add or update tests in the same change.
- **Before finalizing any code changes**, run both test suites from repo root:
  - `PYTHONPATH=. pytest -q pantrypal/tests`
  - `PYTHONPATH=. pytest -q backend/tests`
- Test failures are a hard stop — do not mark tasks complete until failures are fixed or user explicitly approves.
- If unexpected unrelated file changes appear, stop and ask the user how to proceed.

## Architecture

GroceryGuru is a monorepo with three main layers:

```
backend/        FastAPI app (entry point: backend/main.py)
pantrypal/      Core recommendation library
frontend/       React + TypeScript + Vite + Tailwind
```

### Recommendation Flow

1. **Normalization** (`pantrypal/app/utils/normalization.py`) — Deterministic 7-step rule-based pipeline converts raw ingredient strings to canonical form. **This must never use AI/semantic methods.**
2. **Hybrid Engine** (`pantrypal/app/utils/hybrid_engine.py`) — Orchestrates parallel execution of database search and LLM generation via `ThreadPoolExecutor`.
3. **Database Engine** (`pantrypal/app/utils/database_engine.py`) — Matches canonical ingredients against `pantrypal/data/recipes.json` (36 MB).
4. **LLM Engine** (`pantrypal/app/utils/llm_engine.py`) — Calls Groq API to generate new recipes. Falls back gracefully if no API key or on timeout.
5. **Scoring / Ranking** (`scoring.py`, `ranking.py`) — Scores by weighted ingredient match ratio; partitions into `on_hand_recipes` (exact matches) and `related_recipes`.
6. **RAG** (`rag_index.py`, `rag_retriever.py`) — FAISS + sentence-transformers for semantic recipe retrieval. Used for recipe retrieval **only**, never ingredient normalization.

### Normalization Pipeline (Critical Constraint)

The 7-step pipeline must remain deterministic and rule-based:
1. Trim + lowercase
2. Punctuation removal
3. Descriptor removal (fresh, chopped, diced, organic, etc.)
4. Whitespace normalization
5. Singularization (tomatoes → tomato)
6. Alias matching (against `pantrypal/data/canonical_ingredients.json`)
7. Canonical mapping

Multi-word ingredients like "soy sauce" and "olive oil" must be preserved intact. No hallucination or dynamic synonym generation.

### Key Config (`pantrypal/app/config.py`)

| Constant | Value |
|---|---|
| `DEFAULT_TOP_K` | 5 |
| `FUZZY_THRESHOLD` | 80 |
| `HIGH_IMPORTANCE_WEIGHT` | 2.0 (proteins, grains) |
| `LOW_IMPORTANCE_WEIGHT` | 0.35 (spices, seasonings) |
| `GROQ_TIMEOUT_SECONDS` | 8.0 |
| `RAG_TOP_N` | 12 |
| `ON_HAND_LLM_TARGET` | 10 (target exact-match recipes) |

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/recommend` | Main recommendation endpoint |
| `POST` | `/api/recommend/ai` | Alias — uses hybrid engine |
| `GET` | `/api/filters` | Available dietary filters |
| `GET` | `/health` | Health check |

### Environment Variables

Required for full functionality:
- `GROQ_API_KEY` — enables LLM recipe generation
- `USDA_API_KEY` — nutrition data
- `ALLOWED_ORIGINS` — CORS (Vercel URL in prod)

### Data Files

- `pantrypal/data/recipes.json` — 36 MB recipe database
- `pantrypal/data/canonical_ingredients.json` — source of truth for normalization
- `pantrypal/data/recipes.faiss` — FAISS vector index (27 MB)
- `pantrypal/data/recipes_rag_metadata.json` — RAG metadata (13 MB)

### Deployment

Deployed to Render (Python 3.11, free tier). Config in `render.yaml`. Frontend deployed separately to Vercel.
