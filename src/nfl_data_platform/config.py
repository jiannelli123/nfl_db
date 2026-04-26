"""Configuration helpers for the NFL data platform."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    environment: str
    database_url: str
    nflverse_seasons: tuple[int, ...]
    nflverse_data_dir: Path
    temp_data_dir: Path


def _parse_seasons(raw_value: str) -> tuple[int, ...]:
    """Parse a comma-separated season list into a tuple of integers."""
    values = [value.strip() for value in raw_value.split(",") if value.strip()]
    if not values:
        raise ValueError("NFLVERSE_SEASONS must contain at least one season.")
    return tuple(int(value) for value in values)


def get_settings() -> Settings:
    """Load and validate runtime settings from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is required.")

    seasons_raw = os.getenv("NFLVERSE_SEASONS", "2025")
    data_dir = os.getenv("NFLVERSE_DATA_DIR", "./data/nflverse")
    temp_data_dir = os.getenv("TEMP_DATA_DIR", "./data/temp")

    return Settings(
        environment=os.getenv("NFL_DATA_PLATFORM_ENV", "local"),
        database_url=database_url,
        nflverse_seasons=_parse_seasons(seasons_raw),
        nflverse_data_dir=Path(data_dir),
        temp_data_dir=Path(temp_data_dir),
    )
