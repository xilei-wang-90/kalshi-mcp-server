"""Kalshi HTTP client wrappers."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib import parse
from urllib import error, request

from .models import (
    Market,
    MarketsList,
    MveSelectedLeg,
    PriceRange,
    Series,
    SeriesList,
    SettlementSource,
    TagsByCategories,
)
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

    def get_markets(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
        event_ticker: str | None = None,
        series_ticker: str | None = None,
        tickers: str | None = None,
        status: str | None = None,
        mve_filter: str | None = None,
        min_created_ts: int | None = None,
        max_created_ts: int | None = None,
        min_updated_ts: int | None = None,
        min_close_ts: int | None = None,
        max_close_ts: int | None = None,
        min_settled_ts: int | None = None,
        max_settled_ts: int | None = None,
    ) -> MarketsList:
        """Return markets list from Kalshi (GET /markets)."""
        params: dict[str, str] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if series_ticker is not None:
            params["series_ticker"] = series_ticker
        if tickers is not None:
            params["tickers"] = tickers
        if status is not None:
            params["status"] = status
        if mve_filter is not None:
            params["mve_filter"] = mve_filter

        if min_created_ts is not None:
            params["min_created_ts"] = str(min_created_ts)
        if max_created_ts is not None:
            params["max_created_ts"] = str(max_created_ts)
        if min_updated_ts is not None:
            params["min_updated_ts"] = str(min_updated_ts)
        if min_close_ts is not None:
            params["min_close_ts"] = str(min_close_ts)
        if max_close_ts is not None:
            params["max_close_ts"] = str(max_close_ts)
        if min_settled_ts is not None:
            params["min_settled_ts"] = str(min_settled_ts)
        if max_settled_ts is not None:
            params["max_settled_ts"] = str(max_settled_ts)

        path = "/markets"
        if params:
            path = f"{path}?{parse.urlencode(params)}"

        payload = self._get_json(path)
        market_items = payload.get("markets")
        if not isinstance(market_items, list):
            LOGGER.error(
                "Unexpected markets payload: expected list at 'markets', got=%s keys=%s",
                self._describe_value(market_items),
                sorted(payload.keys()),
            )
            raise KalshiClientError(
                "Unexpected response shape from Kalshi API: missing 'markets' array."
            )

        parsed_markets: list[Market] = []
        for index, raw_market in enumerate(market_items):
            parsed = self._parse_market(raw_market, index)
            if parsed is not None:
                parsed_markets.append(parsed)

        next_cursor = payload.get("cursor")
        if next_cursor is not None and not isinstance(next_cursor, str):
            LOGGER.warning(
                "Ignoring unexpected 'cursor' type in markets response: %s",
                self._describe_value(next_cursor),
            )
            next_cursor = None

        return MarketsList(markets=parsed_markets, cursor=next_cursor)

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

    def _parse_market(self, raw_market: Any, index: int) -> Market | None:
        if not isinstance(raw_market, dict):
            LOGGER.warning(
                "Skipping markets[%s]: expected object, got %s",
                index,
                self._describe_value(raw_market),
            )
            return None

        required_string_fields = (
            "ticker",
            "event_ticker",
            "market_type",
            "title",
            "subtitle",
            "status",
        )
        string_values: dict[str, str] = {}
        for field_name in required_string_fields:
            value = raw_market.get(field_name)
            if not isinstance(value, str):
                LOGGER.warning(
                    "Skipping markets[%s]: expected '%s' as string, got %s",
                    index,
                    field_name,
                    self._describe_value(value),
                )
                return None
            string_values[field_name] = value

        price_ranges = self._parse_price_ranges(raw_market.get("price_ranges"), index)
        mve_selected_legs = self._parse_mve_selected_legs(
            raw_market.get("mve_selected_legs"), index
        )

        custom_strike = raw_market.get("custom_strike")
        if custom_strike is not None and not isinstance(custom_strike, dict):
            LOGGER.warning(
                "Ignoring unexpected 'custom_strike' type in markets[%s]: %s",
                index,
                self._describe_value(custom_strike),
            )
            custom_strike = None
        if isinstance(custom_strike, dict):
            # Ensure string keys; values remain arbitrary JSON.
            custom_strike = {k: v for k, v in custom_strike.items() if isinstance(k, str)}

        tick_size = raw_market.get("tick_size")
        if isinstance(tick_size, bool) or (tick_size is not None and not isinstance(tick_size, int)):
            LOGGER.warning(
                "Ignoring unexpected 'tick_size' type in markets[%s]: %s",
                index,
                self._describe_value(tick_size),
            )
            tick_size = None

        return Market(
            ticker=string_values["ticker"],
            event_ticker=string_values["event_ticker"],
            market_type=string_values["market_type"],
            title=string_values["title"],
            subtitle=string_values["subtitle"],
            status=string_values["status"],
            series_ticker=self._optional_str(raw_market, "series_ticker", index=index),
            yes_sub_title=self._optional_str(raw_market, "yes_sub_title", index=index),
            no_sub_title=self._optional_str(raw_market, "no_sub_title", index=index),
            created_time=self._optional_str(raw_market, "created_time", index=index),
            updated_time=self._optional_str(raw_market, "updated_time", index=index),
            open_time=self._optional_str(raw_market, "open_time", index=index),
            close_time=self._optional_str(raw_market, "close_time", index=index),
            expiration_time=self._optional_str(raw_market, "expiration_time", index=index),
            latest_expiration_time=self._optional_str(
                raw_market, "latest_expiration_time", index=index
            ),
            response_price_units=self._optional_str(
                raw_market, "response_price_units", index=index
            ),
            settlement_timer_seconds=self._optional_int(
                raw_market, "settlement_timer_seconds", index=index
            ),
            yes_bid=self._optional_int(raw_market, "yes_bid", index=index),
            yes_ask=self._optional_int(raw_market, "yes_ask", index=index),
            no_bid=self._optional_int(raw_market, "no_bid", index=index),
            no_ask=self._optional_int(raw_market, "no_ask", index=index),
            last_price=self._optional_int(raw_market, "last_price", index=index),
            volume=self._optional_int(raw_market, "volume", index=index),
            volume_24h=self._optional_int(raw_market, "volume_24h", index=index),
            open_interest=self._optional_int(raw_market, "open_interest", index=index),
            notional_value=self._optional_int(raw_market, "notional_value", index=index),
            previous_yes_bid=self._optional_int(raw_market, "previous_yes_bid", index=index),
            previous_yes_ask=self._optional_int(raw_market, "previous_yes_ask", index=index),
            previous_price=self._optional_int(raw_market, "previous_price", index=index),
            liquidity=self._optional_int(raw_market, "liquidity", index=index),
            tick_size=tick_size,
            settlement_value=self._optional_int(raw_market, "settlement_value", index=index),
            floor_strike=self._optional_int(raw_market, "floor_strike", index=index),
            cap_strike=self._optional_int(raw_market, "cap_strike", index=index),
            yes_bid_dollars=self._optional_str(raw_market, "yes_bid_dollars", index=index),
            yes_ask_dollars=self._optional_str(raw_market, "yes_ask_dollars", index=index),
            no_bid_dollars=self._optional_str(raw_market, "no_bid_dollars", index=index),
            no_ask_dollars=self._optional_str(raw_market, "no_ask_dollars", index=index),
            last_price_dollars=self._optional_str(raw_market, "last_price_dollars", index=index),
            volume_fp=self._optional_str(raw_market, "volume_fp", index=index),
            volume_24h_fp=self._optional_str(raw_market, "volume_24h_fp", index=index),
            open_interest_fp=self._optional_str(raw_market, "open_interest_fp", index=index),
            notional_value_dollars=self._optional_str(
                raw_market, "notional_value_dollars", index=index
            ),
            previous_yes_bid_dollars=self._optional_str(
                raw_market, "previous_yes_bid_dollars", index=index
            ),
            previous_yes_ask_dollars=self._optional_str(
                raw_market, "previous_yes_ask_dollars", index=index
            ),
            previous_price_dollars=self._optional_str(
                raw_market, "previous_price_dollars", index=index
            ),
            liquidity_dollars=self._optional_str(raw_market, "liquidity_dollars", index=index),
            settlement_value_dollars=self._optional_str(
                raw_market, "settlement_value_dollars", index=index
            ),
            result=self._optional_str(raw_market, "result", index=index),
            can_close_early=self._optional_bool(raw_market, "can_close_early", index=index),
            expiration_value=self._optional_str(raw_market, "expiration_value", index=index),
            rules_primary=self._optional_str(raw_market, "rules_primary", index=index),
            rules_secondary=self._optional_str(raw_market, "rules_secondary", index=index),
            price_level_structure=self._optional_str(
                raw_market, "price_level_structure", index=index
            ),
            price_ranges=price_ranges,
            expected_expiration_time=self._optional_str(
                raw_market, "expected_expiration_time", index=index
            ),
            settlement_ts=self._optional_str(raw_market, "settlement_ts", index=index),
            fee_waiver_expiration_time=self._optional_str(
                raw_market, "fee_waiver_expiration_time", index=index
            ),
            early_close_condition=self._optional_str(
                raw_market, "early_close_condition", index=index
            ),
            strike_type=self._optional_str(raw_market, "strike_type", index=index),
            functional_strike=self._optional_str(raw_market, "functional_strike", index=index),
            custom_strike=custom_strike,
            mve_collection_ticker=self._optional_str(
                raw_market, "mve_collection_ticker", index=index
            ),
            mve_selected_legs=mve_selected_legs,
            primary_participant_key=self._optional_str(
                raw_market, "primary_participant_key", index=index
            ),
            is_provisional=self._optional_bool(raw_market, "is_provisional", index=index),
        )

    def _optional_str(self, raw: dict[str, Any], key: str, *, index: int) -> str | None:
        value = raw.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            return value
        LOGGER.warning(
            "Ignoring unexpected '%s' type in markets[%s]: %s",
            key,
            index,
            self._describe_value(value),
        )
        return None

    def _optional_int(self, raw: dict[str, Any], key: str, *, index: int) -> int | None:
        value = raw.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            LOGGER.warning(
                "Ignoring unexpected '%s' type in markets[%s]: %s",
                key,
                index,
                self._describe_value(value),
            )
            return None
        return value

    def _optional_bool(self, raw: dict[str, Any], key: str, *, index: int) -> bool | None:
        value = raw.get(key)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        LOGGER.warning(
            "Ignoring unexpected '%s' type in markets[%s]: %s",
            key,
            index,
            self._describe_value(value),
        )
        return None

    def _parse_price_ranges(self, raw_value: Any, index: int) -> list[PriceRange] | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, list):
            LOGGER.warning(
                "Ignoring unexpected 'price_ranges' type in markets[%s]: %s",
                index,
                self._describe_value(raw_value),
            )
            return None
        parsed: list[PriceRange] = []
        for range_index, item in enumerate(raw_value):
            if not isinstance(item, dict):
                LOGGER.warning(
                    "Skipping invalid price_ranges item in markets[%s] at index %s: %s",
                    index,
                    range_index,
                    self._describe_value(item),
                )
                continue
            start = item.get("start")
            end = item.get("end")
            step = item.get("step")
            if not isinstance(start, str) or not isinstance(end, str) or not isinstance(step, str):
                LOGGER.warning(
                    "Skipping invalid price_ranges item in markets[%s] at index %s: %s",
                    index,
                    range_index,
                    self._describe_value(item),
                )
                continue
            parsed.append(PriceRange(start=start, end=end, step=step))
        return parsed

    def _parse_mve_selected_legs(
        self, raw_value: Any, index: int
    ) -> list[MveSelectedLeg] | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, list):
            LOGGER.warning(
                "Ignoring unexpected 'mve_selected_legs' type in markets[%s]: %s",
                index,
                self._describe_value(raw_value),
            )
            return None
        parsed: list[MveSelectedLeg] = []
        for leg_index, item in enumerate(raw_value):
            if not isinstance(item, dict):
                LOGGER.warning(
                    "Skipping invalid mve_selected_legs item in markets[%s] at index %s: %s",
                    index,
                    leg_index,
                    self._describe_value(item),
                )
                continue
            event_ticker = item.get("event_ticker")
            market_ticker = item.get("market_ticker")
            side = item.get("side")
            if (
                not isinstance(event_ticker, str)
                or not isinstance(market_ticker, str)
                or not isinstance(side, str)
            ):
                LOGGER.warning(
                    "Skipping invalid mve_selected_legs item in markets[%s] at index %s: %s",
                    index,
                    leg_index,
                    self._describe_value(item),
                )
                continue
            yes_settlement_value_dollars = item.get("yes_settlement_value_dollars")
            if yes_settlement_value_dollars is not None and not isinstance(
                yes_settlement_value_dollars, str
            ):
                LOGGER.warning(
                    "Ignoring unexpected yes_settlement_value_dollars type in markets[%s] at index %s: %s",
                    index,
                    leg_index,
                    self._describe_value(yes_settlement_value_dollars),
                )
                yes_settlement_value_dollars = None
            parsed.append(
                MveSelectedLeg(
                    event_ticker=event_ticker,
                    market_ticker=market_ticker,
                    side=side,
                    yes_settlement_value_dollars=yes_settlement_value_dollars,
                )
            )
        return parsed

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
