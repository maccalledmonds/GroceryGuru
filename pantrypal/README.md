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
