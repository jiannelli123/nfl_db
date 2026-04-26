"""Team offense fact builders."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_fact_team_offense(pbp: pd.DataFrame, weekly_team_stats: pd.DataFrame) -> pd.DataFrame:
    """Build team offense metrics from play-by-play and weekly team statistics."""
    if pbp.empty:
        columns = [
            "team_offense_key",
            "team",
            "game_id",
            "season",
            "season_type",
            "week",
            "plays",
            "yards_gained",
            "points_scored",
            "total_epa",
            "epa_per_play",
            "success_rate",
            "explosive_play_rate",
            "early_down_epa",
            "third_down_conversion_rate",
            "red_zone_td_rate",
        ]
        return pd.DataFrame(columns=columns)

    frame = pbp.copy()
    frame["posteam"] = frame["posteam"].fillna("")
    offense = frame.loc[frame["posteam"] != ""].copy()
    offense["is_success"] = offense["epa"].fillna(0).gt(0)
    offense["is_explosive"] = offense["yards_gained"].fillna(0).ge(20)
    offense["is_early_down"] = offense["down"].fillna(0).isin([1, 2])
    offense["is_third_down"] = offense["down"].fillna(0).eq(3)
    offense["third_down_converted"] = offense["is_third_down"] & (
        offense["first_down"].fillna(0).eq(1) | offense["touchdown"].fillna(0).eq(1)
    )
    offense["is_red_zone"] = offense["yardline_100"].fillna(101).le(20)
    offense["red_zone_td"] = offense["is_red_zone"] & offense["touchdown"].fillna(0).eq(1)

    grouped = offense.groupby(["posteam", "game_id", "season", "season_type", "week"], as_index=False).agg(
        plays=("play_id", "count"),
        yards_gained=("yards_gained", "sum"),
        total_epa=("epa", "sum"),
        success_rate=("is_success", "mean"),
        explosive_play_rate=("is_explosive", "mean"),
        early_down_epa=("epa", lambda values: values.loc[offense.loc[values.index, "is_early_down"]].mean()),
        third_down_attempts=("is_third_down", "sum"),
        third_down_conversions=("third_down_converted", "sum"),
        red_zone_plays=("is_red_zone", "sum"),
        red_zone_touchdowns=("red_zone_td", "sum"),
    )
    grouped["epa_per_play"] = np.where(grouped["plays"] > 0, grouped["total_epa"] / grouped["plays"], 0.0)
    grouped["third_down_conversion_rate"] = np.where(
        grouped["third_down_attempts"] > 0,
        grouped["third_down_conversions"] / grouped["third_down_attempts"],
        0.0,
    )
    grouped["red_zone_td_rate"] = np.where(
        grouped["red_zone_plays"] > 0,
        grouped["red_zone_touchdowns"] / grouped["red_zone_plays"],
        0.0,
    )

    points = pd.DataFrame(columns=["team", "game_id", "points_scored"])
    if not weekly_team_stats.empty and {"team", "game_id", "points"}.issubset(weekly_team_stats.columns):
        points = weekly_team_stats.loc[:, ["team", "game_id", "points"]].rename(
            columns={"points": "points_scored"}
        )

    result = grouped.merge(
        points,
        how="left",
        left_on=["posteam", "game_id"],
        right_on=["team", "game_id"],
    )
    result["points_scored"] = result["points_scored"].fillna(0)
    result["team"] = result["posteam"]
    result["team_offense_key"] = (
        result["team"].astype(str)
        + "_"
        + result["game_id"].astype(str)
        + "_"
        + result["season_type"].astype(str)
    )
    return result[
        [
            "team_offense_key",
            "team",
            "game_id",
            "season",
            "season_type",
            "week",
            "plays",
            "yards_gained",
            "points_scored",
            "total_epa",
            "epa_per_play",
            "success_rate",
            "explosive_play_rate",
            "early_down_epa",
            "third_down_conversion_rate",
            "red_zone_td_rate",
        ]
    ]
