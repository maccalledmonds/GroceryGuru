"""Tests for the scrape-time ingredient extractor."""

from __future__ import annotations

import pytest

from scraper.ingredient_parser import extract_ingredient


@pytest.mark.parametrize(
    "raw,expected_token",
    [
        # The hard one from the actual recipes.json: long modifier-laden pork loin line.
        # pantrypal's existing DESCRIPTORS treat "loin", "shoulder", "chuck", etc.
        # as descriptors because canonical_ingredients.json already maps cuts to
        # the parent meat (e.g. "pork loin" -> alias of canonical "pork").
        (
            "1 pound trimmed boneless center pork loin, sinew removed cut into 1-inch chunks, well chilled",
            "pork",
        ),
        # Trailing modifier clause should be dropped.
        ("1 5 3/4-pound bone-in leg of lamb, well trimmed", "leg of lamb"),
        # Simple quantity + adjective + noun.
        ("2 medium onions, chopped", "onion"),
        # Parenthetical aside.
        ("1 cup low-sodium chicken broth (preferably homemade)", "chicken broth"),
        # Hyphenated unit prefix.
        ("12 ounces crusty Italian or country-style bread", "bread"),
        # "Of" filler.
        ("Pinch of dried thyme, crumbled", "thyme"),
        # Already-clean canonical name should survive untouched.
        ("garlic", "garlic"),
        # Fresh + plural.
        ("1 cup fresh basil leaves", "basil leaf"),
        # Pepper-style standalone tokens.
        ("3 whole cloves", "clove"),
    ],
)
def test_extract_ingredient_recovers_head_noun(raw: str, expected_token: str) -> None:
    result = extract_ingredient(raw)
    assert expected_token in result.clean_phrase, (
        f"raw={raw!r} clean_phrase={result.clean_phrase!r} pre_clean={result.pre_clean!r}"
    )


def test_extract_ingredient_handles_empty_and_whitespace() -> None:
    assert extract_ingredient("").clean_phrase == ""
    assert extract_ingredient("   ").clean_phrase == ""
