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


@dataclass
class SettlementSource:
    name: str
    url: str


@dataclass
class Series:
    ticker: str
    frequency: str
    title: str
    category: str
    tags: list[str]
    settlement_sources: list[SettlementSource]
    contract_url: str
    contract_terms_url: str
    fee_type: str
    fee_multiplier: float
    additional_prohibitions: list[str]
    product_metadata: dict[str, object] | None = None
    volume: int | None = None
    volume_fp: str | None = None


@dataclass
class SeriesList:
    series: list[Series]
    cursor: str | None = None
