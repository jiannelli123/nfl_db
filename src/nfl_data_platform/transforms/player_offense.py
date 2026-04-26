"""Builds the player offense fact table from weekly player stats.

The high-level flow is intentionally simple:

    raw weekly stats  -->  normalize identity (id, name, team)
                      -->  fill in missing stat columns with 0
                      -->  calculate standard fantasy points
                      -->  keep only offensive players
                      -->  return one row per player per game
"""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.normalization import (
    ensure_numeric_column,
    normalize_player_values,
    resolve_player_name_column,
    resolve_team_column,
)

# ---------------------------------------------------------------------------
# Standard (non-PPR) fantasy scoring rules.
# Each entry maps a stat column to the points awarded per unit of that stat.
# Reads like a scoring sheet: 1 point per 25 passing yards (0.04 * 25 = 1),
# 4 points per passing TD, -2 per interception, etc.
# ---------------------------------------------------------------------------
STANDARD_SCORING_RULES: dict[str, float] = {
    "passing_yards": 0.04,            # 1 pt per 25 yards
    "passing_tds": 4,
    "interceptions": -2,
    "rushing_yards": 0.1,              # 1 pt per 10 yards
    "rushing_tds": 6,
    "receiving_yards": 0.1,            # 1 pt per 10 yards
    "receiving_tds": 6,
    "passing_2pt_conversions": 2,
    "rushing_2pt_conversions": 2,
    "receiving_2pt_conversions": 2,
    "sack_fumbles_lost": -2,
    "rushing_fumbles_lost": -2,
    "receiving_fumbles_lost": -2,
}

# Identity columns that must exist on every input row.
REQUIRED_IDENTITY_COLUMNS = ["player_id", "game_id", "season", "season_type", "week"]

# Volume stats we report but don't directly score (e.g. attempts, targets).
VOLUME_STAT_COLUMNS = ["completions", "attempts", "carries", "targets", "receptions"]

# All stat columns we need to coerce to numbers (volume + scoring).
ALL_STAT_COLUMNS = VOLUME_STAT_COLUMNS + list(STANDARD_SCORING_RULES.keys())

# Positions considered "offensive" for inclusion in this table.
OFFENSIVE_POSITIONS = {"QB", "RB", "FB", "WR", "TE", "HB"}

# Stats whose presence (non-zero value) qualifies a row as "offensive activity"
# even if the player's listed position isn't in OFFENSIVE_POSITIONS.
OFFENSIVE_ACTIVITY_COLUMNS = [
    "attempts", "carries", "targets", "receptions",
    "passing_tds", "rushing_tds", "receiving_tds",
]

# Final shape of the fact table.
OUTPUT_COLUMNS = [
    "player_offense_key",
    "player_id", "player_name", "team",
    "game_id", "season", "season_type", "week",
    "completions", "attempts",
    "passing_yards", "passing_tds", "interceptions",
    "carries", "rushing_yards", "rushing_tds",
    "targets", "receptions", "receiving_yards", "receiving_tds",
    "fantasy_points_standard",
]


def build_fact_player_offense(weekly_player_stats: pd.DataFrame) -> pd.DataFrame:
    """Build the player offense fact table from weekly player statistics.

    TODO: Add target share, air yards share, and route participation once a
    stable source feed and team-level denominator strategy are finalized.
    """
    if weekly_player_stats.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    frame = weekly_player_stats.copy()
    frame = _ensure_identity_columns_exist(frame)
    frame = _normalize_identity_columns(frame)
    frame = _coerce_stat_columns_to_numeric(frame)
    frame["fantasy_points_standard"] = _calculate_standard_fantasy_points(frame)
    frame = _filter_to_offensive_players(frame)

    if frame.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    frame["player_offense_key"] = _build_player_offense_key(frame)
    return frame[OUTPUT_COLUMNS].copy()


# ---------------------------------------------------------------------------
# Step 1: make sure required identity columns are present (fill with NA if not)
# ---------------------------------------------------------------------------
def _ensure_identity_columns_exist(frame: pd.DataFrame) -> pd.DataFrame:
    for column in REQUIRED_IDENTITY_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame


# ---------------------------------------------------------------------------
# Step 2: normalize player id, player name, and team to canonical values
# ---------------------------------------------------------------------------
def _normalize_identity_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame["player_id"] = normalize_player_values(frame["player_id"])
    frame["player_name"] = resolve_player_name_column(frame)
    frame["team"] = resolve_team_column(frame)
    return frame


# ---------------------------------------------------------------------------
# Step 3: ensure every stat column exists and is numeric (missing -> 0)
# ---------------------------------------------------------------------------
def _coerce_stat_columns_to_numeric(frame: pd.DataFrame) -> pd.DataFrame:
    for column in ALL_STAT_COLUMNS:
        frame[column] = ensure_numeric_column(frame, column, default_value=0)
    return frame


# ---------------------------------------------------------------------------
# Step 4: calculate standard fantasy points
#
# For each scoring stat, multiply the value by its rule and sum the result.
# Example: a row with 300 passing yards and 3 passing TDs earns
#   300 * 0.04 + 3 * 4 = 12 + 12 = 24 points (before other stats).
# ---------------------------------------------------------------------------
def _calculate_standard_fantasy_points(frame: pd.DataFrame) -> pd.Series:
    points_per_rule = (frame[stat] * weight for stat, weight in STANDARD_SCORING_RULES.items())
    return sum(points_per_rule).round(2)


# ---------------------------------------------------------------------------
# Step 5: keep only offensive players (by position OR by offensive activity)
# ---------------------------------------------------------------------------
def _filter_to_offensive_players(frame: pd.DataFrame) -> pd.DataFrame:
    position = frame.get("position", pd.Series(pd.NA, index=frame.index)).astype("string").str.upper()
    is_offensive_position = position.isin(OFFENSIVE_POSITIONS)
    has_offensive_activity = frame[OFFENSIVE_ACTIVITY_COLUMNS].sum(axis=1).gt(0)
    return frame.loc[is_offensive_position | has_offensive_activity].copy()


# ---------------------------------------------------------------------------
# Step 6: build the unique row key (e.g. "p1_g1_REG_1")
# ---------------------------------------------------------------------------
def _build_player_offense_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["player_id"].astype(str) + "_"
        + frame["game_id"].astype(str) + "_"
        + frame["season_type"].astype(str) + "_"
        + frame["week"].astype(str)
    )
