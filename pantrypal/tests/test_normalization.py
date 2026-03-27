"""Tests for ingredient normalization."""

from __future__ import annotations

from pantrypal.app.utils.normalization import (
    normalize_ingredient,
    normalize_ingredients,
    with_default_pantry_ingredients,
)


def test_normalize_required_edge_cases() -> None:
    raw = [
        "Fresh Tomatoes",
        "chopped onions",
        "garlic cloves",
        "chicken breasts",
        "extra virgin olive oil",
        "soy sauce",
        "ice cream",
    ]
    normalized = normalize_ingredients(raw)

    assert "tomato" in normalized
    assert "onion" in normalized
    assert "garlic" in normalized
    assert "chicken" in normalized
    assert "olive oil" in normalized
    assert "soy sauce" in normalized
    assert "ice cream" in normalized


def test_normalize_empty_input() -> None:
    assert normalize_ingredients([]) == []


def test_normalize_preserves_unmatched_but_cleaned() -> None:
    raw = ["xyzingredient"]
    normalized = normalize_ingredients(raw)

    assert normalized
    assert normalized[0] == "xyzingredient"


def test_normalize_ingredient_internal_contract_when_unmapped() -> None:
    result = normalize_ingredient("mystery component")

    assert result.raw == "mystery component"
    assert result.normalized == "mystery component"
    assert result.canonical_name is None
    assert result.canonical_id is None


def test_normalize_ingredient_internal_contract_when_mapped() -> None:
    result = normalize_ingredient("garlic cloves")

    assert result.normalized == "garlic clove"
    assert result.canonical_name == "garlic"
    assert result.canonical_id is not None


def test_with_default_pantry_ingredients_adds_staples() -> None:
    ingredients = ["Egg", " spinach "]

    merged = with_default_pantry_ingredients(ingredients)

    assert "Egg" in merged
    assert "spinach" in merged
    assert "salt" in merged
    assert "black pepper" in merged
    assert "water" in merged


def test_with_default_pantry_ingredients_deduplicates_case_insensitive() -> None:
    ingredients = ["salt", "Salt", "black pepper", "WATER"]

    merged = with_default_pantry_ingredients(ingredients)

    lowered = [item.lower() for item in merged]
    assert lowered.count("salt") == 1
    assert lowered.count("black pepper") == 1
    assert lowered.count("water") == 1


def test_deduplicate_after_normalization() -> None:
    normalized = normalize_ingredients(["Tomatoes", "tomato", "fresh tomatoes"])

    assert normalized
    assert normalized == ["tomato"]


def test_normalize_strips_measurement_and_descriptors_for_zest() -> None:
    result = normalize_ingredient("1 teaspoon finely grated lemon zest")

    assert result.normalized == "lemon zest"


def test_normalize_strips_leading_fillers() -> None:
    result = normalize_ingredient("to beef tenderloin steak")

    assert result.normalized == "beef tenderloin steak"


def test_normalize_ingredients_skips_special_equipment_lines() -> None:
    normalized = normalize_ingredients([
        "Special equipment: blender",
        "egg",
        "Equipment: baking tray",
    ])

    assert "egg" in normalized
    assert all("equipment" not in item for item in normalized)


