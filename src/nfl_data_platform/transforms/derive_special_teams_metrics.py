"""Special teams metric derivation helpers.

These helpers stay intentionally conservative because public special teams
coverage varies by source. Phase 1 favors explicit, nflverse-compatible
columns when present and falls back to zeros or null enrichments when a field
is not available yet.
"""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.normalization import (
    first_available_column,
    normalize_player_values,
    resolve_player_name_column,
    resolve_team_column,
)


TEAM_SPECIAL_TEAMS_ALIASES: dict[str, list[str]] = {
    "field_goal_attempts": ["field_goal_attempts", "fg_att"],
    "field_goals_made": ["field_goals_made", "fg_made"],
    "extra_point_attempts": ["extra_point_attempts", "xp_att"],
    "extra_points_made": ["extra_points_made", "xp_made"],
    "punts": ["punts", "punt_attempts"],
    "punt_yards": ["punt_yards"],
    "kick_returns": ["kick_returns", "kickoff_returns"],
    "punt_returns": ["punt_returns"],
}

PLAYER_SPECIAL_TEAMS_ALIASES: dict[str, list[str]] = {
    "field_goal_attempts": ["field_goal_attempts", "fg_att"],
    "field_goals_made": ["field_goals_made", "fg_made"],
    "extra_point_attempts": ["extra_point_attempts", "xp_att"],
    "extra_points_made": ["extra_points_made", "xp_made"],
    "punts": ["punts", "punt_attempts"],
    "punt_yards": ["punt_yards"],
    "kick_returns": ["kick_returns", "kickoff_returns"],
    "kick_return_yards": ["kick_return_yards", "kickoff_return_yards"],
    "punt_returns": ["punt_returns"],
    "punt_return_yards": ["punt_return_yards"],
}


