"""Application-level use cases."""

from typing import Iterable

from .kalshi_client import KalshiClient
from .models import Market


class MarketService:
    def __init__(self, client: KalshiClient) -> None:
        self._client = client

    def list_markets(self) -> Iterable[Market]:
        # TODO: Implement using client
        return []
