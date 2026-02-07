# kalshi-mcp-server
An mcp server that allows AI to operate on the prediction market, Kalshi

## Implemented Public Tool
- `get_tags_for_series_categories`
  - Calls Kalshi public endpoint: `GET /search/tags_by_categories`
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
