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

GET_SERIES_LIST_TOOL = {
    "name": "get_series_list",
    "description": (
        "Get Kalshi market series list. "
        "Uses the public GET /series endpoint."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Optional category filter.",
                "minLength": 1,
            },
            "tags": {
                "type": "string",
                "description": "Optional tags filter.",
                "minLength": 1,
            },
            "include_product_metadata": {
                "type": "boolean",
                "description": "Include product metadata in each series item.",
            },
            "include_volume": {
                "type": "boolean",
                "description": "Include volume fields in each series item.",
            },
        },
        "additionalProperties": False,
    },
}
