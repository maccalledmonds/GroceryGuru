"""Integration test: HTML fixture -> ParsedRecipe -> RecipeRecord."""

from __future__ import annotations

import json
from pathlib import Path

from scraper.canonicalize import UnmatchedReport
from scraper.parse import parse_recipe_html
from scraper.pipeline import _build_record, recanonicalize_existing

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_record_from_meal_fixture(tmp_path: Path) -> None:
    html = (FIXTURES / "sample_recipe.html").read_text(encoding="utf-8")
    parsed = parse_recipe_html(html, source_url="https://example.test/recipe")
    assert parsed is not None and parsed.is_meal_candidate

    report = UnmatchedReport()
    record = _build_record(recipe_id=1, parsed=parsed, report=report)
    assert record.title == "Roasted Chicken Thighs With Lemon and Herbs"
    assert record.source_url == "https://example.test/recipe"
    assert record.servings == 4
    assert len(record.ingredients) == 8
    assert len(record.ingredients_canonical) == 8
    # At least chicken, olive oil, lemon, garlic, rosemary, salt, pepper, broth
    # should map to canonical names.
    matched = [item for item in record.ingredients_canonical if item["matched"]]
    assert len(matched) >= 5, record.ingredients_canonical


def test_recanonicalize_existing_upgrades_records(tmp_path: Path) -> None:
    # Seed a JSONL file with one record whose ingredients_canonical was
    # all unmatched. The "clean_phrase" is a known canonical alias, so a
    # fresh re-canonicalize pass should upgrade it.
    output = tmp_path / "recipes.jsonl"
    report = tmp_path / "unmatched.csv"
    rec = {
        "id": 1,
        "title": "Test Soup",
        "source_url": "https://example.test/soup",
        "recipe_category": ["soup"],
        "ingredients": ["1 cup chicken broth"],
        "ingredients_normalized": ["chicken broth"],
        "ingredients_canonical": [
            {
                "raw": "1 cup chicken broth",
                "clean_phrase": "chicken broth",
                "canonical_id": None,
                "canonical_name": None,
                "matched": False,
            }
        ],
        "instructions": "Heat the broth.",
        "diet_tags": [],
        "nutrition": {},
        "servings": 4,
    }
    output.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    stats = recanonicalize_existing(output_path=output, unmatched_report_path=report)
    assert stats["updated"] == 1
    written = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    audit = written["ingredients_canonical"][0]
    # "chicken broth" maps to broth via alias in canonical_ingredients.json.
    assert audit["matched"] is True
    assert audit["canonical_name"] == "broth"
