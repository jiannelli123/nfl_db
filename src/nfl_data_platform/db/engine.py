"""SQLAlchemy engine utilities."""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from nfl_data_platform.config import Settings


@dataclass(slots=True)
class DatabaseConnectionStatus:
    """Summary of a database connectivity check."""

    status: str
    driver: str
    dialect: str
    database: str | None
    server_version: str | None


class DatabaseManager:
    """Small wrapper around a SQLAlchemy engine with DDL helpers."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def apply_ddl_directory(self, ddl_directory: str | Path) -> dict[str, list[str]]:
        """Execute every SQL file in a DDL directory in filename order."""
        ddl_path = Path(ddl_directory)
        executed_files: list[str] = []
        with self.engine.begin() as connection:
            for path in sorted(ddl_path.glob("*.sql")):
                sql_text = path.read_text(encoding="utf-8")
                normalized_sql = _normalize_sql_for_dialect(
                    sql_text=sql_text,
                    dialect_name=connection.dialect.name,
                )
                for statement in _split_sql_statements(normalized_sql):
                    connection.exec_driver_sql(statement)
                executed_files.append(path.name)
        return {"executed_files": executed_files}

    def check_connection(self) -> DatabaseConnectionStatus:
        """Verify connectivity and return basic database identity details."""
        with self.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
            server_version = _fetch_server_version(connection)
        return DatabaseConnectionStatus(
            status="ok",
            driver=self.engine.url.drivername,
            dialect=self.engine.dialect.name,
            database=self.engine.url.database,
            server_version=server_version,
        )


def validate_database_url(database_url: str) -> None:
    """Validate that a database URL is present and looks usable."""
    if not database_url:
        raise ValueError("DATABASE_URL is required.")
    if "://" not in database_url:
        raise ValueError("DATABASE_URL must be a valid SQLAlchemy connection URL.")


def create_engine_from_settings(settings: Settings) -> DatabaseManager:
    """Create a database manager from validated application settings."""
    validate_database_url(settings.database_url)
    return DatabaseManager(create_engine(settings.database_url, future=True))


@contextmanager
def get_connection(engine: Engine) -> Iterator[Connection]:
    """Provide a managed database connection."""
    with engine.connect() as connection:
        yield connection


def _split_sql_statements(sql_text: str) -> list[str]:
    """Split a SQL file into executable statements."""
    return [statement.strip() for statement in sql_text.split(";") if statement.strip()]


def _normalize_sql_for_dialect(sql_text: str, dialect_name: str) -> str:
    """Translate a subset of Postgres-flavored DDL for SQLite test runs."""
    if dialect_name != "sqlite":
        return sql_text

    normalized = sql_text.replace("TIMESTAMPTZ", "TIMESTAMP")
    normalized = normalized.replace("NOW()", "CURRENT_TIMESTAMP")
    normalized = re.sub(r"NUMERIC\(\d+,\s*\d+\)", "REAL", normalized)
    normalized = normalized.replace("BOOLEAN", "INTEGER")
    return normalized


def _fetch_server_version(connection: Connection) -> str | None:
    """Fetch a human-readable server version when the dialect supports it."""
    if connection.dialect.name == "sqlite":
        version = connection.exec_driver_sql("SELECT sqlite_version()").scalar_one()
        return str(version)
    if connection.dialect.name == "postgresql":
        version = connection.exec_driver_sql("SELECT version()").scalar_one()
        return str(version)
    return None
