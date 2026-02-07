"""Application-level use cases."""

from .kalshi_client import KalshiClient
from .models import TagsByCategories


class MetadataService:
    def __init__(self, client: KalshiClient) -> None:
        self._client = client

    def get_tags_for_series_categories(self) -> TagsByCategories:
        return self._client.get_tags_for_series_categories()

    def get_categories(self) -> list[str]:
        tags_by_categories = self.get_tags_for_series_categories().tags_by_categories
        return sorted(tags_by_categories.keys())

    def get_tags_for_series_category(self, category: str) -> list[str]:
        normalized_category = category.strip()
        if not normalized_category:
            raise ValueError("category must be a non-empty string.")

        tags_by_categories = self.get_tags_for_series_categories().tags_by_categories
        if normalized_category not in tags_by_categories:
            raise ValueError(f"Unknown category: {normalized_category}")

        return tags_by_categories[normalized_category]
