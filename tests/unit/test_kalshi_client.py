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
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR"):
                with self.assertRaises(KalshiClientError):
                    client.get_tags_for_series_categories()

    def test_get_series_list_success(self) -> None:
        payload = {
            "series": [
                {
                    "ticker": "KXBTCUSD",
                    "frequency": "daily",
                    "title": "Will Bitcoin close above 100k?",
                    "category": "Crypto",
                    "tags": ["BTC", "Price"],
                    "settlement_sources": [
                        {"name": "Kalshi", "url": "https://kalshi.com/rules"}
                    ],
                    "contract_url": "https://kalshi.com/series/KXBTCUSD",
                    "contract_terms_url": "https://kalshi.com/terms/KXBTCUSD",
                    "fee_type": "linear",
                    "fee_multiplier": 1.0,
                    "additional_prohibitions": [],
                }
            ],
            "cursor": "next-page",
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
            result = client.get_series_list(
                category="Crypto",
                tags="BTC",
                include_product_metadata=True,
                include_volume=True,
            )

        self.assertEqual(1, len(result.series))
        first = result.series[0]
        self.assertEqual("KXBTCUSD", first.ticker)
        self.assertEqual("Crypto", first.category)
        self.assertEqual("linear", first.fee_type)
        self.assertEqual(1.0, first.fee_multiplier)
        self.assertEqual("next-page", result.cursor)

        request_obj = mocked_urlopen.call_args.args[0]
        full_url = request_obj.get_full_url()
        self.assertIn("/series?", full_url)
        self.assertIn("category=Crypto", full_url)
        self.assertIn("tags=BTC", full_url)
        self.assertIn("include_product_metadata=true", full_url)
        self.assertIn("include_volume=true", full_url)

    def test_get_series_list_missing_payload_key_raises_and_logs(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR") as captured:
                with self.assertRaises(KalshiClientError):
                    client.get_series_list()

        self.assertTrue(any("expected list at 'series'" in message for message in captured.output))

    def test_get_series_list_allows_null_tags_and_additional_prohibitions(self) -> None:
        payload = {
            "series": [
                {
                    "ticker": "KXUSDTMIN",
                    "frequency": "one_off",
                    "title": "USDT de-peg",
                    "category": "Crypto",
                    "tags": None,
                    "settlement_sources": [
                        {"name": "CF Benchmarks", "url": "https://www.cfbenchmarks.com/"}
                    ],
                    "contract_url": "https://kalshi.com/series/KXUSDTMIN",
                    "contract_terms_url": "https://kalshi.com/terms/KXUSDTMIN",
                    "fee_type": "quadratic",
                    "fee_multiplier": 1,
                    "additional_prohibitions": None,
                }
            ]
        }
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ):
            result = client.get_series_list(category="Crypto")

        self.assertEqual(1, len(result.series))
        first = result.series[0]
        self.assertIsNone(first.tags)
        self.assertIsNone(first.additional_prohibitions)


if __name__ == "__main__":
    unittest.main()
