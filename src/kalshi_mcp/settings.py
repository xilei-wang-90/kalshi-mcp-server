"""Configuration loading for the server."""

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Runtime configuration loaded from environment or files."""
    base_url: str
    timeout_seconds: float


def load_settings() -> Settings:
    """Load settings from environment or config files."""
    default_base_url = "https://api.elections.kalshi.com/trade-api/v2"
    base_url = os.getenv("KALSHI_API_BASE_URL", default_base_url).strip().rstrip("/")

    raw_timeout = os.getenv("KALSHI_TIMEOUT_SECONDS", "10")
    try:
        timeout_seconds = float(raw_timeout)
    except ValueError:
        timeout_seconds = 10.0

    if timeout_seconds <= 0:
        timeout_seconds = 10.0

    return Settings(base_url=base_url, timeout_seconds=timeout_seconds)
