"""Play-by-play fact builders."""

from __future__ import annotations

import pandas as pd


def build_fact_game_pbp(pbp: pd.DataFrame) -> pd.DataFrame:
    """Build a normalized play-by-play fact table from raw play rows."""
    columns = [
        "pbp_key",
        "game_id",
        "play_id",
        "season",
        "season_type",
        "week",
        "posteam",
        "defteam",
        "home_team",
        "away_team",
        "down",
        "ydstogo",
        "yardline_100",
        "play_type",
        "yards_gained",
        "epa",
        "success",
        "first_down",
        "touchdown",
    ]
    if pbp.empty:
        return pd.DataFrame(columns=columns)

    frame = pbp.copy()
    required_columns = [
        "game_id",
        "play_id",
        "season",
        "season_type",
        "week",
        "posteam",
        "defteam",
        "home_team",
        "away_team",
        "down",
        "ydstogo",
        "yardline_100",
        "play_type",
        "yards_gained",
        "epa",
        "first_down",
        "touchdown",
    ]
    for column in required_columns:
        if column not in frame.columns:
            frame[column] = pd.NA

    if "success" not in frame.columns:
        frame["success"] = frame["epa"].fillna(0).gt(0)

    frame = frame.dropna(subset=["game_id", "play_id"]).copy()
    frame["pbp_key"] = frame["game_id"].astype(str) + "_" + frame["play_id"].astype(str)
    return frame[columns].drop_duplicates(subset=["pbp_key"]).copy()
