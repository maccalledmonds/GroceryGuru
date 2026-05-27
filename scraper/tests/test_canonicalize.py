"""Tests for canonical lookup and the unmatched-report bookkeeping."""

from __future__ import annotations

from pathlib import Path

from scraper.canonicalize import (
    UnmatchedReport,
    canonical_lookup,
    canonicalize_extractions,
)
from scraper.ingredient_parser import ExtractedIngredient, extract_ingredient


def test_canonical_lookup_maps_known_aliases() -> None:
    # "chicken thigh" should canonicalize to "chicken" via alias.
    cid, cname = canonical_lookup("chicken thigh")
    assert cid is not None
    assert cname == "chicken"


def test_canonical_lookup_returns_none_for_unknown_phrase() -> None:
    cid, cname = canonical_lookup("dragon fruit pulp")
    assert cid is None
    assert cname is None


def test_canonicalize_extractions_records_unmatched(tmp_path: Path) -> None:
    extractions = [
        extract_ingredient("2 medium onions, chopped"),
        extract_ingredient("1 cup dragon fruit pulp"),
        extract_ingredient("1 cup dragon fruit pulp"),
    ]
    report = UnmatchedReport()
    results = canonicalize_extractions(extractions, report=report)
    # First should be matched (onion).
    assert results[0].matched is True
    assert results[0].canonical_name == "onion"
    # Dragon fruit is not in the canonical list — should be unmatched and recorded twice.
    assert results[1].matched is False
    assert results[2].matched is False
    assert report.counts["dragon fruit pulp"] == 2
    # CSV writer should produce a readable file.
    csv_path = tmp_path / "unmatched.csv"
    report.write_csv(csv_path)
    body = csv_path.read_text(encoding="utf-8")
    assert "dragon fruit pulp" in body
    assert "phrase,count,examples" in body


def test_extracted_ingredient_with_empty_phrase_is_skipped_in_report() -> None:
    report = UnmatchedReport()
    canonicalize_extractions(
        [ExtractedIngredient(raw="", clean_phrase="", pre_clean="")],
        report=report,
    )
    assert sum(report.counts.values()) == 0
