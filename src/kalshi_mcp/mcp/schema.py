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
            "cursor": {
                "type": "string",
                "description": "Optional pagination cursor.",
                "minLength": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Optional page size (1-1000).",
                "minimum": 1,
                "maximum": 1000,
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

GET_MARKETS_TOOL = {
    "name": "get_markets",
    "description": (
        "Get Kalshi markets list. "
        "Uses the public GET /markets endpoint."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "cursor": {
                "type": "string",
                "description": "Optional pagination cursor.",
                "minLength": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Optional page size (1-1000).",
                "minimum": 1,
                "maximum": 1000,
            },
            "status": {
                "type": "string",
                "description": (
                    "Optional market status filter (Kalshi docs list values like "
                    "unopened, open, paused, closed, settled)."
                ),
                "minLength": 1,
            },
            "tickers": {
                "type": "string",
                "description": "Optional comma-separated list of market tickers to retrieve.",
                "minLength": 1,
            },
            "event_ticker": {
                "type": "string",
                "description": (
                    "Optional comma-separated list of event tickers to retrieve. "
                    "Kalshi docs note a maximum of 10."
                ),
                "minLength": 1,
            },
            "series_ticker": {
                "type": "string",
                "description": "Optional series ticker to filter markets by.",
                "minLength": 1,
            },
            "mve_filter": {
                "type": "string",
                "description": "Optional filter for multiple-vs-binary markets.",
                "enum": ["only", "exclude"],
            },
            "min_created_ts": {
                "type": "integer",
                "description": "Optional minimum unix timestamp (seconds) for market creation time.",
                "minimum": 0,
            },
            "max_created_ts": {
                "type": "integer",
                "description": "Optional maximum unix timestamp (seconds) for market creation time.",
                "minimum": 0,
            },
            "min_updated_ts": {
                "type": "integer",
                "description": "Optional minimum unix timestamp (seconds) for market update time.",
                "minimum": 0,
            },
            "min_close_ts": {
                "type": "integer",
                "description": "Optional minimum unix timestamp (seconds) for market close time.",
                "minimum": 0,
            },
            "max_close_ts": {
                "type": "integer",
                "description": "Optional maximum unix timestamp (seconds) for market close time.",
                "minimum": 0,
            },
            "min_settled_ts": {
                "type": "integer",
                "description": "Optional minimum unix timestamp (seconds) for market settlement time.",
                "minimum": 0,
            },
            "max_settled_ts": {
                "type": "integer",
                "description": "Optional maximum unix timestamp (seconds) for market settlement time.",
                "minimum": 0,
            },
        },
        "additionalProperties": False,
    },
}

GET_OPEN_MARKETS_FOR_SERIES_TOOL = {
    "name": "get_open_markets_for_series",
    "description": (
        "Get all OPEN markets for a Kalshi series ticker. "
        "Internally pages through the public GET /markets endpoint with status=open."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "series_ticker": {
                "type": "string",
                "description": "Series ticker to filter markets by.",
                "minLength": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Optional page size for each /markets request (1-1000). Defaults to 1000.",
                "minimum": 1,
                "maximum": 1000,
            },
            "max_pages": {
                "type": "integer",
                "description": (
                    "Safety cap on number of pages to fetch. Defaults to 1000. "
                    "Set lower to bound response size/time."
                ),
                "minimum": 1,
                "maximum": 10000,
            },
        },
        "required": ["series_ticker"],
        "additionalProperties": False,
    },
}

GET_OPEN_MARKET_TITLES_FOR_SERIES_TOOL = {
    "name": "get_open_market_titles_for_series",
    "description": (
        "Get ticker + title + subtitle for all OPEN markets in a Kalshi series ticker. "
        "Internally pages through the public GET /markets endpoint with status=open."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "series_ticker": {
                "type": "string",
                "description": "Series ticker to filter markets by.",
                "minLength": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Optional page size for each /markets request (1-1000). Defaults to 1000.",
                "minimum": 1,
                "maximum": 1000,
            },
            "max_pages": {
                "type": "integer",
                "description": (
                    "Safety cap on number of pages to fetch. Defaults to 1000. "
                    "Set lower to bound response size/time."
                ),
                "minimum": 1,
                "maximum": 10000,
            },
        },
        "required": ["series_ticker"],
        "additionalProperties": False,
    },
}

GET_SERIES_TICKERS_FOR_CATEGORY_TOOL = {
    "name": "get_series_tickers_for_category",
    "description": (
        "Get all Kalshi series tickers for a particular category. "
        "Internally pages through the public GET /series endpoint and extracts `ticker`."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Exact Kalshi series category name.",
                "minLength": 1,
            },
            "tags": {
                "type": "string",
                "description": "Optional tags filter (same meaning as /series?tags=...).",
                "minLength": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Optional page size for each /series request (1-1000). Defaults to 1000.",
                "minimum": 1,
                "maximum": 1000,
            },
            "max_pages": {
                "type": "integer",
                "description": (
                    "Safety cap on number of pages to fetch. Defaults to 1000. "
                    "Set lower to bound response size/time."
                ),
                "minimum": 1,
                "maximum": 10000,
            },
        },
        "required": ["category"],
        "additionalProperties": False,
    },
}
