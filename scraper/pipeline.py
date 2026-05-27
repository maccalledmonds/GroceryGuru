"""End-to-end scrape pipeline: URL -> ParsedRecipe -> clean Recipe record."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .canonicalize import UnmatchedReport, canonicalize_extractions
from .config import (
    RECIPES_OUTPUT_PATH,
    UNMATCHED_REPORT_PATH,
)
from .fetcher import Fetcher
from .ingredient_parser import extract_ingredient
from .parse import ParsedRecipe, parse_recipe_html

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RecipeRecord:
    """The on-disk record shape. Compatible with the existing pantrypal Recipe."""

    id: int
    title: str
    source_url: str
    recipe_category: list[str]
    ingredients: list[str]
    """Raw recipe ingredient sentences as scraped from Epicurious."""

    ingredients_normalized: list[str]
    """Canonical (or cleaned) phrases, ready for pantrypal database search."""

    ingredients_canonical: list[dict]
    """Audit array of ``{raw, clean_phrase, canonical_id, canonical_name, matched}``."""

    instructions: str
    diet_tags: list[str] = field(default_factory=list)
    nutrition: dict = field(default_factory=dict)
    servings: int | None = None


def _build_record(
    *, recipe_id: int, parsed: ParsedRecipe, report: UnmatchedReport | None
) -> RecipeRecord:
    extractions = [extract_ingredient(line) for line in parsed.ingredients_raw]
    canonicals = canonicalize_extractions(extractions, report=report)

    normalized: list[str] = []
    seen: set[str] = set()
    audit: list[dict] = []
    for ex, cn in zip(extractions, canonicals):
        value = cn.canonical_name or ex.clean_phrase
        audit.append(
            {
                "raw": ex.raw,
                "clean_phrase": ex.clean_phrase,
                "canonical_id": cn.canonical_id,
                "canonical_name": cn.canonical_name,
                "matched": cn.matched,
            }
        )
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)

    return RecipeRecord(
        id=recipe_id,
        title=parsed.title,
        source_url=parsed.source_url,
        recipe_category=parsed.recipe_category,
        ingredients=list(parsed.ingredients_raw),
        ingredients_normalized=normalized,
        ingredients_canonical=audit,
        instructions=parsed.instructions,
        diet_tags=[],
        nutrition=dict(parsed.nutrition),
        servings=parsed.servings,
    )


def _read_existing_ids(path: Path) -> tuple[set[str], int]:
    """Return (already-seen source URLs, max-id-seen) for resume-safety."""

    if not path.exists():
        return set(), 0
    seen: set[str] = set()
    max_id = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = rec.get("source_url")
            if isinstance(url, str):
                seen.add(url)
            try:
                rec_id = int(rec.get("id", 0))
            except (TypeError, ValueError):
                rec_id = 0
            max_id = max(max_id, rec_id)
    return seen, max_id


async def scrape_urls(
    urls: Iterable[str],
    *,
    output_path: Path = RECIPES_OUTPUT_PATH,
    unmatched_report_path: Path = UNMATCHED_REPORT_PATH,
    use_cache: bool = True,
    write_report: bool = True,
) -> dict:
    """Scrape a list of recipe URLs and append clean records to ``output_path``.

    Returns summary statistics.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    already, next_id_base = _read_existing_ids(output_path)
    next_id = next_id_base + 1

    report = UnmatchedReport()
    stats = {
        "fetched": 0,
        "from_cache": 0,
        "no_recipe_block": 0,
        "rejected_non_meal": 0,
        "written": 0,
        "skipped_already_scraped": 0,
        "total_ingredient_lines": 0,
        "matched_ingredient_lines": 0,
    }

    async with Fetcher() as fetcher:
        with output_path.open("a", encoding="utf-8") as handle:
            for url in urls:
                if url in already:
                    stats["skipped_already_scraped"] += 1
                    continue
                fetched = await fetcher.fetch(url, use_cache=use_cache)
                if fetched is None or fetched.status_code != 200:
                    continue
                stats["fetched"] += 1
                if fetched.from_cache:
                    stats["from_cache"] += 1
                parsed = parse_recipe_html(fetched.body, source_url=url)
                if parsed is None:
                    stats["no_recipe_block"] += 1
                    continue
                if not parsed.is_meal_candidate:
                    stats["rejected_non_meal"] += 1
                    LOGGER.info("Skipping non-meal %s: %s", url, parsed.rejection_reason)
                    continue
                record = _build_record(
                    recipe_id=next_id, parsed=parsed, report=report
                )
                next_id += 1
                stats["total_ingredient_lines"] += len(record.ingredients_canonical)
                stats["matched_ingredient_lines"] += sum(
                    1 for item in record.ingredients_canonical if item["matched"]
                )
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
                handle.flush()
                stats["written"] += 1

    if write_report:
        report.write_csv(unmatched_report_path)

    if stats["total_ingredient_lines"]:
        ratio = stats["matched_ingredient_lines"] / stats["total_ingredient_lines"]
        stats["match_rate"] = round(ratio, 4)
    else:
        stats["match_rate"] = 0.0
    return stats


def recanonicalize_existing(
    *,
    output_path: Path = RECIPES_OUTPUT_PATH,
    unmatched_report_path: Path = UNMATCHED_REPORT_PATH,
) -> dict:
    """Re-run canonical lookup on already-scraped records (no network).

    Use this after editing ``canonical_ingredients.json`` to upgrade
    previously-unmatched ingredients in place.
    """

    if not output_path.exists():
        return {"updated": 0, "match_rate": 0.0}

    records = []
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    report = UnmatchedReport()
    total = 0
    matched = 0
    for rec in records:
        new_audit: list[dict] = []
        new_normalized: list[str] = []
        seen: set[str] = set()
        for item in rec.get("ingredients_canonical", []):
            clean = item.get("clean_phrase", "")
            raw = item.get("raw", "")
            # Re-lookup using current canonical index.
            from .canonicalize import canonical_lookup

            cid, cname = canonical_lookup(clean)
            entry = dict(item)
            entry["canonical_id"] = cid
            entry["canonical_name"] = cname
            entry["matched"] = cid is not None
            new_audit.append(entry)
            total += 1
            if cid is not None:
                matched += 1
            else:
                report.record(clean, raw)
            value = cname or clean
            if value and value not in seen:
                seen.add(value)
                new_normalized.append(value)
        rec["ingredients_canonical"] = new_audit
        rec["ingredients_normalized"] = new_normalized

    # Atomically rewrite the file.
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp_path.replace(output_path)

    report.write_csv(unmatched_report_path)
    match_rate = round(matched / total, 4) if total else 0.0
    return {
        "updated": len(records),
        "total_ingredient_lines": total,
        "matched_ingredient_lines": matched,
        "match_rate": match_rate,
    }
