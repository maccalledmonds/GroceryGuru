"""Deterministic ingredient normalization using canonical dataset mappings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import logging
import re

from ..config import CANONICAL_INGREDIENTS_PATH, DEFAULT_PANTRY_INGREDIENTS

LOGGER = logging.getLogger(__name__)

DESCRIPTORS: frozenset[str] = frozenset(
    {
        "fresh",
        "chopped",
        "diced",
        "sliced",
        "organic",
        "large",
        "small",
        "extra",
        "virgin",
    }
)

MULTISPACE_PATTERN = re.compile(r"\s+")
PUNCT_TO_SPACE_PATTERN = re.compile(r"[-/,.():;&]")
OTHER_PUNCT_PATTERN = re.compile(r"[^a-z0-9\s]")

IRREGULAR_SINGULARS = {
    "tomatoes": "tomato",
    "potatoes": "potato",
    "leaves": "leaf",
    "knives": "knife",
    "loaves": "loaf",
    "wives": "wife",
    "wolves": "wolf",
    "shelves": "shelf",
    "thieves": "thief",
    "lives": "life",
    "people": "person",
    "teeth": "tooth",
    "feet": "foot",
    "children": "child",
    "men": "man",
    "women": "woman",
    "eggs": "egg",
    "peppers": "pepper",
    "onions": "onion",
    "cloves": "clove",
}


@dataclass(frozen=True, slots=True)
class CanonicalMatch:
    """Canonical mapping for a normalized ingredient phrase."""

    canonical_id: str
    canonical_name: str


@dataclass(frozen=True, slots=True)
class NormalizedIngredient:
    """Internal normalization result contract."""

    raw: str
    normalized: str
    canonical_name: str | None
    canonical_id: str | None


@dataclass(frozen=True, slots=True)
class CanonicalIndex:
    """In-memory canonical mapping index with deterministic lookups."""

    by_phrase: dict[str, CanonicalMatch]


def _normalize_dataset_phrase(value: str) -> str:
    lowered = value.strip().lower()
    return MULTISPACE_PATTERN.sub(" ", lowered).strip()


def _normalize_lookup_phrase_for_index(value: str) -> str:
    """Normalize dataset phrases into the same lookup form used for input phrases."""

    lowered = value.strip().lower()
    no_punct = _remove_punctuation(lowered)
    no_descriptors = _remove_descriptors(no_punct)
    normalized_space = MULTISPACE_PATTERN.sub(" ", no_descriptors).strip()
    singularized = _singularize_phrase(normalized_space)
    return MULTISPACE_PATTERN.sub(" ", singularized).strip()


@lru_cache(maxsize=1)
def _load_canonical_index() -> CanonicalIndex:
    with CANONICAL_INGREDIENTS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    ingredients = payload.get("ingredients") if isinstance(payload, dict) else None
    if not isinstance(ingredients, list):
        raise ValueError("canonical_ingredients.json must contain an ingredients array")

    by_phrase: dict[str, CanonicalMatch] = {}

    for item in ingredients:
        if not isinstance(item, dict):
            raise ValueError("canonical ingredient records must be objects")

        canonical_id = str(item.get("id", "")).strip()
        canonical_name = _normalize_dataset_phrase(str(item.get("canonical_name", "")))
        aliases_raw = item.get("aliases", [])

        if not canonical_id or not canonical_name:
            raise ValueError("canonical ingredient record missing id or canonical_name")
        if not isinstance(aliases_raw, list):
            raise ValueError(f"aliases must be a list for {canonical_id}")

        mapping = CanonicalMatch(canonical_id=canonical_id, canonical_name=canonical_name)

        phrase_candidates = [canonical_name]
        for alias in aliases_raw:
            alias_phrase = _normalize_dataset_phrase(str(alias))
            if alias_phrase:
                phrase_candidates.append(alias_phrase)

        for phrase in phrase_candidates:
            lookup_phrase = _normalize_lookup_phrase_for_index(phrase)
            if not lookup_phrase:
                continue

            existing = by_phrase.get(lookup_phrase)
            if existing is not None and existing.canonical_id != canonical_id:
                raise ValueError(
                    "Alias/canonical collision detected for phrase "
                    f"'{lookup_phrase}' between {existing.canonical_id} and {canonical_id}"
                )
            by_phrase[lookup_phrase] = mapping

    return CanonicalIndex(by_phrase=by_phrase)


def _remove_punctuation(text: str) -> str:
    punctuation_to_space = PUNCT_TO_SPACE_PATTERN.sub(" ", text)
    no_apostrophe = punctuation_to_space.replace("'", "")
    return OTHER_PUNCT_PATTERN.sub(" ", no_apostrophe)


def _remove_descriptors(text: str) -> str:
    tokens = text.split()
    kept = [token for token in tokens if token not in DESCRIPTORS]
    return " ".join(kept)


def _singularize_token(token: str) -> str:
    if not token:
        return token
    if token in IRREGULAR_SINGULARS:
        return IRREGULAR_SINGULARS[token]
    if token.endswith("ies") and len(token) > 3:
        return token[:-3] + "y"
    if token.endswith("oes") and len(token) > 3:
        return token[:-2]
    if token.endswith("s") and len(token) > 1 and not token.endswith(("ss", "us")):
        return token[:-1]
    return token


def _singularize_phrase(text: str) -> str:
    singularized = [_singularize_token(token) for token in text.split()]
    return " ".join(token for token in singularized if token)


def normalize_ingredient(raw_ingredient: str) -> NormalizedIngredient:
    """Normalize a single ingredient deterministically and map to canonical dataset."""

    lowered = raw_ingredient.strip().lower()
    no_punct = _remove_punctuation(lowered)
    no_descriptors = _remove_descriptors(no_punct)
    normalized_space = MULTISPACE_PATTERN.sub(" ", no_descriptors).strip()
    singularized = _singularize_phrase(normalized_space)

    lookup_phrase = MULTISPACE_PATTERN.sub(" ", singularized).strip()
    if not lookup_phrase:
        return NormalizedIngredient(
            raw=raw_ingredient,
            normalized="",
            canonical_name=None,
            canonical_id=None,
        )

    index = _load_canonical_index()
    match = index.by_phrase.get(lookup_phrase)
    if match is None:
        return NormalizedIngredient(
            raw=raw_ingredient,
            normalized=lookup_phrase,
            canonical_name=None,
            canonical_id=None,
        )

    return NormalizedIngredient(
        raw=raw_ingredient,
        normalized=lookup_phrase,
        canonical_name=match.canonical_name,
        canonical_id=match.canonical_id,
    )


def with_default_pantry_ingredients(ingredients: list[str]) -> list[str]:
    """Return ingredients plus always-available pantry staples (deduplicated)."""

    deduped: dict[str, str] = {}

    for raw in ingredients:
        cleaned = raw.strip()
        if not cleaned:
            continue
        deduped.setdefault(cleaned.lower(), cleaned)

    for staple in DEFAULT_PANTRY_INGREDIENTS:
        deduped.setdefault(staple.lower(), staple)

    return list(deduped.values())


def normalize_ingredients(ingredients: list[str]) -> list[str]:
    """Normalize ingredient strings and return canonical names or deterministic fallback."""

    if not ingredients:
        return []

    normalized_values: list[str] = []

    for raw in ingredients:
        normalized = normalize_ingredient(raw)
        if not normalized.normalized:
            LOGGER.warning("Failed to normalize ingredient due to empty tokenization: %s", raw)
            continue

        normalized_values.append(normalized.canonical_name or normalized.normalized)

    # Deduplicate after normalization while preserving stable input order.
    deduped: dict[str, str] = {}
    for item in normalized_values:
        deduped.setdefault(item, item)
    return list(deduped.values())
