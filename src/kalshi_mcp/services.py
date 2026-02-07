"""Application-level use cases."""

from .kalshi_client import KalshiClient
from .models import TagsByCategories


class MetadataService:
    def __init__(self, client: KalshiClient) -> None:
        self._client = client

    def get_tags_for_series_categories(self) -> TagsByCategories:
        return self._client.get_tags_for_series_categories()
