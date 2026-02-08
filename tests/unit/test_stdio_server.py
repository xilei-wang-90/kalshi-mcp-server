import io
import json
import unittest

from kalshi_mcp.server import StdioMCPServer, ToolRegistry


class StdioServerTests(unittest.TestCase):
    def test_initialize_tools_list_and_tools_call(self) -> None:
        handlers = {
            "get_tags_for_series_categories": lambda arguments: {
                "tags_by_categories": {"Politics": ["Trump", "Biden"]}
            },
            "get_categories": lambda arguments: {
                "categories": ["Politics"]
            },
            "get_tags_for_series_category": lambda arguments: {
                "category": arguments["category"],
                "tags": ["Trump", "Biden"],
            },
            "get_series_list": lambda arguments: {
                "series": [
                    {
                        "ticker": "KXBTCUSD",
                        "frequency": "daily",
                        "title": "Will Bitcoin close above 100k?",
                        "category": "Crypto",
                        "tags": ["BTC"],
                        "settlement_sources": [],
                        "contract_url": "https://kalshi.com/series/KXBTCUSD",
                        "contract_terms_url": "https://kalshi.com/terms/KXBTCUSD",
                        "fee_type": "linear",
                        "fee_multiplier": 1.0,
                        "additional_prohibitions": [],
                    }
                ]
            },
        }
        registry = ToolRegistry(handlers)
        stdin = io.StringIO(
            "\n".join(
                [
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2025-06-18",
                                "capabilities": {},
                                "clientInfo": {"name": "test", "version": "0.0.1"},
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                            "params": {},
                        }
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/list",
                            "params": {},
                        }
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "tools/call",
                            "params": {
                                "name": "get_tags_for_series_categories",
                                "arguments": {},
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 4,
                            "method": "tools/call",
                            "params": {
                                "name": "get_tags_for_series_category",
                                "arguments": {"category": "Politics"},
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 5,
                            "method": "tools/call",
                            "params": {
                                "name": "get_series_list",
                                "arguments": {"category": "Crypto"},
                            },
                        }
                    ),
                ]
            )
            + "\n"
        )
        stdout = io.StringIO()

        server = StdioMCPServer(registry, stdin=stdin, stdout=stdout)
        server.run()

        lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(5, len(lines))

        initialize_response = json.loads(lines[0])
        self.assertEqual("2.0", initialize_response["jsonrpc"])
        self.assertEqual(1, initialize_response["id"])
        self.assertEqual(
            "kalshi-mcp-server", initialize_response["result"]["serverInfo"]["name"]
        )

        tools_list_response = json.loads(lines[1])
        self.assertEqual(2, tools_list_response["id"])
        tool_names = [tool["name"] for tool in tools_list_response["result"]["tools"]]
        self.assertEqual(
            [
                "get_tags_for_series_categories",
                "get_categories",
                "get_tags_for_series_category",
                "get_series_list",
            ],
            tool_names,
        )

        tools_call_response = json.loads(lines[2])
        self.assertEqual(3, tools_call_response["id"])
        self.assertEqual(False, tools_call_response["result"]["isError"])
        self.assertEqual(
            {"tags_by_categories": {"Politics": ["Trump", "Biden"]}},
            tools_call_response["result"]["structuredContent"],
        )

        tools_call_by_category_response = json.loads(lines[3])
        self.assertEqual(4, tools_call_by_category_response["id"])
        self.assertEqual(False, tools_call_by_category_response["result"]["isError"])
        self.assertEqual(
            {"category": "Politics", "tags": ["Trump", "Biden"]},
            tools_call_by_category_response["result"]["structuredContent"],
        )

        tools_call_series_response = json.loads(lines[4])
        self.assertEqual(5, tools_call_series_response["id"])
        self.assertEqual(False, tools_call_series_response["result"]["isError"])
        self.assertEqual(
            "KXBTCUSD",
            tools_call_series_response["result"]["structuredContent"]["series"][0]["ticker"],
        )

    def test_parse_error(self) -> None:
        registry = ToolRegistry({})
        stdin = io.StringIO("{not_json}\n")
        stdout = io.StringIO()

        server = StdioMCPServer(registry, stdin=stdin, stdout=stdout)
        server.run()

        line = stdout.getvalue().strip()
        response = json.loads(line)
        self.assertEqual(-32700, response["error"]["code"])


if __name__ == "__main__":
    unittest.main()