def test_new_descriptors_strip_prep_state_modifiers() -> None:
    """boneless, skinless, canned, frozen, dried should all be stripped."""
    cases = [
        ("boneless chicken thighs", "chicken"),
        ("skinless chicken breast", "chicken"),
        ("canned black beans", "black bean"),
        ("frozen spinach", "spinach"),
        ("dried brown lentils", "lentil"),
    ]
    for raw, expected_canonical in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected_canonical, (
            f"Expected canonical '{expected_canonical}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_descriptors_strip_cooking_state_modifiers() -> None:
    """shredded, roasted, cooked, ground should all be stripped."""
    cases = [
        ("ground beef", "beef"),
        ("ground turkey", "turkey"),
        ("shredded mozzarella", "mozzarella"),
        # "roasted red pepper" → strip "roasted" → "red pepper".
        # "red pepper" alone has no canonical entry (removed the ambiguous
        # "crushed red pepper" alias that was creating a false hit on "red pepper flakes").
        ("roasted red pepper", None),
    ]
    for raw, expected_canonical in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected_canonical, (
            f"Expected canonical '{expected_canonical}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_descriptors_strip_anatomical_cut_tokens() -> None:
    """loin, shoulder, chuck, flank should be stripped so the protein matches."""
    cases = [
        ("pork loin", "pork"),
        ("pork shoulder", "pork"),
        ("beef chuck", "beef"),
        ("beef flank", "beef"),
    ]
    for raw, expected_canonical in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected_canonical, (
            f"Expected canonical '{expected_canonical}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_descriptors_multi_modifier_chain_canonicalizes() -> None:
    """Stacked prep state + anatomical modifiers should both be stripped."""
    result = normalize_ingredient("boneless skinless chicken thighs")
    assert result.canonical_name == "chicken"

    result2 = normalize_ingredient("trimmed boneless pork loin")
    assert result2.canonical_name == "pork"


def test_sub_phrase_fallback_drops_leading_tokens() -> None:
    """3-token phrases where the meaningful part is at the end should still resolve."""
    # "low" is stripped as a descriptor, leaving "sodium chicken broth" (3 tokens).
    # Sub-phrase drops "sodium" → "chicken broth" → alias for canonical "broth".
    result = normalize_ingredient("low sodium chicken broth")
    assert result.canonical_name == "broth"


def test_sub_phrase_fallback_drops_trailing_tokens() -> None:
    """3-token phrases where the meaningful part is at the front should still resolve."""
    # "chicken thigh meat" → no descriptor matches "thigh" or "meat" → 3 tokens →
    # dropping trailing "meat" → "chicken thigh" → alias for canonical "chicken".
    result = normalize_ingredient("chicken thigh meat")
    assert result.canonical_name == "chicken"


def test_sub_phrase_fallback_does_not_trigger_for_two_token_phrases() -> None:
    """2-token ingredient names like 'sweet potato' must not be reduced by sub-phrase."""
    result = normalize_ingredient("sweet potato")
    assert result.canonical_name == "sweet potato"

    result2 = normalize_ingredient("bell pepper")
    assert result2.canonical_name == "bell pepper"

    result3 = normalize_ingredient("black bean")
    assert result3.canonical_name == "black bean"


def test_sub_phrase_fallback_preserves_normalized_field() -> None:
    """The .normalized field must always equal the cleaned input phrase, never a sub-phrase."""
    result = normalize_ingredient("low sodium chicken broth")
    # canonical found via sub-phrase fallback
    assert result.canonical_name == "broth"
    # but .normalized is always the cleaned input, not the matched sub-phrase
    assert result.normalized == "sodium chicken broth"


def test_new_canonical_dairy_ingredients_resolve() -> None:
    """Newly added dairy canonical entries should resolve correctly."""
    cases = [
        ("parmesan cheese", "parmesan"),
        ("mozzarella cheese", "mozzarella"),
        ("feta", "feta cheese"),
        ("crumbled feta cheese", "feta cheese"),
        ("greek yogurt", "greek yogurt"),
        ("plain greek yogurt", "greek yogurt"),
        ("cream cheese", "cream cheese"),
        ("heavy cream", "heavy cream"),
        ("sour cream", "sour cream"),
    ]
    for raw, expected in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected, (
            f"Expected '{expected}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_canonical_pantry_ingredients_resolve() -> None:
    """Newly added pantry canonical entries should resolve correctly."""
    cases = [
        ("fresh ginger", "ginger"),
        ("ginger root", "ginger"),
        ("shallots", "shallot"),
        ("granulated sugar", "sugar"),
        ("packed brown sugar", "brown sugar"),
        ("pure vanilla extract", "vanilla extract"),
        ("bay leaves", "bay leaf"),
    ]
    for raw, expected in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected, (
            f"Expected '{expected}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_canonical_nut_ingredients_resolve() -> None:
    """Newly added nut canonical entries should resolve correctly."""
    cases = [
        ("almonds", "almond"),
        ("walnut halves", "walnut"),
        ("pecans", "pecan"),
        ("pine nuts", "pine nut"),
    ]
    for raw, expected in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected, (
            f"Expected '{expected}' for '{raw}', got '{result.canonical_name}'"
        )


def test_new_canonical_protein_ingredients_resolve() -> None:
    """Newly added protein canonical entries should resolve correctly."""
    cases = [
        ("cooked ham", "ham"),
        ("diced pancetta", "pancetta"),
        ("anchovy fillet", "anchovy"),
        ("scallops", "scallop"),
        ("duck breast", "duck"),
    ]
    for raw, expected in cases:
        result = normalize_ingredient(raw)
        assert result.canonical_name == expected, (
            f"Expected '{expected}' for '{raw}', got '{result.canonical_name}'"
        )


def test_normalize_essential_spice_aliases_and_misspellings() -> None:
    normalized = normalize_ingredients(
        [
            "black pepper",
            "cumin",
            "paprika",
            "garlic powder",
            "oregeno",
            "coriander",
            "tumeric",
            "chili powder/cayenne",
            "cinnamon",
            "red pepper flakes",
            "salt",
        ]
    )

    assert "black pepper" in normalized
    assert "cumin" in normalized
    assert "paprika" in normalized
    assert "garlic powder" in normalized
    assert "oregano" in normalized
    assert "coriander" in normalized
    assert "turmeric" in normalized
    assert "chili powder" in normalized
    assert "cinnamon" in normalized
    assert "red pepper flakes" in normalized
    assert "salt" in normalized
