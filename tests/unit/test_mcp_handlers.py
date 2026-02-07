import unittest

from kalshi_mcp.mcp.handlers import handle_get_tags_for_series_categories
from kalshi_mcp.models import TagsByCategories


class _FakeMetadataService:
    def get_tags_for_series_categories(self) -> TagsByCategories:
        return TagsByCategories(tags_by_categories={"Politics": ["Trump", "Biden"]})


class HandlersTests(unittest.TestCase):
    def test_get_tags_for_series_categories_handler(self) -> None:
        result = handle_get_tags_for_series_categories(_FakeMetadataService(), None)
        self.assertEqual(
            result,
            {"tags_by_categories": {"Politics": ["Trump", "Biden"]}},
        )

    def test_get_tags_for_series_categories_rejects_arguments(self) -> None:
        with self.assertRaises(ValueError):
            handle_get_tags_for_series_categories(_FakeMetadataService(), {"unexpected": True})


if __name__ == "__main__":
    unittest.main()
