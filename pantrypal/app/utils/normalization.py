"""Ingredient normalization pipeline."""

from __future__ import annotations

from functools import lru_cache
import json
import logging
import re
from typing import Iterable

from rapidfuzz import fuzz, process
import spacy
from spacy.language import Language

from ..config import FUZZY_THRESHOLD, INGREDIENT_VOCAB_PATH

LOGGER = logging.getLogger(__name__)

UNITS = {
    "cup",
    "cups",
    "tbsp",
    "tablespoon",
    "tablespoons",
    "tsp",
    "teaspoon",
    "teaspoons",
    "oz",
    "ounce",
    "ounces",
    "lb",
    "lbs",
    "pound",
    "pounds",
    "gram",
    "grams",
    "g",
    "kg",
    "ml",
    "l",
    "liter",
    "liters",
    "clove",
    "cloves",
    "slice",
    "slices",
    "piece",
    "pieces",
}

QUANTITY_PATTERN = re.compile(r"\b\d+(?:[./]\d+)?\b")
PUNCT_PATTERN = re.compile(r"[^a-zA-Z\s]")
MULTISPACE_PATTERN = re.compile(r"\s+")


@lru_cache(maxsize=1)
def _load_vocab() -> list[str]:
    with INGREDIENT_VOCAB_PATH.open("r", encoding="utf-8") as handle:
        vocab = json.load(handle)

    if not isinstance(vocab, list):
        raise ValueError("ingredients_vocab.json must contain a list")

    return [str(item).strip().lower() for item in vocab if str(item).strip()]


@lru_cache(maxsize=1)
def _get_nlp() -> Language:
    try:
        return spacy.load("en_core_web_sm", disable=["ner", "parser", "textcat"])
    except OSError:
        LOGGER.warning(
            "spaCy model en_core_web_sm not installed; using blank English pipeline fallback."
        )
        return spacy.blank("en")


def _strip_quantities_units(text: str) -> str:
    without_quantities = QUANTITY_PATTERN.sub(" ", text)
    tokens = without_quantities.split()
    filtered = [token for token in tokens if token not in UNITS]
    return " ".join(filtered)


def _lemmatize_text(text: str) -> str:
    nlp = _get_nlp()
    doc = nlp(text)
    lemmas: list[str] = []
    for token in doc:
        lemma = token.lemma_.strip().lower() if token.lemma_ else token.text.lower()
        if lemma and lemma != "-pron-":
            lemmas.append(lemma)
    return " ".join(lemmas)


def _normalize_single(raw_ingredient: str) -> str:
    lower = raw_ingredient.lower().strip()
    no_punct = PUNCT_PATTERN.sub(" ", lower)
    stripped = _strip_quantities_units(no_punct)
    collapsed = MULTISPACE_PATTERN.sub(" ", stripped).strip()
    return _lemmatize_text(collapsed)


def _fuzzy_match(candidate: str, vocab: Iterable[str]) -> str | None:
    match = process.extractOne(candidate, vocab, scorer=fuzz.ratio)
    if not match:
        return None

    best_match, score, _ = match
    if score < FUZZY_THRESHOLD:
        return None
    return best_match


def normalize_ingredients(ingredients: list[str]) -> list[str]:
    """Normalize user ingredient strings into standardized names."""

    if not ingredients:
        return []

    vocab = _load_vocab()
    normalized: list[str] = []

    for raw in ingredients:
        cleaned = _normalize_single(raw)
        if not cleaned:
            LOGGER.warning("Failed to normalize ingredient due to empty tokenization: %s", raw)
            continue

        matched = _fuzzy_match(cleaned, vocab)
        if matched is None:
            LOGGER.warning("No fuzzy vocabulary match for ingredient: %s", raw)
            normalized.append(cleaned)
            continue

        normalized.append(matched)

    return normalized
