"""Kalshi HTTP client wrappers."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib import parse
from urllib import error, request

from .models import Series, SeriesList, SettlementSource, TagsByCategories
from .settings import Settings

LOGGER = logging.getLogger(__name__)


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
            LOGGER.error(
                "Unexpected tags-by-categories payload: expected object at 'tags_by_categories', got=%s",
                self._describe_value(tags),
            )
            raise KalshiClientError(
                "Unexpected response shape from Kalshi API: "
                "missing 'tags_by_categories' object."
            )

        normalized: dict[str, list[str]] = {}
        for category, values in tags.items():
            if isinstance(category, str) and isinstance(values, list):
                normalized[category] = [item for item in values if isinstance(item, str)]

        return TagsByCategories(tags_by_categories=normalized)

    def get_series_list(
        self,
        category: str | None = None,
        tags: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        include_product_metadata: bool = False,
        include_volume: bool = False,
    ) -> SeriesList:
        """Return market series list from Kalshi."""
        params: dict[str, str] = {}
        if category is not None:
            params["category"] = category
        if tags is not None:
            params["tags"] = tags
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)
        if include_product_metadata:
            params["include_product_metadata"] = "true"
        if include_volume:
            params["include_volume"] = "true"

        path = "/series"
        if params:
            path = f"{path}?{parse.urlencode(params)}"

        payload = self._get_json(path)
        series_items = payload.get("series")
        if not isinstance(series_items, list):
            LOGGER.error(
                "Unexpected series-list payload: expected list at 'series', got=%s keys=%s",
                self._describe_value(series_items),
                sorted(payload.keys()),
            )
            raise KalshiClientError(
                "Unexpected response shape from Kalshi API: missing 'series' array."
            )

        parsed_series: list[Series] = []
        for index, raw_series in enumerate(series_items):
            parsed = self._parse_series(raw_series, index)
            if parsed is not None:
                parsed_series.append(parsed)

        cursor = payload.get("cursor")
        if cursor is not None and not isinstance(cursor, str):
            LOGGER.warning(
                "Ignoring unexpected 'cursor' type in series list response: %s",
                self._describe_value(cursor),
            )
            cursor = None

        return SeriesList(series=parsed_series, cursor=cursor)

    def _parse_series(self, raw_series: Any, index: int) -> Series | None:
        if not isinstance(raw_series, dict):
            LOGGER.warning(
                "Skipping series[%s]: expected object, got %s",
                index,
                self._describe_value(raw_series),
            )
            return None

        required_string_fields = (
            "ticker",
            "frequency",
            "title",
            "category",
            "contract_url",
            "contract_terms_url",
            "fee_type",
        )
        string_values: dict[str, str] = {}
        for field_name in required_string_fields:
            value = raw_series.get(field_name)
            if not isinstance(value, str):
                LOGGER.warning(
                    "Skipping series[%s]: expected '%s' as string, got %s",
                    index,
                    field_name,
                    self._describe_value(value),
                )
                return None
            string_values[field_name] = value

        raw_fee_multiplier = raw_series.get("fee_multiplier")
        if isinstance(raw_fee_multiplier, bool) or not isinstance(raw_fee_multiplier, (int, float)):
            LOGGER.warning(
                "Skipping series[%s]: expected 'fee_multiplier' as number, got %s",
                index,
                self._describe_value(raw_fee_multiplier),
            )
            return None

        raw_tags = raw_series.get("tags")
        tags: list[str] | None
        if raw_tags is None:
            tags = None
        elif isinstance(raw_tags, list):
            tags = [tag for tag in raw_tags if isinstance(tag, str)]
            if len(tags) != len(raw_tags):
                LOGGER.warning(
                    "Dropped non-string tag values in series[%s]; before=%s after=%s",
                    index,
                    len(raw_tags),
                    len(tags),
                )
        else:
            # Kalshi occasionally returns null here; treat other unexpected types as absent.
            LOGGER.warning(
                "Unexpected 'tags' type in series[%s]; got %s",
                index,
                self._describe_value(raw_tags),
            )
            tags = None

        settlement_sources = self._parse_settlement_sources(
            raw_series.get("settlement_sources"), index
        )
        if settlement_sources is None:
            return None

        raw_additional_prohibitions = raw_series.get("additional_prohibitions")
        additional_prohibitions: list[str] | None
        if raw_additional_prohibitions is None:
            additional_prohibitions = None
        elif isinstance(raw_additional_prohibitions, list):
            additional_prohibitions = [
                value for value in raw_additional_prohibitions if isinstance(value, str)
            ]
            if len(additional_prohibitions) != len(raw_additional_prohibitions):
                LOGGER.warning(
                    "Dropped non-string additional_prohibitions in series[%s]; before=%s after=%s",
                    index,
                    len(raw_additional_prohibitions),
                    len(additional_prohibitions),
                )
        else:
            LOGGER.warning(
                "Unexpected 'additional_prohibitions' type in series[%s]; got %s",
                index,
                self._describe_value(raw_additional_prohibitions),
            )
            additional_prohibitions = None

        product_metadata = raw_series.get("product_metadata")
        if product_metadata is not None and not isinstance(product_metadata, dict):
            LOGGER.warning(
                "Ignoring unexpected 'product_metadata' type in series[%s]: %s",
                index,
                self._describe_value(product_metadata),
            )
            product_metadata = None

        volume = raw_series.get("volume")
        if isinstance(volume, bool) or (volume is not None and not isinstance(volume, int)):
            LOGGER.warning(
                "Ignoring unexpected 'volume' type in series[%s]: %s",
                index,
                self._describe_value(volume),
            )
            volume = None

        volume_fp = raw_series.get("volume_fp")
        if volume_fp is not None and not isinstance(volume_fp, str):
            LOGGER.warning(
                "Ignoring unexpected 'volume_fp' type in series[%s]: %s",
                index,
                self._describe_value(volume_fp),
            )
            volume_fp = None

        return Series(
            ticker=string_values["ticker"],
            frequency=string_values["frequency"],
            title=string_values["title"],
            category=string_values["category"],
            tags=tags,
            settlement_sources=settlement_sources,
            contract_url=string_values["contract_url"],
            contract_terms_url=string_values["contract_terms_url"],
            fee_type=string_values["fee_type"],
            fee_multiplier=float(raw_fee_multiplier),
            additional_prohibitions=additional_prohibitions,
            product_metadata=product_metadata,
            volume=volume,
            volume_fp=volume_fp,
        )

    def _parse_settlement_sources(
        self, raw_settlement_sources: Any, index: int
    ) -> list[SettlementSource] | None:
        if not isinstance(raw_settlement_sources, list):
            LOGGER.warning(
                "Skipping series[%s]: expected 'settlement_sources' as object array, got %s",
                index,
                self._describe_value(raw_settlement_sources),
            )
            return None

        parsed_sources: list[SettlementSource] = []
        for source_index, raw_source in enumerate(raw_settlement_sources):
            if not isinstance(raw_source, dict):
                LOGGER.warning(
                    "Skipping invalid settlement source in series[%s] at index %s: %s",
                    index,
                    source_index,
                    self._describe_value(raw_source),
                )
                continue

            name = raw_source.get("name")
            url = raw_source.get("url")
            if not isinstance(name, str) or not isinstance(url, str):
                LOGGER.warning(
                    "Skipping invalid settlement source in series[%s] at index %s: name=%s url=%s",
                    index,
                    source_index,
                    self._describe_value(name),
                    self._describe_value(url),
                )
                continue

            parsed_sources.append(SettlementSource(name=name, url=url))

        return parsed_sources

    def _describe_value(self, value: Any) -> str:
        preview = repr(value)
        if len(preview) > 120:
            preview = f"{preview[:117]}..."
        return f"type={type(value).__name__} value={preview}"

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
