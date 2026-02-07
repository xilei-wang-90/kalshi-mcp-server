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

GET_CATEGORIES_TOOL = {
    "name": "get_categories",
    "description": (
        "Get all Kalshi categories. "
        "Uses the public GET /search/tags_by_categories endpoint."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

GET_TAGS_FOR_SERIES_CATEGORY_TOOL = {
    "name": "get_tags_for_series_category",
    "description": (
        "Get Kalshi tags for a single series category. "
        "Uses the public GET /search/tags_by_categories endpoint."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Exact Kalshi series category name.",
                "minLength": 1,
            }
        },
        "required": ["category"],
        "additionalProperties": False,
    },
}
