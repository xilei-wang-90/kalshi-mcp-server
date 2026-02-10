#!/usr/bin/env python3
"""
Export Kalshi market title/subtitle/yes/no subtitles for all OPEN markets in a category.

This bypasses MCP tool-call timeouts by running pagination locally.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from typing import Iterable

from kalshi_mcp.kalshi_client import KalshiClient
from kalshi_mcp.services import MetadataService
from kalshi_mcp.settings import load_settings


def _iter_series_tickers(
    svc: MetadataService,
    *,
    category: str,
    tags: str | None,
    limit: int,
    max_pages: int,
) -> Iterable[str]:
    cursor: str | None = None
    seen_cursors: set[str] = set()
    seen_tickers: set[str] = set()

    pages = 0
    while pages < max_pages:
        series_list = svc.get_series_list(
            category=category,
            tags=tags,
            cursor=cursor,
            limit=limit,
            include_product_metadata=False,
            include_volume=False,
        )

        for s in series_list.series:
            if s.ticker not in seen_tickers:
                seen_tickers.add(s.ticker)
                yield s.ticker

        pages += 1
        if series_list.cursor is None:
            return

        if series_list.cursor in seen_cursors:
            raise RuntimeError("Kalshi /series cursor repeated; aborting pagination.")
        seen_cursors.add(series_list.cursor)
        cursor = series_list.cursor

    raise RuntimeError(f"Exceeded max_pages while paging /series (max_pages={max_pages}).")


def _iter_open_markets(
    svc: MetadataService,
    *,
    series_ticker: str,
    limit: int,
    max_pages: int,
):
    cursor: str | None = None
    seen_cursors: set[str] = set()
    pages = 0

    while pages < max_pages:
        markets_list = svc.get_markets(
            cursor=cursor,
            limit=limit,
            series_ticker=series_ticker,
            status="open",
        )
        for m in markets_list.markets:
            yield m

        pages += 1
        if markets_list.cursor is None:
            return

        if markets_list.cursor in seen_cursors:
            raise RuntimeError(
                f"Kalshi /markets cursor repeated for series {series_ticker}; aborting pagination."
            )
        seen_cursors.add(markets_list.cursor)
        cursor = markets_list.cursor

    raise RuntimeError(
        f"Exceeded max_pages while paging /markets for series {series_ticker} (max_pages={max_pages})."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="Crypto", help="Kalshi category name (default: Crypto)")
    parser.add_argument("--tags", default=None, help="Optional tags filter (string)")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable warnings/logging from the Kalshi client (default: off).",
    )
    parser.add_argument(
        "--series-limit",
        type=int,
        default=1000,
        help="Page size for /series (1-1000). Default: 1000",
    )
    parser.add_argument(
        "--series-max-pages",
        type=int,
        default=10000,
        help="Safety cap for /series pages. Default: 10000",
    )
    parser.add_argument(
        "--markets-limit",
        type=int,
        default=1000,
        help="Page size for /markets (1-1000). Default: 1000",
    )
    parser.add_argument(
        "--markets-max-pages",
        type=int,
        default=10000,
        help="Safety cap for /markets pages per series. Default: 10000",
    )
    parser.add_argument(
        "--out",
        default="out/kalshi_crypto_open_market_titles.csv",
        help="Output CSV path. Default: out/kalshi_crypto_open_market_titles.csv",
    )
    args = parser.parse_args()

    if not args.verbose:
        # The client is intentionally strict about schema and logs a lot of warnings for
        # fields we don't care about in this export.
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("kalshi_mcp").setLevel(logging.ERROR)

    settings = load_settings()
    client = KalshiClient(settings)
    svc = MetadataService(client)

    out_path = args.out
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        "category",
        "series_ticker",
        "ticker",
        "title",
        "subtitle",
        "yes_sub_title",
        "no_sub_title",
    ]

    series_count = 0
    market_count = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for series_ticker in _iter_series_tickers(
            svc,
            category=args.category,
            tags=args.tags,
            limit=args.series_limit,
            max_pages=args.series_max_pages,
        ):
            series_count += 1
            for m in _iter_open_markets(
                svc,
                series_ticker=series_ticker,
                limit=args.markets_limit,
                max_pages=args.markets_max_pages,
            ):
                market_count += 1
                w.writerow(
                    {
                        "category": args.category,
                        "series_ticker": series_ticker,
                        "ticker": m.ticker,
                        "title": m.title,
                        "subtitle": m.subtitle,
                        "yes_sub_title": m.yes_sub_title,
                        "no_sub_title": m.no_sub_title,
                    }
                )

    meta = {
        "base_url": settings.base_url,
        "timeout_seconds": settings.timeout_seconds,
        "category": args.category,
        "tags": args.tags,
        "series_count": series_count,
        "market_count": market_count,
        "out": out_path,
    }

    # Keep stdout small; write metadata as a single line.
    sys.stdout.write(str(meta) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
