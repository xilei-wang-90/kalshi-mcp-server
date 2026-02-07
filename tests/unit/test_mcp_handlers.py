import unittest

from kalshi_mcp.mcp.handlers import (
    handle_get_categories,
    handle_get_tags_for_series_categories,
    handle_get_tags_for_series_category,
)
from kalshi_mcp.models import TagsByCategories


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


if __name__ == "__main__":
    unittest.main()
