"""Player offense fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.normalization import (
    ensure_numeric_column,
    normalize_player_values,
    resolve_player_name_column,
    resolve_team_column,
)


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
        "fantasy_points_standard",
    ]
    if weekly_player_stats.empty:
        return pd.DataFrame(columns=columns)

    frame = weekly_player_stats.copy()
    required = ["player_id", "game_id", "season", "season_type", "week"]
    for column in required:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame["player_id"] = normalize_player_values(frame["player_id"])
    frame["player_name"] = resolve_player_name_column(frame)
    frame["team"] = resolve_team_column(frame)
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
        "sack_fumbles_lost",
        "rushing_fumbles_lost",
        "receiving_fumbles_lost",
        "passing_2pt_conversions",
        "rushing_2pt_conversions",
        "receiving_2pt_conversions",
    ]:
        frame[column] = ensure_numeric_column(frame, column, default_value=0)

    frame["fantasy_points_standard"] = (
        frame["passing_yards"] * 0.04
        + frame["passing_tds"] * 4
        + frame["interceptions"] * -2
        + frame["rushing_yards"] * 0.1
        + frame["rushing_tds"] * 6
        + frame["receiving_yards"] * 0.1
        + frame["receiving_tds"] * 6
        + frame["passing_2pt_conversions"] * 2
        + frame["rushing_2pt_conversions"] * 2
        + frame["receiving_2pt_conversions"] * 2
        + (
            frame["sack_fumbles_lost"]
            + frame["rushing_fumbles_lost"]
            + frame["receiving_fumbles_lost"]
        )
        * -2
    ).round(2)

    position = (
        frame.get("position", pd.Series([pd.NA] * len(frame), index=frame.index))
        .astype("string")
        .str.upper()
    )
    offensive_activity = frame[
        [
            "attempts",
            "carries",
            "targets",
            "receptions",
            "passing_tds",
            "rushing_tds",
            "receiving_tds",
        ]
    ].sum(axis=1)
    offensive_positions = {"QB", "RB", "FB", "WR", "TE", "HB"}
    frame = frame.loc[position.isin(offensive_positions) | offensive_activity.gt(0)].copy()
    if frame.empty:
        return pd.DataFrame(columns=columns)

    frame["player_offense_key"] = (
        frame["player_id"].astype(str)
        + "_"
        + frame["game_id"].astype(str)
        + "_"
        + frame["season_type"].astype(str)
        + "_"
        + frame["week"].astype(str)
    )
    return frame[columns].copy()
