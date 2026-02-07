"""Kalshi HTTP client wrappers."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from .models import TagsByCategories
from .settings import Settings


class KalshiClientError(RuntimeError):
    """Raised when Kalshi API requests fail."""


class KalshiClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.base_url
        self._timeout_seconds = settings.timeout_seconds

    def get_tags_for_series_categories(self) -> TagsByCategories:
        """Return tags grouped by series categories."""
        payload = self._get_json("/search/tags_by_categories")
        tags = payload.get("tags_by_categories")

        if not isinstance(tags, dict):
            raise KalshiClientError(
                "Unexpected response shape from Kalshi API: "
                "missing 'tags_by_categories' object."
            )

        normalized: dict[str, list[str]] = {}
        for category, values in tags.items():
            if isinstance(category, str) and isinstance(values, list):
                normalized[category] = [item for item in values if isinstance(item, str)]

        return TagsByCategories(tags_by_categories=normalized)

    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        req = request.Request(
            url=url,
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise KalshiClientError(f"Kalshi API HTTP {exc.code} for {url}") from exc
        except error.URLError as exc:
            raise KalshiClientError(f"Kalshi API request failed for {url}: {exc.reason}") from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise KalshiClientError(f"Kalshi API response was not valid JSON for {url}") from exc

        if not isinstance(decoded, dict):
            raise KalshiClientError(f"Kalshi API returned a non-object payload for {url}")

        return decoded
