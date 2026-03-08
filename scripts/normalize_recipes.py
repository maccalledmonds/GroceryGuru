"""
One-time script: add `ingredients_normalized` to every recipe in recipes.json.

For recipes that already have clean ingredient names (ids 1–10), the field is
copied directly.  For scraped recipes with raw strings like
"3 medium carrots, cut into julienne strips", each string is cleaned to just
"carrot" using pure-regex logic (no spaCy) so the script runs in seconds,
not hours.

The original `ingredients` list is left completely untouched.

Usage (run from the GroceryGuru repo root):
    python scripts/normalize_recipes.py
    python scripts/normalize_recipes.py --dry-run     # preview only, no write
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).resolve().parent.parent
RECIPES_PATH = REPO_ROOT / "pantrypal" / "data" / "recipes.json"
BACKUP_PATH  = REPO_ROOT / "pantrypal" / "data" / "recipes.json.bak"
VOCAB_PATH   = REPO_ROOT / "pantrypal" / "data" / "ingredients_vocab.json"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Leading quantity: integers, decimals, fractions ("1", "1/2", "1 1/2", "2.5")
_QUANTITY = re.compile(r"^\s*\d+(?:[./]\d+)?(?:\s+\d+/\d+)?\s*")

# Parenthetical groups anywhere: "(28-ounce)", "(about 2 cobs)"
_PARENS = re.compile(r"\([^)]*\)")

# Measurement units (standalone word boundaries)
_UNITS = re.compile(
    r"\b(?:cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|"
    r"oz|ounce|ounces|lb|lbs|pound|pounds|gram|grams|g|kg|ml|l|liter|liters|"
    r"clove|cloves|slice|slices|piece|pieces|can|cans|package|packages|pkg|"
    r"bunch|bunches|sprig|sprigs|head|heads|stalk|stalks|stick|sticks|"
    r"pinch|dash|handful|knob|drizzle|splash|sheet|strip|strips|"
    r"pint|quart|gallon|fluid)\b",
    re.IGNORECASE,
)

# Noise adjectives / state descriptors that don't name the ingredient
_NOISE_WORDS = re.compile(
    r"\b(?:large|medium|small|mini|extra|big|tiny|"
    r"whole|fresh|dried|frozen|canned|raw|cooked|organic|ripe|"
    r"rinsed|drained|softened|peeled|pitted|chopped|minced|grated|"
    r"sliced|diced|crushed|ground|shredded|trimmed|halved|quartered|"
    r"toasted|roasted|skinless|boneless|lean|low.sodium|low.fat|non.fat|"
    r"salted|unsalted|uncooked|undrained|unpacked|packed|"
    r"room|temperature|about|approximately|roughly|"
    r"\ba\b|\ban\b|\bthe\b)\b",
    re.IGNORECASE,
)

# Hyphenated numeric-unit compounds: "12-ounce", "1/2-inch-thick", "6-oz", "3-pound"
# Must be matched before regular unit stripping.
_NUM_UNIT_HYPHEN = re.compile(
    r"\b\d+(?:[./]\d+)?(?:-\d+(?:[./]\d+)?)*-"
    r"(?:ounce|ounces|oz|inch|inches|pound|pounds|lb|lbs|gram|grams|cm|mm|ml|liter|liters|thick|wide|long)\b",
    re.IGNORECASE,
)

# Dangling hyphens left after a word is removed:
#   leading  → "-virgin" from removing "extra" in "extra-virgin"
#   trailing → "thick-"  from removing "sliced" in "thick-sliced"
_DANGLING_HYPHEN = re.compile(r"\s-\w+|^-\w+|\w+-\s|\w+-$")

# Residual isolated numbers not caught by the leading-quantity strip (e.g. "14" in "14 cans diced tomatoes")
_RESIDUAL_DIGITS = re.compile(r"\b\d+\b")

# Prepositions / conjunctions that bind descriptor phrases but name no ingredient
_PREPOSITIONS = re.compile(r"\b(?:with|without|in|of|and|or|from|by|for)\b", re.IGNORECASE)

# Collapse multiple spaces
_SPACES = re.compile(r"\s+")

# Simple English plural endings.
# Strip -ies→-y, -ves→-f, -oes→-o (tomatoes→tomato), otherwise just strip trailing -s.
def _depluralize(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ves") and len(word) > 4:
        return word[:-3] + "f"
    if word.endswith("oes") and len(word) > 4:
        return word[:-2]           # "potatoes" → "potato", "tomatoes" → "tomato"
    if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
        return word[:-1]
    return word


def _clean_raw_ingredient(raw: str) -> str:
    """
    Strip quantity / prep metadata from a raw scraped ingredient string.

    Examples
    --------
    "3 medium carrots, cut into julienne strips"  →  "carrot"
    "1 (28-ounce) can whole tomatoes in juice"    →  "tomato"
    "2 garlic cloves, finely chopped"             →  "garlic"
    "Kosher salt"                                 →  "salt"
    "1/2 yellow onion, chopped"                   →  "onion"
    "2 6-ounce beef tenderloin steaks"            →  "beef tenderloin"
    """
    text = raw.strip()

    # 1. Keep only the clause before the first comma  (removes prep notes)
    text = text.split(",")[0]

    # 2. Remove parentheticals
    text = _PARENS.sub(" ", text)

    # 3. Remove hyphenated numeric-unit compounds ("12-ounce", "1/2-inch-thick")
    #    before the leading-quantity strip so they don't leave dangling hyphens.
    text = _NUM_UNIT_HYPHEN.sub(" ", text)

    # 4. Strip leading quantity expression
    text = _QUANTITY.sub("", text)

    # 5. Remove unit words
    text = _UNITS.sub(" ", text)

    # 6. Remove noise adjectives / state words
    text = _NOISE_WORDS.sub(" ", text)

    # 7. Remove dangling hyphens left by word-removal (e.g. "-virgin", "-wide")
    text = _DANGLING_HYPHEN.sub(" ", text)

    # 8. Remove residual isolated numbers and prepositions/conjunctions
    text = _RESIDUAL_DIGITS.sub(" ", text)
    text = _PREPOSITIONS.sub(" ", text)

    # 9. Lowercase and collapse whitespace
    text = _SPACES.sub(" ", text.lower()).strip()

    # 10. Depluralize each token
    tokens = [_depluralize(t) for t in text.split()]
    text = " ".join(tokens).strip()

    return text


# ---------------------------------------------------------------------------
# Vocab loading + fuzzy matching (no spaCy required)
# ---------------------------------------------------------------------------

def _load_vocab() -> list[str]:
    with VOCAB_PATH.open("r", encoding="utf-8") as fh:
        vocab = json.load(fh)
    return [str(v).strip().lower() for v in vocab if str(v).strip()]


def _fuzzy_match(candidate: str, vocab: list[str], threshold: int = 85) -> str | None:
    """
    Return the best vocab match above threshold, or None.

    Uses fuzz.ratio (full-string edit-distance) with a threshold of 85 rather
    than WRatio/partial_ratio so that partial substring matches (e.g.
    "chicken broth" hitting "chicken breast" at ~81%) don't produce false
    positives.  Items that don't hit the threshold are kept as their cleaned
    descriptors, which is still far superior to the raw scraped string.
    """
    from rapidfuzz import fuzz, process
    result = process.extractOne(candidate, vocab, scorer=fuzz.ratio)
    if result and result[1] >= threshold:
        return result[0]
    return None


def normalize_recipe_ingredients(ingredients: list[str], vocab: list[str]) -> list[str]:
    """
    Return a deduplicated list of normalized ingredient names for one recipe.

    Strategy
    --------
    1. Clean the raw string down to a short core descriptor.
    2. Fuzzy-match against the known vocab — if confident, use the canonical
       vocab term (ensures exact overlap with user inputs that also go through
       the vocab matcher).
    3. Otherwise keep the cleaned descriptor as-is (still far better than the
       original scraped string and will benefit from partial fuzzy scoring).
    4. Drop empty strings; deduplicate while preserving order.
    """
    seen: set[str] = set()
    result: list[str] = []

    for raw in ingredients:
        cleaned = _clean_raw_ingredient(raw)
        if not cleaned:
            continue

        matched = _fuzzy_match(cleaned, vocab)
        term = matched if matched else cleaned

        if term not in seen:
            seen.add(term)
            result.append(term)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize recipe ingredients in recipes.json")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only; do not write")
    args = parser.parse_args()

    print(f"Loading {RECIPES_PATH} …")
    with RECIPES_PATH.open("r", encoding="utf-8") as fh:
        recipes: list[dict] = json.load(fh)
    print(f"  {len(recipes):,} recipes found")

    vocab = _load_vocab()
    print(f"  Vocab size: {len(vocab)} terms")

    already_normalized = 0
    newly_normalized   = 0

    for i, recipe in enumerate(recipes):
        if (i + 1) % 2000 == 0:
            print(f"  Processed {i + 1:,} / {len(recipes):,} …")

        existing = recipe.get("ingredients_normalized")
        if isinstance(existing, list) and existing:
            already_normalized += 1
            continue

        raw_ingredients: list[str] = recipe.get("ingredients", [])
        recipe["ingredients_normalized"] = normalize_recipe_ingredients(raw_ingredients, vocab)
        newly_normalized += 1

    print(f"\nDone.")
    print(f"  Already had ingredients_normalized : {already_normalized:,}")
    print(f"  Newly normalized                   : {newly_normalized:,}")

    if args.dry_run:
        print("\n--- Dry-run sample (8 scraped recipes) ---")
        shown = 0
        for recipe in recipes:
            raw  = recipe.get("ingredients", [])
            norm = recipe.get("ingredients_normalized", [])
            if any(len(r) > 25 for r in raw):
                print(f'\n  "{recipe["title"][:60]}"')
                print(f'  RAW  ({len(raw)} ingredients):')
                for r in raw[:6]:
                    print(f'    - {r[:70]!r}')
                print(f'  NORMALIZED  ({len(norm)} after dedup):')
                for n in norm[:6]:
                    print(f'    → {n!r}')
                shown += 1
                if shown >= 8:
                    break
        print("\nDry-run complete — no file was modified.")
        return

    print(f"\nBacking up original → {BACKUP_PATH} …")
    shutil.copy2(RECIPES_PATH, BACKUP_PATH)

    print(f"Writing updated recipes → {RECIPES_PATH} …")
    with RECIPES_PATH.open("w", encoding="utf-8") as fh:
        json.dump(recipes, fh, ensure_ascii=False, indent=2)

    print("All done. Original preserved at recipes.json.bak")


if __name__ == "__main__":
    main()
