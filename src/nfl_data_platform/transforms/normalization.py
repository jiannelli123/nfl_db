"""Shared normalization helpers for nflverse-compatible transforms."""

from __future__ import annotations

import pandas as pd


def first_available_column(
    frame: pd.DataFrame,
    candidate_columns: list[str],
    default_value: object = pd.NA,
) -> pd.Series:
    """Return the first available non-null value across candidate columns."""
    if frame.empty:
        return pd.Series(dtype="object")
    result = pd.Series([pd.NA] * len(frame), index=frame.index, dtype="object")
    for column in candidate_columns:
        if column in frame.columns:
            result = result.where(result.notna(), frame[column])
    return result.fillna(default_value)


def normalize_team_values(series: pd.Series) -> pd.Series:
    """Normalize team identifiers to uppercase string abbreviations."""
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA})
        .str.upper()
    )


def normalize_player_values(series: pd.Series) -> pd.Series:
    """Normalize player identifiers to trimmed strings."""
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA})
    )


def resolve_team_column(frame: pd.DataFrame) -> pd.Series:
    """Resolve the best available team column from nflverse-style inputs."""
    return normalize_team_values(
        first_available_column(frame, ["team", "recent_team", "team_abbr", "club_code"])
    )


def resolve_player_name_column(frame: pd.DataFrame) -> pd.Series:
    """Resolve the best available player display name from nflverse-style inputs."""
    return first_available_column(frame, ["player_name", "full_name", "display_name", "player_id"])


def ensure_numeric_column(frame: pd.DataFrame, column: str, default_value: int | float = 0) -> pd.Series:
    """Return a numeric column with missing values filled to a default."""
    if column not in frame.columns:
        return pd.Series([default_value] * len(frame), index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default_value)


def safe_rate(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide two aligned series and return null when the rate is unavailable."""
    numerator_values = pd.to_numeric(numerator, errors="coerce")
    denominator_values = pd.to_numeric(denominator, errors="coerce")
    result = numerator_values / denominator_values
    return result.where(denominator_values.notna() & denominator_values.ne(0), pd.NA)
