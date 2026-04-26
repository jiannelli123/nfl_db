"""Dimension builders for canonical warehouse entities (teams, players, games)."""

from __future__ import annotations

import pandas as pd


def _coalesce_columns(frame: pd.DataFrame, columns: list[str], default: object = pd.NA) -> pd.Series:
    """Return the first non-null value across a list of possible source columns."""
    if frame.empty:
        return pd.Series(dtype="object")
    result = pd.Series([default] * len(frame), index=frame.index)
    for column in columns:
        if column in frame.columns:
            result = result.where(result.notna(), frame[column])
    return result


def _normalize_identifier(series: pd.Series) -> pd.Series:
    """Normalize identifier values to non-empty strings."""
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA})
    )


def build_dim_team(rosters: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical team dimension from roster and schedule inputs."""
    roster_teams = rosters.copy()
    if "team" not in roster_teams.columns:
        roster_teams["team"] = _coalesce_columns(roster_teams, ["team_abbr", "recent_team", "club_code"])
    if "team_name" not in roster_teams.columns:
        roster_teams["team_name"] = _coalesce_columns(
            roster_teams,
            ["team_name", "club_name", "team"],
        )
    roster_teams = roster_teams.loc[
        :,
        [column for column in ["team", "season", "team_name"] if column in roster_teams.columns],
    ].copy()
    schedule_home = schedules.loc[
        :,
        [column for column in ["home_team", "season", "home_team_name"] if column in schedules.columns],
    ].rename(columns={"home_team": "team"})
    schedule_away = schedules.loc[
        :,
        [column for column in ["away_team", "season", "away_team_name"] if column in schedules.columns],
    ].rename(columns={"away_team": "team"})
    if "home_team_name" in schedule_home.columns:
        schedule_home = schedule_home.rename(columns={"home_team_name": "team_name"})
    if "away_team_name" in schedule_away.columns:
        schedule_away = schedule_away.rename(columns={"away_team_name": "team_name"})

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
        team_name=("team_name", "last"),
        first_season=("season", "min"),
        last_seen_season=("season", "max"),
    )
    grouped["team_key"] = grouped["team"].str.lower()
    grouped["team_id"] = grouped["team"]
    grouped["team_abbr"] = grouped["team"]
    grouped["team_name"] = grouped["team_name"].fillna(grouped["team"])
    grouped["conference"] = pd.NA
    grouped["division"] = pd.NA
    grouped["franchise_name"] = pd.NA
    return grouped[
        [
            "team_key",
            "team_id",
            "team_abbr",
            "team_name",
            "conference",
            "division",
            "franchise_name",
            "first_season",
            "last_seen_season",
        ]
    ]


def build_dim_player(rosters: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical player dimension from roster inputs."""
    frame = rosters.copy()
    frame["player_id"] = _normalize_identifier(
        _coalesce_columns(frame, ["player_id", "gsis_id", "esb_id", "smart_id", "pfr_id"])
    )
    if "player_name" not in frame.columns:
        frame["player_name"] = _coalesce_columns(frame, ["full_name", "display_name", "player_id"])
    if "team" not in frame.columns:
        frame["team"] = _coalesce_columns(frame, ["team_abbr", "recent_team", "club_code"])
    if "position" not in frame.columns:
        frame["position"] = _coalesce_columns(frame, ["position", "pos"])
    if "status" not in frame.columns:
        frame["status"] = _coalesce_columns(frame, ["status", "player_status"])
    required_columns = ["player_id", "player_name", "team", "position", "status", "season"]
    available_columns = [column for column in required_columns if column in frame.columns]
    frame = frame.loc[:, available_columns].copy() if available_columns else pd.DataFrame(columns=required_columns)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "player_key",
                "player_id",
                "player_name",
                "current_team",
                "position",
                "status",
                "rookie_season",
                "last_seen_season",
            ]
        )

    frame = frame.dropna(subset=["player_id"]).sort_values(["player_id", "season"])
    grouped = frame.groupby("player_id", as_index=False).agg(
        player_name=("player_name", "last"),
        current_team=("team", "last"),
        position=("position", "last"),
        status=("status", "last"),
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
            "status",
            "rookie_season",
            "last_seen_season",
        ]
    ]


def build_dim_game(schedules: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical game dimension from normalized schedule inputs."""
    frame = schedules.copy()
    if "season_type" not in frame.columns and "game_type" in frame.columns:
        frame["season_type"] = frame["game_type"]
    if "gameday" not in frame.columns and "game_date" in frame.columns:
        frame["gameday"] = frame["game_date"]
    if "gametime" not in frame.columns and "start_time" in frame.columns:
        frame["gametime"] = frame["start_time"]
    if "status" not in frame.columns:
        frame["status"] = pd.NA
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
    available_columns = [column for column in expected_columns if column in frame.columns]
    frame = frame.loc[:, available_columns].copy() if available_columns else pd.DataFrame(columns=expected_columns)
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
