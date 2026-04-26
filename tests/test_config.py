"""Tests for application settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from nfl_data_platform.config import get_settings


def test_get_settings_loads_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/test_db")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2023,2024")
    monkeypatch.setenv("NFLVERSE_DATA_DIR", "./data/custom")
    monkeypatch.setenv("NFL_DATA_PLATFORM_ENV", "test")

    settings = get_settings()

    assert settings.environment == "test"
    assert settings.database_url.endswith("/test_db")
    assert settings.nflverse_seasons == (2023, 2024)
    assert settings.nflverse_data_dir == Path("./data/custom")
    assert settings.temp_data_dir == Path("./data/temp")


def test_get_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")

    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        get_settings()
