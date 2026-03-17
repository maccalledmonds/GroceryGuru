# PantryPal (GroceryGuru MVP)

PantryPal is a Streamlit recipe recommendation app that suggests recipes from ingredients users already have.

## Features

- Text ingredient input (`eggs, spinach, feta cheese`)
- Optional pantry image upload (modular, non-blocking if disabled)
- Ingredient normalization pipeline:
  - lowercase
  - punctuation removal
  - quantity/unit stripping
  - spaCy lemmatization
  - RapidFuzz matching (threshold 80)
- Recipe ranking with exact and partial match scoring
- Dietary filters (`vegetarian`, `vegan`, `gluten_free`, `high_protein`)
- Nutrition integration utility with USDA FoodData Central API + local cache
- Unit tests for normalization and scoring
- AI-enhanced recommendation endpoint with:
  - semantic retrieval over local recipe corpus (FAISS + sentence-transformers)
  - Groq-hosted Llama ranking with grounded explanations
  - deterministic fallback to existing scorer when AI fails or times out

## Project Structure

```text
pantrypal/
├── notebooks/
│   ├── data_exploration.ipynb
│   ├── ingredient_normalization.ipynb
│   ├── matching_engine.ipynb
├── app/
│   ├── main.py
│   ├── models.py
│   ├── config.py
│   └── utils/
│       ├── normalization.py
│       ├── scoring.py
│       ├── nutrition.py
│       ├── image_classifier.py
├── data/
│   ├── recipes.json
│   ├── ingredients_vocab.json
│   └── nutrition_cache.json
├── tests/
│   ├── test_normalization.py
│   ├── test_scoring.py
├── requirements.txt
├── README.md
└── .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Optional (for FastAPI AI endpoint usage)
pip install -r ../backend/requirements.txt
```

Copy env values:

```bash
cp .env.example .env
```

## Run App

```bash
streamlit run app/main.py
```

## Run Tests

```bash
pytest
```

## AI Recommendation Setup (FastAPI)

The AI pipeline is exposed through a separate endpoint to preserve compatibility:

- `POST /api/recommend` -> deterministic scorer (legacy behavior)
- `POST /api/recommend/ai` -> semantic retrieval + Groq Llama reasoning

Set the required environment variables before running the FastAPI backend:

```bash
export GROQ_API_KEY="your-groq-api-key"
export GROQ_MODEL="llama-3.1-8b-instant"
export RAG_TOP_N="12"
export RAG_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

Optional timeout tuning:

```bash
export GROQ_TIMEOUT_SECONDS="8.0"
```

Start backend:

```bash
uvicorn backend.main:app --reload
```

## How RAG Works Here

1. At FastAPI startup, recipes are loaded from `data/recipes.json`.
2. Each recipe is converted into retrieval text containing title, ingredients, tags, instructions snippet, and nutrition summary.
3. Embeddings are built with `RAG_EMBEDDING_MODEL` and stored in a FAISS index.
4. Index + metadata are cached on disk so startup can reuse them instead of rebuilding every request.
5. `/api/recommend/ai` normalizes user ingredients, retrieves top-N semantic candidates, and asks Llama to rank only those candidates.
6. Model output is validated as strict JSON and mapped back into the existing recipe schema with an optional `explanation` field.

## Fallback Behavior

- If Groq is unavailable, times out, or returns invalid JSON, the AI endpoint falls back to the existing deterministic scorer.
- Existing endpoint (`/api/recommend`) is unchanged and always deterministic.
- Logs include retrieval count, Groq latency, and fallback events for diagnostics.

## Ranking Formula

For each recipe:

- `exact_match_count = overlap(user_ingredients, recipe_ingredients)`
- `coverage = overlap / total_recipe_ingredients`
- `ingredient_match_ratio = overlap / len(user_ingredients)`
- `score = 0.7 * coverage + 0.3 * ingredient_match_ratio`

Dietary filters are applied before ranking.

## USDA Nutrition Notes

`app/utils/nutrition.py` includes:

- API key via `USDA_API_KEY`
- local JSON caching (`data/nutrition_cache.json`)
- retry handling for rate limit (HTTP 429)
- graceful fallback to zeroed nutrition values on failure

## Production Decisions

- Static local recipe data is used (`data/recipes.json`) to avoid runtime scraping.
- Image classification is optional and does not break recommendations if Torch/Torchvision is unavailable.
- If spaCy model is missing, the system falls back to a blank English tokenizer and logs a warning.
