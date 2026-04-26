"""Tests for engine helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from nfl_data_platform.config import Settings
from nfl_data_platform.db.engine import _normalize_sql_for_dialect, create_engine_from_settings, validate_database_url


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

    manager = create_engine_from_settings(settings)

    assert isinstance(manager.engine, Engine)


def test_apply_ddl_directory_creates_expected_tables() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=Path("./data/temp"),
    )

    manager = create_engine_from_settings(settings)
    result = manager.apply_ddl_directory("sql/ddl")
    inspector = inspect(manager.engine)

    assert "dim_team" in inspector.get_table_names()
    assert "fact_game_pbp" in inspector.get_table_names()
    assert "etl_run_log" in inspector.get_table_names()
    assert "dim_team.sql" in result["executed_files"]


def test_normalize_sql_for_dialect_translates_postgres_to_sqlite() -> None:
    sql = (
        "CREATE TABLE foo ("
        "  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),"
        "  price NUMERIC(10, 2),"
        "  is_active BOOLEAN"
        ")"
    )
    result = _normalize_sql_for_dialect(sql, "sqlite")

    assert "TIMESTAMPTZ" not in result
    assert "TIMESTAMP" in result
    assert "NOW()" not in result
    assert "CURRENT_TIMESTAMP" in result
    assert "NUMERIC(10, 2)" not in result
    assert "REAL" in result
    assert "BOOLEAN" not in result
    assert "INTEGER" in result


def test_normalize_sql_for_dialect_is_noop_for_postgresql() -> None:
    sql = "CREATE TABLE foo (created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
    result = _normalize_sql_for_dialect(sql, "postgresql")

    assert result == sql


def test_check_connection_returns_database_metadata() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=Path("./data/temp"),
    )

    manager = create_engine_from_settings(settings)
    status = manager.check_connection()

    assert status.status == "ok"
    assert status.dialect == "sqlite"
    assert status.database == ":memory:"
    assert status.server_version is not None
