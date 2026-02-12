# CLAUDE.md

This file provides guidance for Claude Code when working with this codebase.

## Project Purpose

This is an **MCP (Model Context Protocol) server** for the **Kalshi prediction market API**. It enables AI assistants like Claude to interact with Kalshi's trading platform through a standardized JSON-RPC 2.0 interface over stdio.

Key capabilities:
- **MCP tools** for querying market data and portfolio information
- **Public endpoints** (no auth) for market/series data
- **Private endpoints** (authenticated) for portfolio operations
- **MCP Resources** for exposing data as read-only URIs

## Architecture Overview

```
src/kalshi_mcp/
├── server.py          # MCP server engine, ToolRegistry, JSON-RPC handling
├── settings.py        # Configuration loading from .env and environment
├── models.py          # Dataclasses for API responses (Market, Series, etc.)
├── kalshi_client.py   # HTTP client with retry logic and RSA auth
├── services.py        # Business logic layer (MetadataService, PortfolioService)
└── mcp/
    ├── schema.py      # Tool definitions (JSON-RPC schemas)
    ├── handlers.py    # Tool implementations
    └── resources.py   # Resource URI routing
```

### File Purposes

| File | Purpose |
|------|---------|
| `server.py` | MCP server engine. Contains `ToolRegistry` for managing tools and `StdioMCPServer` for JSON-RPC protocol handling. Entry point is `main()`. |
| `settings.py` | Configuration via `Settings` dataclass. Loads from `.env` file and environment variables. |
| `models.py` | Dataclasses representing Kalshi API responses: `Market`, `Series`, `PortfolioBalance`, `TagsByCategories`, etc. |
| `kalshi_client.py` | HTTP communication with Kalshi API. Handles retries, RSA-SHA256 authentication, response parsing, and validation. |
| `services.py` | Business logic layer. `MetadataService` wraps market/series calls; `PortfolioService` wraps authenticated calls. |
| `mcp/schema.py` | Declarative tool definitions as JSON-RPC schema dicts with `inputSchema` for each tool. |
| `mcp/handlers.py` | Tool implementation functions. Parses arguments, calls services, serializes responses. |
| `mcp/resources.py` | Maps `kalshi:///` URIs to tool calls. Provides static resources and URI templates. |

## Adding a New Tool

To add a new tool, modify these files in order but do not modify existing model unless it is only an extension, do not break existing tools:

### 1. Define the Schema (`mcp/schema.py`)

```python
GET_NEW_TOOL = {
    "name": "get_new_tool",
    "description": "Description of what this tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Required parameter",
                "minLength": 1,
            },
        },
        "required": ["param1"],
        "additionalProperties": False,
    },
}
```

### 2. Add Client Method (`kalshi_client.py`)

```python
def get_new_data(self, param1: str) -> SomeModel:
    """Return new data from Kalshi."""
    path = f"/new_endpoint?param1={parse.quote(param1)}"
    payload = self._get_json(path, authenticated=False)  # or True
    return SomeModel(...)
```

### 3. Add Service Method (`services.py`)

```python
# In MetadataService or PortfolioService
def get_new_data(self, param1: str) -> SomeModel:
    return self._client.get_new_data(param1)
```

### 4. Add Handler Function (`mcp/handlers.py`)

```python
def handle_get_new_tool(
    metadata_service: MetadataService, arguments: dict[str, Any] | None
) -> dict[str, Any]:
    args = _require_arguments(arguments, "get_new_tool")
    param1 = _parse_required_str(args, "param1", ...)
    result = metadata_service.get_new_data(param1)
    return _serialize_new_data(result)
```

Register in `build_tool_handlers()`:
```python
"get_new_tool": lambda arguments: handle_get_new_tool(metadata_service, arguments),
```

### 5. Register Schema (`server.py`)

Import and add to `ToolRegistry.list_tools()`:
```python
from .mcp.schema import GET_NEW_TOOL

def list_tools(self) -> list[dict[str, Any]]:
    return [
        # ... existing tools ...
        GET_NEW_TOOL,
    ]
```

### 6. (Optional) Add Resource Route (`mcp/resources.py`)

If the tool should be accessible as a resource URI, add a template and route.

### 7. Add Tests (`tests/unit/test_mcp_handlers.py`)

Add test cases using fake service mocks.

### 8. Document in README (`README.md`)

Add the new tool to the "Implemented Tools" section in `README.md`, following the format of existing tool entries. Include the endpoint, authentication requirements, and any arguments.

## Configuration

Environment variables (can be set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `KALSHI_API_BASE_URL` | `https://api.elections.kalshi.com/trade-api/v2` | API base URL |
| `KALSHI_TIMEOUT_SECONDS` | `10` | Request timeout |
| `KALSHI_API_KEY_ID` | (none) | API key ID for authenticated endpoints |
| `KALSHI_API_KEY_PATH` | (none) | Path to PEM private key file |

## Running

```bash
# Install dependencies
pip install -e .

# Run the MCP server
python -m kalshi_mcp.server
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Key Implementation Details

- **Protocol**: JSON-RPC 2.0 over stdio
- **Authentication**: RSA-SHA256 signing with timestamp headers
- **Retry Logic**: Up to 4 attempts with exponential backoff for 429/5xx errors
- **Pagination**: Cursor-based with loop detection to prevent infinite loops
- **Python**: Requires 3.12+
- **Dependencies**: `cryptography>=42.0` (runtime), `pytest>=8.0` (dev)
