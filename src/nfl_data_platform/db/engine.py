"""SQLAlchemy engine utilities."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from nfl_data_platform.config import Settings


def validate_database_url(database_url: str) -> None:
    """Validate that a database URL is present and looks usable."""
    if not database_url:
        raise ValueError("DATABASE_URL is required.")
    if "://" not in database_url:
        raise ValueError("DATABASE_URL must be a valid SQLAlchemy connection URL.")


def create_engine_from_settings(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine from validated application settings."""
    validate_database_url(settings.database_url)
    return create_engine(settings.database_url, future=True)


@contextmanager
def get_connection(engine: Engine) -> Iterator[Connection]:
    """Provide a managed database connection."""
    with engine.connect() as connection:
        yield connection
