import json
import unittest
from unittest.mock import patch

from kalshi_mcp.kalshi_client import KalshiClient, KalshiClientError
from kalshi_mcp.models import CreateOrderParams
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


def _make_client() -> KalshiClient:
    settings = Settings(
        base_url="https://api.elections.kalshi.com/trade-api/v2",
        timeout_seconds=5,
        api_key_id="test-key-id",
        api_key_path="/tmp/test-key.pem",
    )
    return KalshiClient(settings)


def _sample_order_response() -> dict:
    return {
        "order": {
            "order_id": "order-abc-123",
            "user_id": "user-1",
            "client_order_id": "my-client-id",
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
    }


class CreateOrderTests(unittest.TestCase):
    def test_create_order_success_required_fields_only(self) -> None:
        payload = _sample_order_response()
        client = _make_client()
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ), patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            result = client.create_order(params)

        self.assertEqual("order-abc-123", result.order_id)
        self.assertEqual("KXBTCUSD-26JAN01-T1", result.ticker)
        self.assertEqual("yes", result.side)
        self.assertEqual("buy", result.action)
        self.assertEqual(51, result.yes_price)
        self.assertEqual("0.51", result.yes_price_dollars)
        self.assertEqual(0, result.subaccount_number)

        request_obj = mocked_urlopen.call_args.args[0]
        self.assertEqual("POST", request_obj.get_method())
        self.assertTrue(request_obj.get_full_url().endswith("/portfolio/orders"))

        sent_body = json.loads(request_obj.data.decode("utf-8"))
        self.assertEqual("KXBTCUSD-26JAN01-T1", sent_body["ticker"])
        self.assertEqual("yes", sent_body["side"])
        self.assertEqual("buy", sent_body["action"])
        # Optional fields should not be present
        self.assertNotIn("count", sent_body)
        self.assertNotIn("yes_price", sent_body)
        self.assertNotIn("post_only", sent_body)

    def test_create_order_success_with_optional_fields(self) -> None:
        payload = _sample_order_response()
        client = _make_client()
        params = CreateOrderParams(
            ticker="KXBTCUSD-26JAN01-T1",
            side="yes",
            action="buy",
            client_order_id="my-client-id",
            count=10,
            yes_price=51,
            time_in_force="good_till_canceled",
            post_only=True,
            subaccount=0,
        )

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ), patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            result = client.create_order(params)

        self.assertEqual("order-abc-123", result.order_id)

        request_obj = mocked_urlopen.call_args.args[0]
        sent_body = json.loads(request_obj.data.decode("utf-8"))
        self.assertEqual("KXBTCUSD-26JAN01-T1", sent_body["ticker"])
        self.assertEqual("yes", sent_body["side"])
        self.assertEqual("buy", sent_body["action"])
        self.assertEqual("my-client-id", sent_body["client_order_id"])
        self.assertEqual(10, sent_body["count"])
        self.assertEqual(51, sent_body["yes_price"])
        self.assertEqual("good_till_canceled", sent_body["time_in_force"])
        self.assertTrue(sent_body["post_only"])
        self.assertEqual(0, sent_body["subaccount"])

    def test_create_order_sends_auth_headers(self) -> None:
        payload = _sample_order_response()
        client = _make_client()
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

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
            client.create_order(params)

        mocked_sign.assert_called_once_with("1700000000123POST/trade-api/v2/portfolio/orders")

        request_obj = mocked_urlopen.call_args.args[0]
        header_items = {key.lower(): value for key, value in request_obj.header_items()}
        self.assertEqual("application/json", header_items["accept"])
        self.assertEqual("application/json", header_items["content-type"])
        self.assertEqual("test-key-id", header_items["kalshi-access-key"])
        self.assertEqual("signed-message", header_items["kalshi-access-signature"])
        self.assertEqual("1700000000123", header_items["kalshi-access-timestamp"])

    def test_create_order_without_api_credentials_raises(self) -> None:
        settings = Settings(
            base_url="https://api.elections.kalshi.com/trade-api/v2",
            timeout_seconds=5,
        )
        client = KalshiClient(settings)
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

        with self.assertRaises(KalshiClientError):
            client.create_order(params)

    def test_create_order_missing_order_key_raises_and_logs(self) -> None:
        client = _make_client()
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps({"foo": "bar"})),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR") as captured:
                with self.assertRaises(KalshiClientError):
                    client.create_order(params)

        self.assertTrue(
            any("expected object at 'order'" in message for message in captured.output)
        )

    def test_create_order_malformed_order_object_raises(self) -> None:
        # Response has "order" key but the inner object is missing required fields
        payload = {"order": {"order_id": "order-1"}}
        client = _make_client()
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="WARNING"):
                with self.assertRaises(KalshiClientError):
                    client.create_order(params)

    def test_create_order_order_key_is_not_dict_raises(self) -> None:
        payload = {"order": "not-a-dict"}
        client = _make_client()
        params = CreateOrderParams(ticker="KXBTCUSD-26JAN01-T1", side="yes", action="buy")

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ), patch.object(client, "_sign_message", return_value="signed"):
            with self.assertLogs("kalshi_mcp.kalshi_client", level="ERROR"):
                with self.assertRaises(KalshiClientError):
                    client.create_order(params)

    def test_create_order_all_optional_fields_in_body(self) -> None:
        payload = _sample_order_response()
        client = _make_client()
        params = CreateOrderParams(
            ticker="KXBTCUSD-26JAN01-T1",
            side="no",
            action="sell",
            client_order_id="cid-1",
            count=5,
            count_fp="5.0000",
            yes_price=60,
            no_price=40,
            yes_price_dollars="0.60",
            no_price_dollars="0.40",
            expiration_ts=1700001000,
            time_in_force="fill_or_kill",
            buy_max_cost=500,
            sell_position_floor=0,
            post_only=False,
            reduce_only=True,
            self_trade_prevention_type="taker_at_cross",
            order_group_id="group-1",
            cancel_order_on_pause=True,
            subaccount=2,
        )

        with patch(
            "kalshi_mcp.kalshi_client.request.urlopen",
            return_value=_FakeResponse(json.dumps(payload)),
        ) as mocked_urlopen, patch.object(
            client,
            "_sign_message",
            return_value="signed-message",
        ), patch(
            "kalshi_mcp.kalshi_client.time.time",
            return_value=1700000000.123,
        ):
            client.create_order(params)

        request_obj = mocked_urlopen.call_args.args[0]
        sent_body = json.loads(request_obj.data.decode("utf-8"))
        self.assertEqual("KXBTCUSD-26JAN01-T1", sent_body["ticker"])
        self.assertEqual("no", sent_body["side"])
        self.assertEqual("sell", sent_body["action"])
        self.assertEqual("cid-1", sent_body["client_order_id"])
        self.assertEqual(5, sent_body["count"])
        self.assertEqual("5.0000", sent_body["count_fp"])
        self.assertEqual(60, sent_body["yes_price"])
        self.assertEqual(40, sent_body["no_price"])
        self.assertEqual("0.60", sent_body["yes_price_dollars"])
        self.assertEqual("0.40", sent_body["no_price_dollars"])
        self.assertEqual(1700001000, sent_body["expiration_ts"])
        self.assertEqual("fill_or_kill", sent_body["time_in_force"])
        self.assertEqual(500, sent_body["buy_max_cost"])
        self.assertEqual(0, sent_body["sell_position_floor"])
        self.assertFalse(sent_body["post_only"])
        self.assertTrue(sent_body["reduce_only"])
        self.assertEqual("taker_at_cross", sent_body["self_trade_prevention_type"])
        self.assertEqual("group-1", sent_body["order_group_id"])
        self.assertTrue(sent_body["cancel_order_on_pause"])
        self.assertEqual(2, sent_body["subaccount"])


if __name__ == "__main__":
    unittest.main()
