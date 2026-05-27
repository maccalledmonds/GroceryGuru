"""Ingredient extraction at scrape time: strong rules with spaCy as tiebreaker.

For each raw ingredient line (e.g. ``"1 1/2 pound trimmed boneless center pork
loin, sinew removed cut into 1-inch chunks, well chilled"``) we run a
deterministic pre-clean to drop quantity/unit/parenthetical/comma-modifier
clauses, then strip descriptors and singularize using the existing
``pantrypal.app.utils.normalization`` helpers. spaCy is only invoked as a
disambiguator when the cleaned phrase still contains conjunctions or
prepositions that point to multiple candidate noun phrases.

This module lives in the scraper package, not in ``pantrypal``. It runs only
at scrape time, never at runtime. Runtime normalization inside ``pantrypal``
remains rule-based as the project requires.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache

import spacy
from spacy.language import Language

from pantrypal.app.utils.normalization import (
    DESCRIPTORS as PANTRYPAL_DESCRIPTORS,
    LEADING_FILLER_TOKENS,
    MULTISPACE_PATTERN,
    NUMERIC_TOKEN_PATTERN,
    UNIT_TOKENS,
    _remove_punctuation,
    _singularize_phrase,
    _strip_leading_fillers,
)

LOGGER = logging.getLogger(__name__)

PARENS_PATTERN = re.compile(r"\([^)]*\)")
BRACKETS_PATTERN = re.compile(r"\[[^\]]*\]")
# Compound descriptors that get destroyed by punctuation-stripping. Handle
# them up front so "bone-in leg of lamb" doesn't decay into "bone in leg of
# lamb" and confuse the parser.
COMPOUND_DESCRIPTOR_PATTERN = re.compile(
    r"\b(?:bone[\s-]?in|bone[\s-]?less|skin[\s-]?on|skin[\s-]?less|"
    r"sugar[\s-]?free|fat[\s-]?free|gluten[\s-]?free|"
    r"low[\s-]?(?:sodium|fat|sugar|carb)|reduced[\s-]?(?:sodium|fat|sugar))\b",
    re.IGNORECASE,
)
# A trailing " or X" alternative inside an ingredient line. E.g. "vegetable
# oil or canola oil" -> "vegetable oil". Conservatively only stripped when
# preceded by at least one word.
OR_ALTERNATIVE_PATTERN = re.compile(r"\s+or\s+.*$", re.IGNORECASE)
CONJUNCTION_TOKENS: frozenset[str] = frozenset({"and", "or", "with", "plus"})

# Scraper-side descriptors that are NOT yet in pantrypal's DESCRIPTORS but
# show up constantly in Epicurious lines. Keeping these here (rather than
# editing pantrypal/normalization.py) means runtime normalization stays
# unchanged while scrape-time cleaning gets stricter.
EXTRA_DESCRIPTORS: frozenset[str] = frozenset(
    {
        # Size adjectives
        "medium",
        "mini",
        "tiny",
        "huge",
        "giant",
        "jumbo",
        # Ripeness / maturity
        "ripe",
        "unripe",
        "young",
        "mature",
        "baby",
        "new",
        # Preparation participles that pantrypal's set misses
        "softened",
        "chilled",
        "warm",
        "warmed",
        "melted",
        "stirred",
        "rinsed",
        "drained",
        "patted",
        "blotted",
        "discarded",
        "reserved",
        "torn",
        "snipped",
        "stemmed",
        "rolled",
        "broken",
        "scraped",
        "quartered",
        "julienned",
        "rough",
        "fine",
        # Generic intensifiers
        "very",
        "really",
        "slightly",
        "loosely",
        "tightly",
        "packed",
        "lightly",
        "good",
        "quality",
        "store",
        "bought",
        "homemade",
        # Source/quality words
        "imported",
        "domestic",
        "best",
        "premium",
        "kosher",
        "sea",
        "table",
        "fine",
        # Color qualifiers (sometimes part of canonical, but stripping at
        # scrape time is safe because canonical_ingredients.json normalizes
        # them: e.g. "yellow onion" -> alias of "onion").
        # Intentionally NOT stripping color tokens here — they're meaningful
        # for ingredients like "red wine", "white wine", "black bean", etc.
        # Trailing room-temperature noise
        "room",
        "temperature",
    }
)
SCRAPER_DESCRIPTORS: frozenset[str] = PANTRYPAL_DESCRIPTORS | EXTRA_DESCRIPTORS

# Tokens that signal "this comma-clause is a modifier; drop everything from
# this comma onward". Checked against the first 3 tokens of each tail.
COMMA_TAIL_CUES: frozenset[str] = frozenset(
    {
        "cut",
        "sliced",
        "chopped",
        "diced",
        "minced",
        "peeled",
        "trimmed",
        "halved",
        "quartered",
        "crushed",
        "ground",
        "grated",
        "rinsed",
        "drained",
        "thawed",
        "seeded",
        "cored",
        "pitted",
        "stemmed",
        "rolled",
        "shredded",
        "crumbled",
        "torn",
        "discarded",
        "reserved",
        "broken",
        "well",
        "lightly",
        "finely",
        "coarsely",
        "roughly",
        "thinly",
        "thickly",
        "softened",
        "melted",
        "chilled",
        "about",
        "preferably",
        "removed",
        "cleaned",
        "patted",
        "blotted",
        "warmed",
        "warm",
    }
)
COMMA_TAIL_PHRASE_CUES: tuple[str, ...] = (
    "plus more",
    "for serving",
    "for garnish",
    "to taste",
    "for brushing",
    "for drizzling",
    "for dusting",
    "for sprinkling",
    "such as",
    "at room temperature",
)

# Additional quantity-side filler tokens that show up before the noun.
QUANTITY_FILLER_TOKENS: frozenset[str] = frozenset(
    {
        "about",
        "approximately",
        "a",
        "an",
        "the",
        "or",
        "plus",
        "more",
        "of",
        "for",
        "serving",
        "garnish",
        "pinch",
        "dash",
        "handful",
        "bunch",
        "head",
        "heads",
        "package",
        "packages",
        "pkg",
        "container",
        "containers",
        "jar",
        "jars",
        "can",
        "cans",
        "bottle",
        "bottles",
        "box",
        "boxes",
        "stick",
        "sticks",
        "bag",
        "bags",
    }
)


@dataclass(frozen=True, slots=True)
class ExtractedIngredient:
    """Result of scrape-time ingredient extraction."""

    raw: str
    clean_phrase: str
    """Cleaned noun phrase suitable for canonical lookup."""

    pre_clean: str
    """Intermediate cleaned form (debug-only; produced before final descriptor pass)."""


@lru_cache(maxsize=1)
def _nlp() -> Language:
    """Load the spaCy pipeline (lazy, cached).

    Honors ``SPACY_MODEL_PATH`` if set — useful in CI/sandbox environments
    where the model can't be installed but is available on disk.
    """

    override = os.environ.get("SPACY_MODEL_PATH")
    if override:
        return spacy.load(override)
    try:
        return spacy.load("en_core_web_sm")
    except OSError as exc:  # pragma: no cover - environmental
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. Run "
            "`python -m spacy download en_core_web_sm`."
        ) from exc


def _strip_compound_descriptors(text: str) -> str:
    return COMPOUND_DESCRIPTOR_PATTERN.sub(" ", text)


def _strip_trailing_modifier_clauses(text: str) -> str:
    """Walk comma-separated parts and drop from the first modifier clause on."""

    if "," not in text:
        return text
    parts = text.split(",")
    kept: list[str] = [parts[0]]
    for tail in parts[1:]:
        tail_stripped = tail.strip().lower()
        if not tail_stripped:
            continue
        if any(phrase in tail_stripped for phrase in COMMA_TAIL_PHRASE_CUES):
            break
        head_tokens = tail_stripped.split()[:3]
        if any(tok in COMMA_TAIL_CUES for tok in head_tokens):
            break
        kept.append(tail)
    return ",".join(kept)


def _strip_or_alternative(text: str) -> str:
    """Drop a trailing ``or X`` alternative if the head has at least one word."""

    match = OR_ALTERNATIVE_PATTERN.search(text)
    if not match:
        return text
    head = text[: match.start()].strip()
    # Only drop the alternative if the head is substantive (>= 1 word).
    if len(head.split()) >= 1:
        return head
    return text


def _strip_leading_quantity(text: str) -> str:
    """Drop leading numeric/unit/filler tokens until the first content token."""

    tokens = text.split()
    out: list[str] = []
    leading = True
    for tok in tokens:
        tok_lower = tok.lower()
        if leading:
            if NUMERIC_TOKEN_PATTERN.match(tok):
                continue
            if tok_lower in UNIT_TOKENS:
                continue
            if tok_lower in QUANTITY_FILLER_TOKENS:
                continue
            if re.match(r"^\d", tok):
                continue
            leading = False
        out.append(tok)
    return " ".join(out)


def _remove_extended_descriptors(text: str) -> str:
    tokens = text.split()
    kept = [tok for tok in tokens if tok.lower() not in SCRAPER_DESCRIPTORS]
    return " ".join(kept)


def _spacy_head_phrase(text: str) -> str:
    """Use spaCy to pick the head noun phrase from a conjunction-laden string."""

    doc = _nlp()(text)
    chunks = list(doc.noun_chunks)
    if not chunks:
        # Last resort: keep nouns / proper nouns only.
        return " ".join(tok.text for tok in doc if tok.pos_ in {"NOUN", "PROPN"})

    # Pick the LONGEST chunk by token count — multi-word ingredients like
    # "chicken thigh" should beat single tokens like "lemon" from a tail-clause.
    best = max(chunks, key=lambda chunk: sum(1 for _ in chunk))
    words: list[str] = []
    for tok in best:
        lower = tok.text.lower()
        if tok.pos_ in {"DET", "ADP", "CCONJ", "SCONJ", "PART", "PUNCT"}:
            continue
        if lower in SCRAPER_DESCRIPTORS:
            continue
        if lower in QUANTITY_FILLER_TOKENS:
            continue
        if NUMERIC_TOKEN_PATTERN.match(lower):
            continue
        if lower in UNIT_TOKENS:
            continue
        words.append(tok.text)
    return " ".join(words).strip()


def _has_conjunction(text: str) -> bool:
    return any(tok in CONJUNCTION_TOKENS for tok in text.split())


def _rule_clean(raw: str) -> str:
    """The deterministic rule pipeline; produces an intermediate phrase."""

    text = raw.strip().lower()
    text = PARENS_PATTERN.sub(" ", text)
    text = BRACKETS_PATTERN.sub(" ", text)
    text = _strip_compound_descriptors(text)
    text = _strip_trailing_modifier_clauses(text)
    text = _remove_punctuation(text)
    text = _strip_leading_quantity(text)
    text = _strip_leading_fillers(text)
    text = _remove_extended_descriptors(text)
    text = MULTISPACE_PATTERN.sub(" ", text).strip()
    return text


def extract_ingredient(raw: str) -> ExtractedIngredient:
    """Run the full rule pipeline, then conditionally spaCy, then singularize."""

    if not raw or not raw.strip():
        return ExtractedIngredient(raw=raw, clean_phrase="", pre_clean="")

    pre = _rule_clean(raw)
    if not pre:
        return ExtractedIngredient(raw=raw, clean_phrase="", pre_clean="")

    # spaCy is invoked only when rule output still hints at multiple phrases.
    candidate = pre
    if _has_conjunction(pre):
        spacy_phrase = _spacy_head_phrase(pre)
        if spacy_phrase:
            candidate = spacy_phrase

    # Strip any descriptor that survived the spaCy pass (it can re-introduce them
    # by virtue of returning a chunk verbatim).
    candidate = _remove_extended_descriptors(candidate)
    # Drop leading 'or' / 'and' tokens left behind by spaCy chunk borders.
    candidate = _strip_or_alternative(candidate)
    candidate = MULTISPACE_PATTERN.sub(" ", candidate).strip()
    candidate = _singularize_phrase(candidate)
    candidate = MULTISPACE_PATTERN.sub(" ", candidate).strip()
    return ExtractedIngredient(raw=raw, clean_phrase=candidate, pre_clean=pre)


def extract_ingredients(raws: list[str]) -> list[ExtractedIngredient]:
    return [extract_ingredient(r) for r in raws]


__all__ = [
    "EXTRA_DESCRIPTORS",
    "ExtractedIngredient",
    "SCRAPER_DESCRIPTORS",
    "extract_ingredient",
    "extract_ingredients",
]
