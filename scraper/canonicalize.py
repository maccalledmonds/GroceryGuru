"""Canonical lookup + unmatched-report bookkeeping.

The scraper reuses ``pantrypal``'s canonical index so curation flows
straight back into runtime normalization.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pantrypal.app.utils.normalization import (
    _load_canonical_index,
    _normalize_lookup_phrase_for_index,
    normalize_ingredient,
)

from .ingredient_parser import ExtractedIngredient

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CanonicalLookup:
    """Canonical lookup result for a single extracted ingredient."""

    raw: str
    clean_phrase: str
    canonical_id: str | None
    canonical_name: str | None

    @property
    def matched(self) -> bool:
        return self.canonical_id is not None


@dataclass(slots=True)
class UnmatchedReport:
    """Frequency-ranked unmatched candidates with example raw lines."""

    counts: Counter[str] = field(default_factory=Counter)
    examples: dict[str, list[str]] = field(default_factory=dict)

    def record(self, clean_phrase: str, raw: str) -> None:
        if not clean_phrase:
            return
        self.counts[clean_phrase] += 1
        bucket = self.examples.setdefault(clean_phrase, [])
        if len(bucket) < 3 and raw not in bucket:
            bucket.append(raw)

    def write_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["phrase", "count", "examples"])
            for phrase, count in self.counts.most_common():
                ex = " | ".join(self.examples.get(phrase, []))
                writer.writerow([phrase, count, ex])


def canonical_lookup(clean_phrase: str) -> tuple[str | None, str | None]:
    """Return ``(canonical_id, canonical_name)`` for a cleaned ingredient phrase.

    Uses the same lookup index ``pantrypal`` uses at runtime, so any future
    edits to ``canonical_ingredients.json`` apply immediately on re-canonicalize.
    """

    if not clean_phrase:
        return None, None
    index = _load_canonical_index()
    lookup_phrase = _normalize_lookup_phrase_for_index(clean_phrase)
    match = index.by_phrase.get(lookup_phrase)
    if match is not None:
        return match.canonical_id, match.canonical_name

    # Sub-phrase fallback (mirrors normalization.normalize_ingredient).
    tokens = lookup_phrase.split()
    if len(tokens) >= 3:
        for i in range(1, min(len(tokens) - 1, 4)):
            candidate = " ".join(tokens[i:])
            m = index.by_phrase.get(candidate)
            if m:
                return m.canonical_id, m.canonical_name
        for i in range(1, min(len(tokens) - 1, 4)):
            candidate = " ".join(tokens[:-i])
            m = index.by_phrase.get(candidate)
            if m:
                return m.canonical_id, m.canonical_name

    # Final fallback: pantrypal's own normalize_ingredient handles a few extra
    # cleaning steps. Re-running it costs almost nothing and catches edge cases.
    result = normalize_ingredient(clean_phrase)
    return result.canonical_id, result.canonical_name


def canonicalize_extractions(
    extractions: Iterable[ExtractedIngredient],
    report: UnmatchedReport | None = None,
) -> list[CanonicalLookup]:
    """Look up every extracted phrase. Optionally record unmatched ones."""

    out: list[CanonicalLookup] = []
    for ex in extractions:
        cid, cname = canonical_lookup(ex.clean_phrase)
        lookup = CanonicalLookup(
            raw=ex.raw,
            clean_phrase=ex.clean_phrase,
            canonical_id=cid,
            canonical_name=cname,
        )
        if not lookup.matched and report is not None and ex.clean_phrase:
            report.record(ex.clean_phrase, ex.raw)
        out.append(lookup)
    return out
