"""MCP tool handlers."""

from __future__ import annotations

from typing import Any, Callable

from ..models import Series, SeriesList, SettlementSource, TagsByCategories
from ..services import MetadataService

ToolHandler = Callable[[dict[str, Any] | None], dict[str, Any]]


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
    if arguments is None:
        raise ValueError("Missing arguments for get_tags_for_series_category.")

    category = arguments.get("category")
    if not isinstance(category, str):
        raise ValueError("category must be a string.")

    tags = metadata_service.get_tags_for_series_category(category)
    return {"category": category.strip(), "tags": tags}


def handle_get_series_list(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    category: str | None = None
    tags: str | None = None
    include_product_metadata = False
    include_volume = False

    if arguments is not None:
        raw_category = arguments.get("category")
        if raw_category is not None:
            if not isinstance(raw_category, str):
                raise ValueError("category must be a string.")
            category = raw_category.strip()
            if not category:
                raise ValueError("category must be a non-empty string.")

        raw_tags = arguments.get("tags")
        if raw_tags is not None:
            if not isinstance(raw_tags, str):
                raise ValueError("tags must be a string.")
            tags = raw_tags.strip()
            if not tags:
                raise ValueError("tags must be a non-empty string.")

        raw_include_product_metadata = arguments.get("include_product_metadata", False)
        if not isinstance(raw_include_product_metadata, bool):
            raise ValueError("include_product_metadata must be a boolean.")
        include_product_metadata = raw_include_product_metadata

        raw_include_volume = arguments.get("include_volume", False)
        if not isinstance(raw_include_volume, bool):
            raise ValueError("include_volume must be a boolean.")
        include_volume = raw_include_volume

    series_list = metadata_service.get_series_list(
        category=category,
        tags=tags,
        include_product_metadata=include_product_metadata,
        include_volume=include_volume,
    )
    return _serialize_series_list(series_list)


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
