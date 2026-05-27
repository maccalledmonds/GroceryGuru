"""Discover Epicurious recipe URLs from the sitemap, filtered to meal/snack scope."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable, Iterator

from bs4 import BeautifulSoup

from .config import (
    EPICURIOUS_BASE,
    EPICURIOUS_SITEMAP_INDEX,
    NON_MEAL_TOKENS,
)
from .fetcher import Fetcher

LOGGER = logging.getLogger(__name__)

RECIPE_URL_PATTERN = re.compile(r"/recipes/food/views/", re.IGNORECASE)
SLUG_TOKEN_PATTERN = re.compile(r"[a-z]+")


@dataclass(frozen=True, slots=True)
class DiscoveredUrl:
    """A candidate recipe URL plus the reason we kept or skipped it."""

    url: str
    slug_tokens: tuple[str, ...]
    is_meal_candidate: bool
    rejection_reason: str | None


def _slug_tokens(url: str) -> tuple[str, ...]:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return tuple(SLUG_TOKEN_PATTERN.findall(slug.lower()))


def title_passes_meal_filter(tokens: Iterable[str]) -> tuple[bool, str | None]:
    """Cheap pre-check based on URL slug tokens."""

    token_set = {tok.lower() for tok in tokens if tok}
    rejected = token_set.intersection(NON_MEAL_TOKENS)
    if rejected:
        return False, f"slug contains non-meal tokens: {sorted(rejected)}"
    return True, None


def filter_recipe_url(url: str) -> DiscoveredUrl:
    """Decide whether a sitemap URL is a meal/snack recipe candidate."""

    tokens = _slug_tokens(url)
    if not RECIPE_URL_PATTERN.search(url):
        return DiscoveredUrl(
            url=url,
            slug_tokens=tokens,
            is_meal_candidate=False,
            rejection_reason="not a recipe URL",
        )
    passes, reason = title_passes_meal_filter(tokens)
    return DiscoveredUrl(
        url=url,
        slug_tokens=tokens,
        is_meal_candidate=passes,
        rejection_reason=reason,
    )


def iter_sitemap_urls(xml: str) -> Iterator[str]:
    """Yield <loc> values from a sitemap or sitemap-index XML document."""

    soup = BeautifulSoup(xml, "xml")
    for loc in soup.find_all("loc"):
        text = (loc.text or "").strip()
        if text:
            yield text


async def discover_recipe_urls(
    fetcher: Fetcher,
    *,
    limit: int | None = None,
    sitemap_index_url: str = EPICURIOUS_SITEMAP_INDEX,
) -> list[DiscoveredUrl]:
    """Walk the sitemap index and return meal-candidate recipe URLs."""

    LOGGER.info("Discovering recipe URLs from %s", sitemap_index_url)
    index_result = await fetcher.fetch(sitemap_index_url)
    if index_result is None or index_result.status_code != 200:
        LOGGER.error("Could not fetch sitemap index")
        return []

    sub_sitemaps = [
        url
        for url in iter_sitemap_urls(index_result.body)
        if url.lower().endswith(".xml")
    ]
    if not sub_sitemaps:
        # The sitemap index might itself list URLs directly.
        sub_sitemaps = [sitemap_index_url]

    discovered: list[DiscoveredUrl] = []
    seen_urls: set[str] = set()
    for sub in sub_sitemaps:
        if limit is not None and sum(d.is_meal_candidate for d in discovered) >= limit:
            break
        sub_url = sub if sub.startswith("http") else f"{EPICURIOUS_BASE}{sub}"
        if sub_url == sitemap_index_url and sub_sitemaps != [sitemap_index_url]:
            continue
        sub_result = await fetcher.fetch(sub_url)
        if sub_result is None or sub_result.status_code != 200:
            continue
        for url in iter_sitemap_urls(sub_result.body):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            decision = filter_recipe_url(url)
            if decision.is_meal_candidate:
                discovered.append(decision)
            if (
                limit is not None
                and sum(d.is_meal_candidate for d in discovered) >= limit
            ):
                break

    LOGGER.info("Discovered %d meal-candidate URLs", len(discovered))
    return discovered
