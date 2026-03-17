"""Groq API client wrapper for grounded recipe ranking."""
# pyright: reportMissingImports=false

from __future__ import annotations

import json
import logging
from typing import Any

try:  # pragma: no cover - exercised in environments with Groq installed
    from groq import Groq  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Groq = None

LOGGER = logging.getLogger(__name__)


class GroqClientError(RuntimeError):
    """Base class for Groq client errors."""


class GroqTimeoutError(GroqClientError):
    """Raised when Groq request exceeds configured timeout."""


class GroqClient:
    """Thin wrapper around Groq chat completions with JSON output parsing."""

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        if Groq is None:
            raise GroqClientError("groq package is not installed; install groq to enable AI recommendations")
        if not api_key.strip():
            raise GroqClientError("GROQ_API_KEY is missing or empty")

        self.model = model
        self.timeout_seconds = timeout_seconds
        try:
            self._client = Groq(api_key=api_key)
        except Exception as exc:
            raise GroqClientError(
                "Failed to initialize Groq client. "
                "This is often caused by an incompatible httpx version; pin httpx==0.27.2. "
                f"Original error: {exc}"
            ) from exc

    def generate_rankings(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = self._create_completion(messages)
        except TimeoutError as exc:
            raise GroqTimeoutError("Groq request timed out") from exc
        except Exception as exc:
            raise GroqClientError(f"Groq request failed: {exc}") from exc

        content = completion.choices[0].message.content if completion.choices else ""
        if not content:
            raise GroqClientError("Groq returned empty content")

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            LOGGER.error("Invalid JSON from Groq model: %s", content)
            raise GroqClientError("Groq returned non-JSON content") from exc

    def _create_completion(self, messages: list[dict[str, str]]) -> Any:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": 900,
        }

        try:
            return self._client.chat.completions.create(**kwargs, timeout=self.timeout_seconds)
        except TypeError:
            return self._client.chat.completions.create(**kwargs)
