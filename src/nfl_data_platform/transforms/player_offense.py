"""Player offense fact builders."""

from __future__ import annotations

import pandas as pd


def build_fact_player_offense(weekly_player_stats: pd.DataFrame) -> pd.DataFrame:
    """Build a player offense fact table from normalized weekly player statistics.

    TODO: Add target share, air yards share, and route participation once a stable
    source feed and team-level denominator strategy are finalized.
    """
    columns = [
        "player_offense_key",
        "player_id",
        "player_name",
        "team",
        "game_id",
        "season",
        "season_type",
        "week",
        "completions",
        "attempts",
        "passing_yards",
        "passing_tds",
        "interceptions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
    ]
    if weekly_player_stats.empty:
        return pd.DataFrame(columns=columns)

    frame = weekly_player_stats.copy()
    required = ["player_id", "player_name", "recent_team", "game_id", "season", "season_type", "week"]
    for column in required:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame = frame.rename(columns={"recent_team": "team"})
    for column in [
        "completions",
        "attempts",
        "passing_yards",
        "passing_tds",
        "interceptions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
    ]:
        if column not in frame.columns:
            frame[column] = 0

    frame["player_offense_key"] = (
        frame["player_id"].astype(str)
        + "_"
        + frame["game_id"].astype(str)
        + "_"
        + frame["week"].astype(str)
    )
    return frame[columns].copy()
