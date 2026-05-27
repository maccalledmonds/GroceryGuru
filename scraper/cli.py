"""Scraper CLI.

Examples:

    PYTHONPATH=. python -m scraper.cli discover --limit 50
    PYTHONPATH=. python -m scraper.cli scrape --urls scraper/data/urls.txt
    PYTHONPATH=. python -m scraper.cli recanonicalize
    PYTHONPATH=. python -m scraper.cli report --top 30
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path

from .config import (
    RECIPES_OUTPUT_PATH,
    UNMATCHED_REPORT_PATH,
    URLS_OUTPUT_PATH,
)
from .discover import discover_recipe_urls
from .fetcher import Fetcher
from .pipeline import recanonicalize_existing, scrape_urls

LOGGER = logging.getLogger("scraper")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )


async def _cmd_discover(args: argparse.Namespace) -> int:
    URLS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with Fetcher() as fetcher:
        urls = await discover_recipe_urls(fetcher, limit=args.limit)
    out_path = Path(args.out or URLS_OUTPUT_PATH)
    with out_path.open("w", encoding="utf-8") as handle:
        for entry in urls:
            handle.write(entry.url + "\n")
    print(f"Wrote {len(urls)} URLs to {out_path}", file=sys.stderr)
    return 0


async def _cmd_scrape(args: argparse.Namespace) -> int:
    urls_path = Path(args.urls)
    if not urls_path.exists():
        print(f"URLs file not found: {urls_path}", file=sys.stderr)
        return 2
    urls = [line.strip() for line in urls_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        urls = urls[: args.limit]
    stats = await scrape_urls(
        urls,
        output_path=Path(args.output) if args.output else RECIPES_OUTPUT_PATH,
        unmatched_report_path=Path(args.unmatched) if args.unmatched else UNMATCHED_REPORT_PATH,
        use_cache=not args.no_cache,
    )
    print(json.dumps(stats, indent=2))
    return 0


def _cmd_recanonicalize(args: argparse.Namespace) -> int:
    stats = recanonicalize_existing(
        output_path=Path(args.output) if args.output else RECIPES_OUTPUT_PATH,
        unmatched_report_path=Path(args.unmatched) if args.unmatched else UNMATCHED_REPORT_PATH,
    )
    print(json.dumps(stats, indent=2))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.path) if args.path else UNMATCHED_REPORT_PATH
    if not path.exists():
        print(f"Report not found: {path}", file=sys.stderr)
        return 2
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    header, rows = rows[0], rows[1:]
    rows.sort(key=lambda r: int(r[1]), reverse=True)
    rows = rows[: args.top]
    width = max(len(row[0]) for row in rows) if rows else 0
    print(f"{header[0]:<{width}}  {header[1]:>5}  {header[2]}")
    print("-" * (width + 30))
    for row in rows:
        print(f"{row[0]:<{width}}  {row[1]:>5}  {row[2][:80]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraper", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_disc = sub.add_parser("discover", help="Walk the sitemap for recipe URLs")
    p_disc.add_argument("--limit", type=int, default=None)
    p_disc.add_argument("--out", default=None)

    p_scrape = sub.add_parser("scrape", help="Scrape recipes from a URL list")
    p_scrape.add_argument("--urls", required=True)
    p_scrape.add_argument("--limit", type=int, default=None)
    p_scrape.add_argument("--output", default=None)
    p_scrape.add_argument("--unmatched", default=None)
    p_scrape.add_argument("--no-cache", action="store_true")

    p_recan = sub.add_parser("recanonicalize", help="Re-run canonical lookup on saved records")
    p_recan.add_argument("--output", default=None)
    p_recan.add_argument("--unmatched", default=None)

    p_report = sub.add_parser("report", help="Print the unmatched candidates report")
    p_report.add_argument("--path", default=None)
    p_report.add_argument("--top", type=int, default=30)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    if args.command == "discover":
        return asyncio.run(_cmd_discover(args))
    if args.command == "scrape":
        return asyncio.run(_cmd_scrape(args))
    if args.command == "recanonicalize":
        return _cmd_recanonicalize(args)
    if args.command == "report":
        return _cmd_report(args)
    raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
