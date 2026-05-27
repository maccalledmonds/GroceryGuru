"""Polite HTTP fetcher with on-disk cache and robots.txt enforcement."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import (
    HTTP_CACHE_DIR,
    MAX_CONCURRENCY,
    MAX_DELAY_SECONDS,
    MAX_RETRIES,
    MIN_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Container for a single fetch result."""

    url: str
    status_code: int
    body: str
    from_cache: bool


class RobotsCache:
    """Per-origin robots.txt cache."""

    def __init__(self) -> None:
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._lock = asyncio.Lock()

    async def allowed(self, client: httpx.AsyncClient, url: str) -> bool:
        origin = _origin_of(url)
        async with self._lock:
            parser = self._parsers.get(origin)
            if parser is None:
                parser = await self._load_parser(client, origin)
                self._parsers[origin] = parser
        return parser.can_fetch(USER_AGENT, url)

    async def _load_parser(
        self, client: httpx.AsyncClient, origin: str
    ) -> urllib.robotparser.RobotFileParser:
        parser = urllib.robotparser.RobotFileParser()
        robots_url = f"{origin}/robots.txt"
        try:
            response = await client.get(robots_url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                # No usable robots.txt: default-allow but log it.
                LOGGER.warning(
                    "robots.txt for %s returned status %s; defaulting to allow",
                    origin,
                    response.status_code,
                )
                parser.parse([])
        except httpx.HTTPError as exc:
            LOGGER.warning("Failed to fetch robots.txt for %s: %s", origin, exc)
            parser.parse([])
        return parser


def _origin_of(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _cache_path(url: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return HTTP_CACHE_DIR / digest[:2] / f"{digest}.html"


class Fetcher:
    """Async fetcher: caches to disk, respects robots.txt, jitters requests."""

    def __init__(
        self,
        *,
        cache_dir: Path = HTTP_CACHE_DIR,
        max_concurrency: int = MAX_CONCURRENCY,
        min_delay: float = MIN_DELAY_SECONDS,
        max_delay: float = MAX_DELAY_SECONDS,
    ) -> None:
        self._cache_dir = cache_dir
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._robots = RobotsCache()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "Fetcher":
        self._client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str, *, use_cache: bool = True) -> Optional[FetchResult]:
        """Fetch a URL, honoring robots.txt and on-disk cache."""

        cached_path = _cache_path(url)
        if use_cache and cached_path.exists():
            body = cached_path.read_text(encoding="utf-8")
            return FetchResult(url=url, status_code=200, body=body, from_cache=True)

        client = self._client
        if client is None:
            raise RuntimeError("Fetcher must be used as an async context manager")

        if not await self._robots.allowed(client, url):
            LOGGER.info("robots.txt disallows %s; skipping", url)
            return None

        async with self._semaphore:
            await asyncio.sleep(random.uniform(self._min_delay, self._max_delay))
            response = await self._do_get(client, url)
            if response.status_code == 200:
                body = response.text
                cached_path.parent.mkdir(parents=True, exist_ok=True)
                cached_path.write_text(body, encoding="utf-8")
                return FetchResult(url=url, status_code=200, body=body, from_cache=False)
            LOGGER.info("fetch %s returned status %s", url, response.status_code)
            return FetchResult(url=url, status_code=response.status_code, body="", from_cache=False)

    async def _do_get(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)
            ),
            reraise=True,
        ):
            with attempt:
                return await client.get(url)
        raise RuntimeError("unreachable")  # pragma: no cover
