"""Dimension builders for canonical warehouse entities."""

from __future__ import annotations

import pandas as pd


def build_dim_team(rosters: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical team dimension from roster and schedule inputs."""
    roster_teams = rosters.loc[:, [column for column in ["team", "season"] if column in rosters.columns]].copy()
    schedule_home = schedules.loc[
        :, [column for column in ["home_team", "season"] if column in schedules.columns]
    ].rename(columns={"home_team": "team"})
    schedule_away = schedules.loc[
        :, [column for column in ["away_team", "season"] if column in schedules.columns]
    ].rename(columns={"away_team": "team"})

    combined = pd.concat([roster_teams, schedule_home, schedule_away], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(
            columns=[
                "team_key",
                "team_id",
                "team_abbr",
                "team_name",
                "conference",
                "division",
                "first_season",
                "last_seen_season",
            ]
        )

    combined = combined.dropna(subset=["team"]).drop_duplicates().sort_values(["team", "season"])
    grouped = combined.groupby("team", as_index=False).agg(
        first_season=("season", "min"),
        last_seen_season=("season", "max"),
    )
    grouped["team_key"] = grouped["team"].str.lower()
    grouped["team_id"] = grouped["team"]
    grouped["team_abbr"] = grouped["team"]
    grouped["team_name"] = grouped["team"]
    grouped["conference"] = pd.NA
    grouped["division"] = pd.NA
    return grouped[
        [
            "team_key",
            "team_id",
            "team_abbr",
            "team_name",
            "conference",
            "division",
            "first_season",
            "last_seen_season",
        ]
    ]


def build_dim_player(rosters: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical player dimension from roster inputs."""
    required_columns = ["player_id", "player_name", "team", "position", "season"]
    available_columns = [column for column in required_columns if column in rosters.columns]
    frame = rosters.loc[:, available_columns].copy() if available_columns else pd.DataFrame(columns=required_columns)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "player_key",
                "player_id",
                "player_name",
                "current_team",
                "position",
                "rookie_season",
                "last_seen_season",
            ]
        )

    frame = frame.dropna(subset=["player_id"]).sort_values(["player_id", "season"])
    grouped = frame.groupby("player_id", as_index=False).agg(
        player_name=("player_name", "last"),
        current_team=("team", "last"),
        position=("position", "last"),
        rookie_season=("season", "min"),
        last_seen_season=("season", "max"),
    )
    grouped["player_key"] = grouped["player_id"].astype(str)
    return grouped[
        [
            "player_key",
            "player_id",
            "player_name",
            "current_team",
            "position",
            "rookie_season",
            "last_seen_season",
        ]
    ]


def build_dim_game(schedules: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical game dimension from normalized schedule inputs."""
    expected_columns = [
        "game_id",
        "season",
        "season_type",
        "week",
        "gameday",
        "gametime",
        "home_team",
        "away_team",
        "stadium",
        "status",
    ]
    available_columns = [column for column in expected_columns if column in schedules.columns]
    frame = schedules.loc[:, available_columns].copy() if available_columns else pd.DataFrame(columns=expected_columns)
    if frame.empty:
        return pd.DataFrame(columns=["game_key", *expected_columns])

    frame = frame.dropna(subset=["game_id"]).drop_duplicates(subset=["game_id"]).sort_values(
        ["season", "week", "game_id"]
    )
    frame["game_key"] = frame["game_id"].astype(str)
    return frame[
        [
            "game_key",
            "game_id",
            "season",
            "season_type",
            "week",
            "gameday",
            "gametime",
            "home_team",
            "away_team",
            "stadium",
            "status",
        ]
    ]
