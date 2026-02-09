"""MCP tool handlers."""

from __future__ import annotations

from typing import Any, Callable

from ..models import Series, SeriesList, SettlementSource, TagsByCategories
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
