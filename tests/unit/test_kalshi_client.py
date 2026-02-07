import json
import unittest
from unittest.mock import patch

from kalshi_mcp.kalshi_client import KalshiClient, KalshiClientError
from kalshi_mcp.settings import Settings


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body.encode("utf-8")


class KalshiClientTests(unittest.TestCase):
    def test_get_tags_for_series_categories_success(self) -> None:
        payload = {
            "tags_by_categories": {
                "Politics": ["Trump", "Biden"],
                "Economy": ["Inflation"],
            }
        }
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen:
            result = client.get_tags_for_series_categories()

        self.assertEqual(payload["tags_by_categories"], result.tags_by_categories)
        request_obj = mocked_urlopen.call_args.args[0]
        self.assertTrue(request_obj.get_full_url().endswith("/search/tags_by_categories"))

    def test_get_tags_for_series_categories_missing_payload_key_raises(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ):
            with self.assertRaises(KalshiClientError):
                client.get_tags_for_series_categories()


if __name__ == "__main__":
    unittest.main()
