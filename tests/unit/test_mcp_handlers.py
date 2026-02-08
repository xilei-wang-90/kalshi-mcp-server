import unittest

from kalshi_mcp.mcp.handlers import (
    handle_get_series_list,
    handle_get_categories,
    handle_get_tags_for_series_categories,
    handle_get_tags_for_series_category,
)
from kalshi_mcp.models import Series, SeriesList, SettlementSource, TagsByCategories


class _FakeMetadataService:
    def get_tags_for_series_categories(self) -> TagsByCategories:
        return TagsByCategories(
            tags_by_categories={
                "Politics": ["Trump", "Biden"],
                "Crypto": ["BTC", "ETH"],
            }
        )

    def get_categories(self) -> list[str]:
        return ["Crypto", "Politics"]

    def get_tags_for_series_category(self, category: str) -> list[str]:
        if category == "Crypto":
            return ["BTC", "ETH"]
        raise ValueError(f"Unknown category: {category}")

    def get_series_list(
        self,
        category: str | None = None,
        tags: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        include_product_metadata: bool = False,
        include_volume: bool = False,
    ) -> SeriesList:
        _ = include_product_metadata
        _ = include_volume
        _ = cursor
        _ = limit
        if category == "Crypto" and tags == "BTC":
            return SeriesList(
                series=[
                    Series(
                        ticker="KXBTCUSD",
                        frequency="daily",
                        title="Will Bitcoin close above 100k?",
                        category="Crypto",
                        tags=["BTC"],
                        settlement_sources=[
                            SettlementSource(
                                name="Kalshi Rules", url="https://kalshi.com/rules"
                            )
                        ],
                        contract_url="https://kalshi.com/series/KXBTCUSD",
                        contract_terms_url="https://kalshi.com/terms/KXBTCUSD",
                        fee_type="linear",
                        fee_multiplier=1.0,
                        additional_prohibitions=[],
                    )
                ],
                cursor="next-page",
            )
        return SeriesList(series=[], cursor=None)


class HandlersTests(unittest.TestCase):
    def test_get_tags_for_series_categories_handler(self) -> None:
        result = handle_get_tags_for_series_categories(_FakeMetadataService(), None)
        self.assertEqual(
            result,
            {"tags_by_categories": {"Politics": ["Trump", "Biden"], "Crypto": ["BTC", "ETH"]}},
        )

    def test_get_tags_for_series_categories_rejects_arguments(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_tags_for_series_categories(_FakeMetadataService(), {"unexpected": True})

    def test_get_categories_handler(self) -> None:
        result = handle_get_categories(_FakeMetadataService(), None)
        self.assertEqual({"categories": ["Crypto", "Politics"]}, result)

    def test_get_categories_rejects_arguments(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_categories(_FakeMetadataService(), {"unexpected": True})

    def test_get_tags_for_series_category_handler(self) -> None:
        result = handle_get_tags_for_series_category(
            _FakeMetadataService(), {"category": "Crypto"}
        )
        self.assertEqual({"category": "Crypto", "tags": ["BTC", "ETH"]}, result)

    def test_get_tags_for_series_category_requires_arguments(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_tags_for_series_category(_FakeMetadataService(), None)

    def test_get_tags_for_series_category_requires_string_category(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_tags_for_series_category(_FakeMetadataService(), {"category": 123})

    def test_get_series_list_handler(self) -> None:
        result = handle_get_series_list(
            _FakeMetadataService(),
            {
                "category": "Crypto",
                "tags": "BTC",
                "include_product_metadata": True,
                "include_volume": True,
            },
        )
        self.assertEqual(1, len(result["series"]))
        self.assertEqual("KXBTCUSD", result["series"][0]["ticker"])
        self.assertEqual("next-page", result["cursor"])

    def test_get_series_list_rejects_invalid_types(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_series_list(_FakeMetadataService(), {"include_volume": "yes"})

    def test_get_series_list_rejects_invalid_limit(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_series_list(_FakeMetadataService(), {"limit": 0})


if __name__ == "__main__":
    unittest.main()
