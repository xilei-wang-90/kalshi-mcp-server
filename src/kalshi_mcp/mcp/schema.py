"""MCP tool schemas and I/O models."""

GET_TAGS_FOR_SERIES_CATEGORIES_TOOL = {
    "name": "get_tags_for_series_categories",
    "description": (
        "Get Kalshi tags grouped by series categories. "
        "Uses the public GET /search/tags_by_categories endpoint."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}
