# kalshi-mcp-server
An mcp server that allows AI to operate on the prediction market, Kalshi

## Implemented Public Tool
- `get_tags_for_series_categories`
  - Calls Kalshi public endpoint: `GET /search/tags_by_categories`
  - No API key required
- `get_categories`
  - Calls Kalshi public endpoint: `GET /search/tags_by_categories`
  - Returns only the category names
  - No API key required
- `get_tags_for_series_category`
  - Calls Kalshi public endpoint: `GET /search/tags_by_categories`
  - Requires one argument: `category` (exact category name)
  - Returns tags for the selected category
  - No API key required
- `get_series_list`
  - Calls Kalshi public endpoint: `GET /series`
  - Optional arguments:
    - `category` (string)
    - `tags` (string)
    - `include_product_metadata` (boolean)
    - `include_volume` (boolean)
  - Returns typed series objects from Kalshi response
  - Logs warning/error details when response fields have unexpected types/shapes
  - No API key required

## Configuration
- `KALSHI_API_BASE_URL`
  - Default: `https://api.elections.kalshi.com/trade-api/v2`
- `KALSHI_TIMEOUT_SECONDS`
  - Default: `10`

## Run as MCP stdio server
- Command:
  - `PYTHONPATH=src python3 -m kalshi_mcp.server`
- Transport:
  - JSON-RPC 2.0 over newline-delimited JSON on stdin/stdout
