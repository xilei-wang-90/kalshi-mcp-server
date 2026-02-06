"""Configuration loading for the server."""

from dataclasses import dataclass


@dataclass
class Settings:
    """Runtime configuration loaded from environment or files."""
    # TODO: Add Kalshi API keys, environment, base URL, timeouts, etc.
    pass


def load_settings() -> Settings:
    """Load settings from environment or config files."""
    # TODO: Implement settings loading.
    return Settings()
