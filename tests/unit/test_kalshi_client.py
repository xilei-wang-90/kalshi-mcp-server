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

    def test_get_markets_success(self) -> None:
        payload = {
            "markets": [
                {
                    "ticker": "TRUMPWIN-26NOV-T2",
                    "event_ticker": "TRUMPWIN-26NOV",
                    "market_type": "binary",
                    "title": "Will Trump win the 2024 election?",
                    "subtitle": "Trump Wins",
                    "status": "initialized",
                    "tick_size": 1,
                    "floor_strike": 78999.99,
                    "cap_strike": 79999.99,
                    "price_ranges": [{"start": "0", "end": "0.2", "step": "0.01"}],
                    "mve_selected_legs": [
                        {
                            "event_ticker": "TRUMPWIN-26NOV",
                            "market_ticker": "TRUMPWIN-26NOV-T2",
                            "side": "yes",
                            "yes_settlement_value_dollars": "0",
                        }
                    ],
                    "custom_strike": {},
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
        ) as mocked_urlopen, patch("kalshi_mcp.kalshi_client.LOGGER.warning") as mocked_warn:
            result = client.get_markets(
                limit=5,
                status="open",
                event_ticker="TRUMPWIN-26NOV",
                min_close_ts=1700000000,
            )

        self.assertEqual(1, len(result.markets))
        first = result.markets[0]
        self.assertEqual("TRUMPWIN-26NOV-T2", first.ticker)
        self.assertEqual("TRUMPWIN-26NOV", first.event_ticker)
        self.assertEqual("binary", first.market_type)
        self.assertEqual("initialized", first.status)
        self.assertEqual(1, first.tick_size)
        self.assertEqual(78999.99, first.floor_strike)
        self.assertEqual(79999.99, first.cap_strike)
        self.assertEqual("next-page", result.cursor)
        self.assertIsNotNone(first.price_ranges)
        self.assertEqual("0.01", first.price_ranges[0].step)
        self.assertIsNotNone(first.mve_selected_legs)
        self.assertEqual("yes", first.mve_selected_legs[0].side)
        mocked_warn.assert_not_called()

        request_obj = mocked_urlopen.call_args.args[0]
        full_url = request_obj.get_full_url()
        self.assertIn("/markets?", full_url)
        self.assertIn("limit=5", full_url)
        self.assertIn("status=open", full_url)
        self.assertIn("event_ticker=TRUMPWIN-26NOV", full_url)
        self.assertIn("min_close_ts=1700000000", full_url)

    def test_get_markets_missing_payload_key_raises_and_logs(self) -> None:
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
                    client.get_markets()

        self.assertTrue(any("expected list at 'markets'" in message for message in captured.output))

    def test_get_balance_success(self) -> None:
        payload = {
            "balance": 1000,
            "portfolio_value": 2500,
            "updated_ts": 1735000000123,
        }
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ) as mocked_sign, patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            result = client.get_balance()

        self.assertEqual(1000, result.balance)
        self.assertEqual(2500, result.portfolio_value)
        self.assertEqual(1735000000123, result.updated_ts)
        mocked_sign.assert_called_once_with("1700000000123GET/trade-api/v2/portfolio/balance")

        request_obj = mocked_urlopen.call_args.args[0]
        header_items = {key.lower(): value for key, value in request_obj.header_items()}
        self.assertEqual("application/json", header_items["accept"])
        self.assertEqual("test-key-id", header_items["kalshi-access-key"])
        self.assertEqual("signed-message", header_items["kalshi-access-signature"])
        self.assertEqual("1700000000123", header_items["kalshi-access-timestamp"])

    def test_get_balance_without_api_credentials_raises(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with self.assertRaises(KalshiClientError):
            client.get_balance()

    def test_get_balance_missing_fields_raises_and_logs(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR") as captured:
                with self.assertRaises(KalshiClientError):
                    client.get_balance()

        self.assertTrue(
            any("expected integer at 'balance'" in message for message in captured.output)
        )

    def test_get_subaccount_balances_success(self) -> None:
        payload = {
            "subaccount_balances": [
                {
                    "subaccount_number": 0,
                    "balance": "100.5600",
                    "updated_ts": 1735000000123,
                },
                {
                    "subaccount_number": 1,
                    "balance": "0.0000",
                    "updated_ts": 1735000000456,
                },
            ]
        }
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ) as mocked_sign, patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            result = client.get_subaccount_balances()

        self.assertEqual(2, len(result.subaccount_balances))
        first = result.subaccount_balances[0]
        self.assertEqual(0, first.subaccount_number)
        self.assertEqual("100.5600", first.balance)
        self.assertEqual(1735000000123, first.updated_ts)
        second = result.subaccount_balances[1]
        self.assertEqual(1, second.subaccount_number)
        self.assertEqual("0.0000", second.balance)
        self.assertEqual(1735000000456, second.updated_ts)

        mocked_sign.assert_called_once_with(
            "1700000000123GET/trade-api/v2/portfolio/subaccounts/balances"
        )

        request_obj = mocked_urlopen.call_args.args[0]
        full_url = request_obj.get_full_url()
        self.assertTrue(full_url.endswith("/portfolio/subaccounts/balances"))
        header_items = {key.lower(): value for key, value in request_obj.header_items()}
        self.assertEqual("application/json", header_items["accept"])
        self.assertEqual("test-key-id", header_items["kalshi-access-key"])
        self.assertEqual("signed-message", header_items["kalshi-access-signature"])
        self.assertEqual("1700000000123", header_items["kalshi-access-timestamp"])

    def test_get_subaccount_balances_without_api_credentials_raises(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)

        with self.assertRaises(KalshiClientError):
            client.get_subaccount_balances()

    def test_get_subaccount_balances_missing_payload_key_raises_and_logs(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR") as captured:
                with self.assertRaises(KalshiClientError):
                    client.get_subaccount_balances()

        self.assertTrue(
            any(
                "expected list at 'subaccount_balances'" in message
                for message in captured.output
            )
        )

    def test_get_orders_success(self) -> None:
        payload = {
            "orders": [
                {
                    "order_id": "order-1",
                    "user_id": "user-1",
                    "client_order_id": "client-1",
                    "ticker": "KXBTCUSD-26JAN01-T1",
                    "status": "resting",
                    "side": "yes",
                    "action": "buy",
                    "type": "limit",
                    "yes_price": 51,
                    "no_price": 49,
                    "fill_count": 0,
                    "remaining_count": 10,
                    "initial_count": 10,
                    "taker_fees": 0,
                    "maker_fees": 0,
                    "taker_fill_cost": 0,
                    "maker_fill_cost": 0,
                    "queue_position": 1,
                    "yes_price_dollars": "0.51",
                    "no_price_dollars": "0.49",
                    "fill_count_fp": "0.0000",
                    "remaining_count_fp": "10.0000",
                    "initial_count_fp": "10.0000",
                    "taker_fill_cost_dollars": "0.00",
                    "maker_fill_cost_dollars": "0.00",
                    "subaccount_number": 0,
                }
            ],
            "cursor": "next-page",
        }
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ) as mocked_sign, patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            result = client.get_orders(
                ticker="KXBTCUSD-26JAN01-T1",
                event_ticker="KXBTCUSD-26JAN01",
                min_ts=1700000000,
                max_ts=1700001000,
                status="resting",
                limit=10,
                cursor="c1",
                subaccount=0,
            )

        self.assertEqual(1, len(result.orders))
        first = result.orders[0]
        self.assertEqual("order-1", first.order_id)
        self.assertEqual(51, first.yes_price)
        self.assertEqual("0.51", first.yes_price_dollars)
        self.assertEqual(0, first.subaccount_number)
        self.assertEqual("next-page", result.cursor)

        request_obj = mocked_urlopen.call_args.args[0]
        full_url = request_obj.get_full_url()
        self.assertIn("/portfolio/orders?", full_url)
        self.assertIn("ticker=KXBTCUSD-26JAN01-T1", full_url)
        self.assertIn("event_ticker=KXBTCUSD-26JAN01", full_url)
        self.assertIn("min_ts=1700000000", full_url)
        self.assertIn("max_ts=1700001000", full_url)
        self.assertIn("status=resting", full_url)
        self.assertIn("limit=10", full_url)
        self.assertIn("cursor=c1", full_url)
        self.assertIn("subaccount=0", full_url)

        mocked_sign.assert_called_once()
        signed_message = mocked_sign.call_args.args[0]
        self.assertIn("GET/trade-api/v2/portfolio/orders", signed_message)

    def test_get_orders_missing_payload_key_raises_and_logs(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
            api_key_id="test-key-id",
            api_key_path="/tmp/test-key.pem",
        )
        client = KalshiClient(settings)

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR") as captured:
                with self.assertRaises(KalshiClientError):
                    client.get_orders()

        self.assertTrue(any("expected list at 'orders'" in message for message in captured.output))


if __name__ == "__main__":
    unittest.main()
