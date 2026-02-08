"""MCP resource registry for exposing Kalshi data as read-only resources.

Tools are for actions (tools/call). Resources are for data (resources/read).
This module maps a small set of Kalshi endpoints to stable `kalshi:///...` URIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import parse


@dataclass(frozen=True)
class ResourceDescriptor:
    uri: str
    name: str
    description: str
    mimeType: str = "application/json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mimeType,
        }


@dataclass(frozen=True)
class ResourceTemplateDescriptor:
    uriTemplate: str
    name: str
    description: str
    mimeType: str = "application/json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uriTemplate": self.uriTemplate,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mimeType,
        }


class ResourceRegistry:
    def __init__(self, tool_registry: Any) -> None:
        # Keep it loosely typed to avoid import cycles; we only need call_tool().
        self._tool_registry = tool_registry

    def list_resources(self) -> list[dict[str, Any]]:
        resources = [
            ResourceDescriptor(
                uri="kalshi:///categories",
                name="Kalshi Categories",
                description="All Kalshi series categories (derived from tags_by_categories).",
            ),
            ResourceDescriptor(
                uri="kalshi:///tags_by_categories",
                name="Kalshi Tags By Categories",
                description="Kalshi tags grouped by series category.",
            ),
        ]
        return [item.to_dict() for item in resources]

    def list_resource_templates(self) -> list[dict[str, Any]]:
        templates = [
            ResourceTemplateDescriptor(
                uriTemplate="kalshi:///category/{category}/tags",
                name="Kalshi Tags For Category",
                description="Tags for a single series category.",
            ),
            ResourceTemplateDescriptor(
                uriTemplate="kalshi:///category/{category}/series_tickers{?tags,limit,max_pages}",
                name="Kalshi Series Tickers For Category",
                description="All series tickers for a single category (paged from /series).",
            ),
            ResourceTemplateDescriptor(
                uriTemplate=(
                    "kalshi:///series{?category,tags,cursor,limit,include_product_metadata,include_volume}"
                ),
                name="Kalshi Series List",
                description="Market series list, optionally filtered by category/tags and including metadata/volume.",
            ),
        ]
        return [item.to_dict() for item in templates]

    def read_resource(self, uri: str) -> dict[str, Any]:
        if not isinstance(uri, str) or not uri:
            raise ValueError("Missing resource uri")

        parsed = parse.urlparse(uri)
        if parsed.scheme != "kalshi":
            raise ValueError("Unsupported resource scheme (expected kalshi://)")

        path = parsed.path or "/"
        payload = self._route(path, parsed.query)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, indent=2, sort_keys=True),
                }
            ]
        }

    def _route(self, path: str, query: str) -> dict[str, Any]:
        if path == "/categories":
            return self._tool_registry.call_tool("get_categories", {})

        if path == "/tags_by_categories":
            return self._tool_registry.call_tool("get_tags_for_series_categories", {})

        if path.startswith("/category/") and path.endswith("/tags"):
            # /category/{category}/tags
            parts = [p for p in path.split("/") if p]
            if len(parts) != 3 or parts[0] != "category" or parts[2] != "tags":
                raise ValueError("Invalid category tags resource uri")
            category = parse.unquote(parts[1])
            return self._tool_registry.call_tool(
                "get_tags_for_series_category", {"category": category}
            )

        if path.startswith("/category/") and path.endswith("/series_tickers"):
            # /category/{category}/series_tickers
            parts = [p for p in path.split("/") if p]
            if len(parts) != 3 or parts[0] != "category" or parts[2] != "series_tickers":
                raise ValueError("Invalid category series tickers resource uri")
            category = parse.unquote(parts[1])
            args: dict[str, Any] = {"category": category}
            q = parse.parse_qs(query, keep_blank_values=False)
            if "tags" in q and q["tags"]:
                args["tags"] = q["tags"][0]
            if "limit" in q and q["limit"]:
                args["limit"] = _parse_int(q["limit"][0])
            if "max_pages" in q and q["max_pages"]:
                args["max_pages"] = _parse_int(q["max_pages"][0])
            return self._tool_registry.call_tool("get_series_tickers_for_category", args)

        if path == "/series":
            args: dict[str, Any] = {}
            q = parse.parse_qs(query, keep_blank_values=False)
            if "category" in q and q["category"]:
                args["category"] = q["category"][0]
            if "tags" in q and q["tags"]:
                args["tags"] = q["tags"][0]
            if "cursor" in q and q["cursor"]:
                args["cursor"] = q["cursor"][0]
            if "limit" in q and q["limit"]:
                args["limit"] = _parse_int(q["limit"][0])
            if "include_product_metadata" in q and q["include_product_metadata"]:
                args["include_product_metadata"] = _parse_bool(q["include_product_metadata"][0])
            if "include_volume" in q and q["include_volume"]:
                args["include_volume"] = _parse_bool(q["include_volume"][0])
            return self._tool_registry.call_tool("get_series_list", args)

        raise ValueError("Unknown resource uri")


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes", "y", "t"):
        return True
    if normalized in ("false", "0", "no", "n", "f"):
        return False
    raise ValueError("Expected boolean query value (true/false)")


def _parse_int(value: str) -> int:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Expected integer query value")
    try:
        return int(normalized, 10)
    except ValueError as exc:
        raise ValueError("Expected integer query value") from exc
