"""Shared data models used across the server."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Market:
    id: str
    title: str
    status: str


@dataclass
class Order:
    id: str
    market_id: str
    side: str
    quantity: int
    price: Optional[int] = None


@dataclass
class TagsByCategories:
    tags_by_categories: dict[str, list[str]]