def derive_team_special_teams_metrics(
    weekly_team_stats: pd.DataFrame,
    team_rankings_metrics: pd.DataFrame | None = None,
    ftn_metrics: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Derive team-level special teams metrics from public-compatible inputs.

    Assumptions:
    - Weekly team stats are already at one row per team/game grain.
    - TeamRankings, when provided, enriches the same team/game grain with a
      public rating field.
    - FTN special teams DVOA is optional and may only be available later.
    """
    base_columns = [
        "team_special_teams_key",
        "team",
        "game_id",
        "season",
        "season_type",
        "week",
        "field_goal_attempts",
        "field_goals_made",
        "extra_point_attempts",
        "extra_points_made",
        "punts",
        "punt_yards",
        "kick_returns",
        "punt_returns",
        "team_rankings_special_teams_rating",
        "dvoa_special_teams",
    ]
    if weekly_team_stats.empty:
        return pd.DataFrame(columns=base_columns)

    frame = weekly_team_stats.copy()
    for column in ["game_id", "season", "season_type", "week"]:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame["team"] = resolve_team_column(frame)

    for target_column, aliases in TEAM_SPECIAL_TEAMS_ALIASES.items():
        frame[target_column] = _resolve_first_available_column(frame, aliases, default_value=0)

    frame["team_rankings_special_teams_rating"] = pd.NA
    if team_rankings_metrics is not None and not team_rankings_metrics.empty:
        rating_frame = team_rankings_metrics.copy()
        join_columns = [column for column in ["team", "game_id"] if column in rating_frame.columns]
        if "team_rankings_special_teams_rating" not in rating_frame.columns:
            rating_frame["team_rankings_special_teams_rating"] = _resolve_first_available_column(
                rating_frame,
                ["team_rankings_special_teams_rating", "special_teams_rating"],
                default_value=pd.NA,
            )
        if join_columns:
            frame = frame.merge(
                rating_frame.loc[:, [*join_columns, "team_rankings_special_teams_rating"]],
                how="left",
                on=join_columns,
                suffixes=("", "_incoming"),
            )
            if "team_rankings_special_teams_rating_incoming" in frame.columns:
                frame["team_rankings_special_teams_rating"] = frame[
                    "team_rankings_special_teams_rating_incoming"
                ]
                frame = frame.drop(columns=["team_rankings_special_teams_rating_incoming"])

    frame["dvoa_special_teams"] = pd.NA
    if ftn_metrics is not None and not ftn_metrics.empty:
        dvoa_frame = ftn_metrics.copy()
        join_columns = [column for column in ["team", "game_id"] if column in dvoa_frame.columns]
        if "dvoa_special_teams" not in dvoa_frame.columns:
            dvoa_frame["dvoa_special_teams"] = _resolve_first_available_column(
                dvoa_frame,
                ["dvoa_special_teams", "special_teams_dvoa"],
                default_value=pd.NA,
            )
        if join_columns:
            frame = frame.merge(
                dvoa_frame.loc[:, [*join_columns, "dvoa_special_teams"]],
                how="left",
                on=join_columns,
                suffixes=("", "_incoming"),
            )
            if "dvoa_special_teams_incoming" in frame.columns:
                frame["dvoa_special_teams"] = frame["dvoa_special_teams_incoming"]
                frame = frame.drop(columns=["dvoa_special_teams_incoming"])

    frame["team_special_teams_key"] = (
        frame["team"].astype(str)
        + "_"
        + frame["game_id"].astype(str)
        + "_"
        + frame["season_type"].astype(str)
    )
    return frame[base_columns].copy()


def derive_player_special_teams_metrics(weekly_player_stats: pd.DataFrame) -> pd.DataFrame:
    """Derive player-level special teams metrics from public-compatible inputs.

    Assumptions:
    - Weekly player stats are already at one row per player/game grain.
    - Missing special teams fields should default to zero instead of blocking
      the transform, because source coverage is incomplete in Phase 1.
    """
    base_columns = [
        "player_special_teams_key",
        "player_id",
        "player_name",
        "team",
        "game_id",
        "season",
        "season_type",
        "week",
        "field_goal_attempts",
        "field_goals_made",
        "extra_point_attempts",
        "extra_points_made",
        "punts",
        "punt_yards",
        "kick_returns",
        "kick_return_yards",
        "punt_returns",
        "punt_return_yards",
    ]
    if weekly_player_stats.empty:
        return pd.DataFrame(columns=base_columns)

    frame = weekly_player_stats.copy()
    required_columns = ["player_id", "game_id", "season", "season_type", "week"]
    for column in required_columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame["player_id"] = normalize_player_values(frame["player_id"])
    frame["player_name"] = resolve_player_name_column(frame)
    frame["team"] = resolve_team_column(frame)

    for target_column, aliases in PLAYER_SPECIAL_TEAMS_ALIASES.items():
        frame[target_column] = _resolve_first_available_column(frame, aliases, default_value=0)

    position = (
        frame.get("position", pd.Series([pd.NA] * len(frame), index=frame.index))
        .astype("string")
        .str.upper()
    )
    special_teams_activity = frame[
        [
            "field_goal_attempts",
            "extra_point_attempts",
            "punts",
            "kick_returns",
            "punt_returns",
        ]
    ].sum(axis=1)
    special_teams_positions = {"K", "P", "PK"}
    frame = frame.loc[position.isin(special_teams_positions) | special_teams_activity.gt(0)].copy()
    if frame.empty:
        return pd.DataFrame(columns=base_columns)

    frame["player_special_teams_key"] = (
        frame["player_id"].astype(str)
        + "_"
        + frame["game_id"].astype(str)
        + "_"
        + frame["week"].astype(str)
    )
    return frame[base_columns].copy()


def _resolve_first_available_column(
    frame: pd.DataFrame,
    candidate_columns: list[str],
    default_value: object,
) -> pd.Series:
    """Return the first available source column or a default-filled series."""
    return first_available_column(frame, candidate_columns, default_value=default_value).fillna(default_value)
