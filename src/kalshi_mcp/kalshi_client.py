"""Adapter for kalshi_python_sync client."""

from typing import Iterable

from .models import Market


class KalshiClient:
    def __init__(self) -> None:
        # TODO: Initialize kalshi_python_sync client
        pass

    def list_markets(self) -> Iterable[Market]:
        # TODO: Call kalshi_python_sync and map to Market
        return []
