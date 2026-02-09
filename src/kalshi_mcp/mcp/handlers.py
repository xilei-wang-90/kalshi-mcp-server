"""MCP tool handlers."""

from __future__ import annotations

from typing import Any, Callable

from ..models import (
    Market,
    MarketsList,
    MveSelectedLeg,
    PriceRange,
    Series,
    SeriesList,
    SettlementSource,
    TagsByCategories,
)
from ..services import MetadataService

ToolHandler = Callable[[dict[str, Any] | None], dict[str, Any]]


def _require_arguments(arguments: dict[str, Any] | None, tool_name: str) -> dict[str, Any]:
    if arguments is None:
        raise ValueError(f"Missing arguments for {tool_name}.")
    return arguments


def _parse_required_str(
    arguments: dict[str, Any],
    key: str,
    *,
    type_error: str,
    empty_error: str | None = None,
) -> str:
    value = arguments.get(key)
    if not isinstance(value, str):
        raise ValueError(type_error)
    normalized = value.strip()
    if empty_error is not None and not normalized:
        raise ValueError(empty_error)
    return normalized


def _parse_optional_str(
    arguments: dict[str, Any],
    key: str,
    *,
    type_error: str,
    empty_error: str,
) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(type_error)
    normalized = value.strip()
    if not normalized:
        raise ValueError(empty_error)
    return normalized


def _parse_optional_int(
    arguments: dict[str, Any],
    key: str,
    *,
    type_error: str,
    range_error: str,
    min_value: int,
    max_value: int,
) -> int | None:
    value = arguments.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(type_error)
    if value < min_value or value > max_value:
        raise ValueError(range_error)
    return value


def _parse_bool(arguments: dict[str, Any], key: str, default: bool, *, type_error: str) -> bool:
    value = arguments.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(type_error)
    return value


def build_tool_handlers(metadata_service: MetadataService) -> dict[str, ToolHandler]:
    return {
        "get_tags_for_series_categories": lambda arguments: (
            handle_get_tags_for_series_categories(metadata_service, arguments)
        ),
        "get_categories": lambda arguments: (
            handle_get_categories(metadata_service, arguments)
        ),
        "get_tags_for_series_category": lambda arguments: (
            handle_get_tags_for_series_category(metadata_service, arguments)
        ),
        "get_series_list": lambda arguments: (
            handle_get_series_list(metadata_service, arguments)
        ),
        "get_markets": lambda arguments: (
            handle_get_markets(metadata_service, arguments)
        ),
        "get_open_markets_for_series": lambda arguments: (
            handle_get_open_markets_for_series(metadata_service, arguments)
        ),
        "get_open_market_titles_for_series": lambda arguments: (
            handle_get_open_market_titles_for_series(metadata_service, arguments)
        ),
        "get_series_tickers_for_category": lambda arguments: (
            handle_get_series_tickers_for_category(metadata_service, arguments)
        ),
    }


