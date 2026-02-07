"""MCP tool handlers."""

from __future__ import annotations

from typing import Any, Callable

from ..models import TagsByCategories
from ..services import MetadataService

ToolHandler = Callable[[dict[str, Any] | None], dict[str, Any]]


def build_tool_handlers(metadata_service: MetadataService) -> dict[str, ToolHandler]:
    return {
        "get_tags_for_series_categories": lambda arguments: (
            handle_get_tags_for_series_categories(metadata_service, arguments)
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
