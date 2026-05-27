# Epicurious Scraper

A polite scraper for Epicurious recipes that performs ingredient extraction
and canonical mapping during scrape time, so the resulting corpus is clean
and consistent enough to drive `pantrypal`'s deterministic normalization.

## Why

`pantrypal/data/recipes.json` is heterogeneous: a small seed of clean records
plus a much larger Epicurious-style dump where every ingredient is a full
recipe-card sentence (e.g. `"1 1/2 pound trimmed boneless center pork loin,
sinew removed, cut into 1-inch chunks, well chilled"`). Only about half of
those lines map to the 177-entry canonical ingredient list, leaving ~38k
unique residue strings.

This scraper re-builds the corpus from Epicurious with structured extraction:

1. Discover meal/snack recipe URLs from the sitemap (filtered by category and
   title hints; sauces, drinks, rubs, spreads, glazes etc. are excluded).
2. Fetch politely (low concurrency, jittered, robots-respecting, on-disk
   cache, resume-safe).
3. Parse `schema.org/Recipe` JSON-LD for title, ingredients, instructions,
   servings, nutrition, category.
4. For each raw ingredient line, run a rule + spaCy NER extractor to recover
   a clean noun phrase (e.g. `"chicken thigh"` from `"4 boneless skinless
   chicken thighs, about 1 1/2 lb"`).
5. Look up each clean phrase against `pantrypal/data/canonical_ingredients.json`.
6. Unmatched phrases go into `unmatched_candidates.csv` with frequency
   counts so you can curate `canonical_ingredients.json` and re-run the
   canonical pass without re-fetching.

## Scope

Meals and snacks only. The non-meal title filter in `discover.py` rejects
titles or categories matching: sauce, dressing, dip, marinade, drink,
smoothie, juice, cocktail, tea, coffee, rub, blend, seasoning, stock,
pickle, relish, chutney, spread, pesto, vinaigrette, aioli, syrup, glaze,
frosting, icing, ganache, compote, jelly, dough, roux.

## Usage

```bash
# from repo root, with the project venv activated
PYTHONPATH=. python -m scraper.cli discover --limit 50 > scraper/data/urls.txt
PYTHONPATH=. python -m scraper.cli scrape --urls scraper/data/urls.txt
PYTHONPATH=. python -m scraper.cli report
```

Outputs land in `scraper/data/`:

* `recipes.jsonl` — one recipe per line, schema-compatible with the
  existing `pantrypal` `Recipe` model plus a `source_url`,
  `recipe_category`, and `ingredients_canonical` audit array.
* `unmatched_candidates.csv` — phrase, frequency, sample raw lines.
* `http_cache/` — on-disk cache of fetched pages so reruns don't re-hit
  Epicurious.

## Tests

```bash
PYTHONPATH=. pytest -q scraper/tests
```

Tests cover JSON-LD parsing, the non-meal title filter, the ingredient
extractor on a hand-picked set of nasty lines, and the re-canonicalize
upgrade flow. No network access required.
