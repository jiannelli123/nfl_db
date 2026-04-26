"""Tests for engine helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.engine import Engine

from nfl_data_platform.config import Settings
from nfl_data_platform.db.engine import create_engine_from_settings, validate_database_url


def test_validate_database_url_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="valid SQLAlchemy connection URL"):
        validate_database_url("not-a-url")


def test_create_engine_from_settings_returns_engine() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=Path("./data/temp"),
    )

    engine = create_engine_from_settings(settings)

    assert isinstance(engine, Engine)