def handle_get_tags_for_series_categories(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    if arguments:
        raise ValueError("get_tags_for_series_categories does not accept arguments.")

    tags = metadata_service.get_tags_for_series_categories()
    return _serialize_tags(tags)


def _serialize_tags(tags: TagsByCategories) -> dict[str, Any]:
    return {"tags_by_categories": tags.tags_by_categories}


def handle_get_categories(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    if arguments:
        raise ValueError("get_categories does not accept arguments.")

    categories = metadata_service.get_categories()
    return {"categories": categories}


def handle_get_tags_for_series_category(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    args = _require_arguments(arguments, "get_tags_for_series_category")
    category = _parse_required_str(
        args,
        "category",
        type_error="category must be a string.",
        empty_error="category must be a non-empty string.",
    )

    tags = metadata_service.get_tags_for_series_category(category)
    return {"category": category, "tags": tags}


def handle_get_series_list(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    category: str | None = None
    tags: str | None = None
    cursor: str | None = None
    limit: int | None = None
    include_product_metadata = False
    include_volume = False

    if arguments is not None:
        category = _parse_optional_str(
            arguments,
            "category",
            type_error="category must be a string.",
            empty_error="category must be a non-empty string.",
        )
        tags = _parse_optional_str(
            arguments,
            "tags",
            type_error="tags must be a string.",
            empty_error="tags must be a non-empty string.",
        )
        cursor = _parse_optional_str(
            arguments,
            "cursor",
            type_error="cursor must be a string.",
            empty_error="cursor must be a non-empty string.",
        )
        limit = _parse_optional_int(
            arguments,
            "limit",
            type_error="limit must be an integer.",
            range_error="limit must be between 1 and 1000.",
            min_value=1,
            max_value=1000,
        )
        include_product_metadata = _parse_bool(
            arguments,
            "include_product_metadata",
            False,
            type_error="include_product_metadata must be a boolean.",
        )
        include_volume = _parse_bool(
            arguments,
            "include_volume",
            False,
            type_error="include_volume must be a boolean.",
        )

    series_list = metadata_service.get_series_list(
        category=category,
        tags=tags,
        cursor=cursor,
        limit=limit,
        include_product_metadata=include_product_metadata,
        include_volume=include_volume,
    )
    return _serialize_series_list(series_list)

def handle_get_markets(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    cursor: str | None = None
    limit: int | None = None
    event_ticker: str | None = None
    series_ticker: str | None = None
    tickers: str | None = None
    status: str | None = None
    mve_filter: str | None = None
    min_created_ts: int | None = None
    max_created_ts: int | None = None
    min_updated_ts: int | None = None
    min_close_ts: int | None = None
    max_close_ts: int | None = None
    min_settled_ts: int | None = None
    max_settled_ts: int | None = None

    if arguments is not None:
        cursor = _parse_optional_str(
            arguments,
            "cursor",
            type_error="cursor must be a string.",
            empty_error="cursor must be a non-empty string.",
        )
        limit = _parse_optional_int(
            arguments,
            "limit",
            type_error="limit must be an integer.",
            range_error="limit must be between 1 and 1000.",
            min_value=1,
            max_value=1000,
        )
        event_ticker = _parse_optional_str(
            arguments,
            "event_ticker",
            type_error="event_ticker must be a string.",
            empty_error="event_ticker must be a non-empty string.",
        )
        series_ticker = _parse_optional_str(
            arguments,
            "series_ticker",
            type_error="series_ticker must be a string.",
            empty_error="series_ticker must be a non-empty string.",
        )
        tickers = _parse_optional_str(
            arguments,
            "tickers",
            type_error="tickers must be a string.",
            empty_error="tickers must be a non-empty string.",
        )
        status = _parse_optional_str(
            arguments,
            "status",
            type_error="status must be a string.",
            empty_error="status must be a non-empty string.",
        )

        mve_filter = _parse_optional_str(
            arguments,
            "mve_filter",
            type_error="mve_filter must be a string.",
            empty_error="mve_filter must be a non-empty string.",
        )
        if mve_filter is not None:
            allowed_mve = {"only", "exclude"}
            if mve_filter not in allowed_mve:
                raise ValueError("mve_filter must be one of only, exclude.")

        ts_max = 10_000_000_000
        min_created_ts = _parse_optional_int(
            arguments,
            "min_created_ts",
            type_error="min_created_ts must be an integer.",
            range_error="min_created_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        max_created_ts = _parse_optional_int(
            arguments,
            "max_created_ts",
            type_error="max_created_ts must be an integer.",
            range_error="max_created_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        min_updated_ts = _parse_optional_int(
            arguments,
            "min_updated_ts",
            type_error="min_updated_ts must be an integer.",
            range_error="min_updated_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        min_close_ts = _parse_optional_int(
            arguments,
            "min_close_ts",
            type_error="min_close_ts must be an integer.",
            range_error="min_close_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        max_close_ts = _parse_optional_int(
            arguments,
            "max_close_ts",
            type_error="max_close_ts must be an integer.",
            range_error="max_close_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        min_settled_ts = _parse_optional_int(
            arguments,
            "min_settled_ts",
            type_error="min_settled_ts must be an integer.",
            range_error="min_settled_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )
        max_settled_ts = _parse_optional_int(
            arguments,
            "max_settled_ts",
            type_error="max_settled_ts must be an integer.",
            range_error="max_settled_ts must be a non-negative integer.",
            min_value=0,
            max_value=ts_max,
        )

    markets_list = metadata_service.get_markets(
        cursor=cursor,
        limit=limit,
        event_ticker=event_ticker,
        series_ticker=series_ticker,
        tickers=tickers,
        status=status,
        mve_filter=mve_filter,
        min_created_ts=min_created_ts,
        max_created_ts=max_created_ts,
        min_updated_ts=min_updated_ts,
        min_close_ts=min_close_ts,
        max_close_ts=max_close_ts,
        min_settled_ts=min_settled_ts,
        max_settled_ts=max_settled_ts,
    )
    return _serialize_markets_list(markets_list)


def _page_open_markets_for_series(
    metadata_service: MetadataService,
    *,
    series_ticker: str,
    limit: int,
    max_pages: int,
) -> tuple[list[Market], int]:
    markets: list[Market] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    pages = 0

    while True:
        if pages >= max_pages:
            raise ValueError(
                "Exceeded max_pages while paging /markets; reduce scope or increase max_pages."
            )

        markets_list = metadata_service.get_markets(
            cursor=cursor,
            limit=limit,
            series_ticker=series_ticker,
            status="open",
        )
        markets.extend(markets_list.markets)

        pages += 1
        next_cursor = markets_list.cursor
        if next_cursor is None:
            break

        # Protect against a buggy/looping cursor.
        if next_cursor in seen_cursors:
            raise ValueError("Kalshi /markets cursor repeated; aborting pagination.")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    return markets, pages


def handle_get_open_markets_for_series(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    args = _require_arguments(arguments, "get_open_markets_for_series")
    series_ticker = _parse_required_str(
        args,
        "series_ticker",
        type_error="series_ticker must be a string.",
        empty_error="series_ticker must be a non-empty string.",
    )

    # Default to max Kalshi page size to minimize API round-trips.
    limit = (
        _parse_optional_int(
            args,
            "limit",
            type_error="limit must be an integer.",
            range_error="limit must be between 1 and 1000.",
            min_value=1,
            max_value=1000,
        )
        or 1000
    )
    max_pages = (
        _parse_optional_int(
            args,
            "max_pages",
            type_error="max_pages must be an integer.",
            range_error="max_pages must be between 1 and 10000.",
            min_value=1,
            max_value=10000,
        )
        or 1000
    )

    markets, pages = _page_open_markets_for_series(
        metadata_service, series_ticker=series_ticker, limit=limit, max_pages=max_pages
    )
    return {
        "series_ticker": series_ticker,
        "status": "open",
        "markets": [_serialize_market(m) for m in markets],
        "count": len(markets),
        "pages": pages,
    }


def handle_get_open_market_titles_for_series(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    args = _require_arguments(arguments, "get_open_market_titles_for_series")
    series_ticker = _parse_required_str(
        args,
        "series_ticker",
        type_error="series_ticker must be a string.",
        empty_error="series_ticker must be a non-empty string.",
    )

    # Default to max Kalshi page size to minimize API round-trips.
    limit = (
        _parse_optional_int(
            args,
            "limit",
            type_error="limit must be an integer.",
            range_error="limit must be between 1 and 1000.",
            min_value=1,
            max_value=1000,
        )
        or 1000
    )
    max_pages = (
        _parse_optional_int(
            args,
            "max_pages",
            type_error="max_pages must be an integer.",
            range_error="max_pages must be between 1 and 10000.",
            min_value=1,
            max_value=10000,
        )
        or 1000
    )

    markets, pages = _page_open_markets_for_series(
        metadata_service, series_ticker=series_ticker, limit=limit, max_pages=max_pages
    )
    return {
        "series_ticker": series_ticker,
        "status": "open",
        "markets": [{"ticker": m.ticker, "title": m.title, "subtitle": m.subtitle} for m in markets],
        "count": len(markets),
        "pages": pages,
    }


def handle_get_series_tickers_for_category(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    args = _require_arguments(arguments, "get_series_tickers_for_category")

    category = _parse_required_str(
        args,
        "category",
        type_error="category must be a string.",
        empty_error="category must be a non-empty string.",
    )
    tags = _parse_optional_str(
        args,
        "tags",
        type_error="tags must be a string.",
        empty_error="tags must be a non-empty string.",
    )

    # Default to max Kalshi page size to minimize API round-trips.
    limit = (
        _parse_optional_int(
            args,
            "limit",
            type_error="limit must be an integer.",
            range_error="limit must be between 1 and 1000.",
            min_value=1,
            max_value=1000,
        )
        or 1000
    )

    max_pages = (
        _parse_optional_int(
            args,
            "max_pages",
            type_error="max_pages must be an integer.",
            range_error="max_pages must be between 1 and 10000.",
            min_value=1,
            max_value=10000,
        )
        or 1000
    )

    tickers: list[str] = []
    seen_tickers: set[str] = set()
    cursor: str | None = None
    seen_cursors: set[str] = set()
    pages = 0

    while True:
        if pages >= max_pages:
            raise ValueError(
                "Exceeded max_pages while paging /series; "
                "reduce scope with tags or increase max_pages."
            )

        series_list = metadata_service.get_series_list(
            category=category,
            tags=tags,
            cursor=cursor,
            limit=limit,
            include_product_metadata=False,
            include_volume=False,
        )

        for series in series_list.series:
            if series.ticker not in seen_tickers:
                seen_tickers.add(series.ticker)
                tickers.append(series.ticker)

        pages += 1
        next_cursor = series_list.cursor
        if next_cursor is None:
            break

        # Protect against a buggy/looping cursor.
        if next_cursor in seen_cursors:
            raise ValueError("Kalshi /series cursor repeated; aborting pagination.")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    payload: dict[str, Any] = {
        "category": category,
        "tickers": tickers,
        "count": len(tickers),
        "pages": pages,
    }
    if tags is not None:
        payload["tags"] = tags
    return payload


def _serialize_series_list(series_list: SeriesList) -> dict[str, Any]:
    serialized: dict[str, Any] = {"series": [_serialize_series(item) for item in series_list.series]}
    if series_list.cursor is not None:
        serialized["cursor"] = series_list.cursor
    return serialized


def _serialize_series(series: Series) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ticker": series.ticker,
        "frequency": series.frequency,
        "title": series.title,
        "category": series.category,
        "tags": series.tags,
        "settlement_sources": [
            _serialize_settlement_source(source) for source in series.settlement_sources
        ],
        "contract_url": series.contract_url,
        "contract_terms_url": series.contract_terms_url,
        "fee_type": series.fee_type,
        "fee_multiplier": series.fee_multiplier,
        "additional_prohibitions": series.additional_prohibitions,
    }
    if series.product_metadata is not None:
        payload["product_metadata"] = series.product_metadata
    if series.volume is not None:
        payload["volume"] = series.volume
    if series.volume_fp is not None:
        payload["volume_fp"] = series.volume_fp

    return payload


def _serialize_settlement_source(source: SettlementSource) -> dict[str, str]:
    return {"name": source.name, "url": source.url}


def _serialize_markets_list(markets_list: MarketsList) -> dict[str, Any]:
    serialized: dict[str, Any] = {"markets": [_serialize_market(item) for item in markets_list.markets]}
    if markets_list.cursor is not None:
        serialized["cursor"] = markets_list.cursor
    return serialized


def _serialize_market(market: Market) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ticker": market.ticker,
        "event_ticker": market.event_ticker,
        "market_type": market.market_type,
        "title": market.title,
        "subtitle": market.subtitle,
        "status": market.status,
    }

    _maybe(payload, "series_ticker", market.series_ticker)
    _maybe(payload, "yes_sub_title", market.yes_sub_title)
    _maybe(payload, "no_sub_title", market.no_sub_title)
    _maybe(payload, "created_time", market.created_time)
    _maybe(payload, "updated_time", market.updated_time)
    _maybe(payload, "open_time", market.open_time)
    _maybe(payload, "close_time", market.close_time)
    _maybe(payload, "expiration_time", market.expiration_time)
    _maybe(payload, "latest_expiration_time", market.latest_expiration_time)
    _maybe(payload, "response_price_units", market.response_price_units)

    _maybe(payload, "settlement_timer_seconds", market.settlement_timer_seconds)
    _maybe(payload, "yes_bid", market.yes_bid)
    _maybe(payload, "yes_ask", market.yes_ask)
    _maybe(payload, "no_bid", market.no_bid)
    _maybe(payload, "no_ask", market.no_ask)
    _maybe(payload, "last_price", market.last_price)
    _maybe(payload, "volume", market.volume)
    _maybe(payload, "volume_24h", market.volume_24h)
    _maybe(payload, "open_interest", market.open_interest)
    _maybe(payload, "notional_value", market.notional_value)
    _maybe(payload, "previous_yes_bid", market.previous_yes_bid)
    _maybe(payload, "previous_yes_ask", market.previous_yes_ask)
    _maybe(payload, "previous_price", market.previous_price)
    _maybe(payload, "liquidity", market.liquidity)
    _maybe(payload, "tick_size", market.tick_size)
    _maybe(payload, "settlement_value", market.settlement_value)
    _maybe(payload, "floor_strike", market.floor_strike)
    _maybe(payload, "cap_strike", market.cap_strike)

    _maybe(payload, "yes_bid_dollars", market.yes_bid_dollars)
    _maybe(payload, "yes_ask_dollars", market.yes_ask_dollars)
    _maybe(payload, "no_bid_dollars", market.no_bid_dollars)
    _maybe(payload, "no_ask_dollars", market.no_ask_dollars)
    _maybe(payload, "last_price_dollars", market.last_price_dollars)
    _maybe(payload, "volume_fp", market.volume_fp)
    _maybe(payload, "volume_24h_fp", market.volume_24h_fp)
    _maybe(payload, "open_interest_fp", market.open_interest_fp)
    _maybe(payload, "notional_value_dollars", market.notional_value_dollars)
    _maybe(payload, "previous_yes_bid_dollars", market.previous_yes_bid_dollars)
    _maybe(payload, "previous_yes_ask_dollars", market.previous_yes_ask_dollars)
    _maybe(payload, "previous_price_dollars", market.previous_price_dollars)
    _maybe(payload, "liquidity_dollars", market.liquidity_dollars)
    _maybe(payload, "settlement_value_dollars", market.settlement_value_dollars)

    _maybe(payload, "result", market.result)
    _maybe(payload, "can_close_early", market.can_close_early)
    _maybe(payload, "expiration_value", market.expiration_value)
    _maybe(payload, "rules_primary", market.rules_primary)
    _maybe(payload, "rules_secondary", market.rules_secondary)
    _maybe(payload, "price_level_structure", market.price_level_structure)
    if market.price_ranges is not None:
        payload["price_ranges"] = [_serialize_price_range(item) for item in market.price_ranges]
    _maybe(payload, "expected_expiration_time", market.expected_expiration_time)
    _maybe(payload, "settlement_ts", market.settlement_ts)
    _maybe(payload, "fee_waiver_expiration_time", market.fee_waiver_expiration_time)
    _maybe(payload, "early_close_condition", market.early_close_condition)
    _maybe(payload, "strike_type", market.strike_type)
    _maybe(payload, "functional_strike", market.functional_strike)
    if market.custom_strike is not None:
        payload["custom_strike"] = market.custom_strike
    _maybe(payload, "mve_collection_ticker", market.mve_collection_ticker)
    if market.mve_selected_legs is not None:
        payload["mve_selected_legs"] = [
            _serialize_mve_selected_leg(item) for item in market.mve_selected_legs
        ]
    _maybe(payload, "primary_participant_key", market.primary_participant_key)
    _maybe(payload, "is_provisional", market.is_provisional)

    return payload


def _serialize_price_range(item: PriceRange) -> dict[str, str]:
    return {"start": item.start, "end": item.end, "step": item.step}


def _serialize_mve_selected_leg(item: MveSelectedLeg) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_ticker": item.event_ticker,
        "market_ticker": item.market_ticker,
        "side": item.side,
    }
    _maybe(payload, "yes_settlement_value_dollars", item.yes_settlement_value_dollars)
    return payload


def _maybe(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value
