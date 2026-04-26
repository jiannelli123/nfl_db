"""Team defense fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.team_offense import build_fact_team_offense


def build_fact_team_defense(pbp: pd.DataFrame, weekly_team_stats: pd.DataFrame) -> pd.DataFrame:
    """Build team defense metrics by mirroring opponent offensive outputs."""
    offense = build_fact_team_offense(pbp=pbp, weekly_team_stats=weekly_team_stats)
    if offense.empty:
        return pd.DataFrame(
            columns=[
                "team_defense_key",
                "team",
                "game_id",
                "season",
                "season_type",
                "week",
                "plays_allowed",
                "yards_allowed",
                "points_allowed",
                "epa_allowed",
                "epa_allowed_per_play",
                "success_rate_allowed",
                "explosive_play_rate_allowed",
                "early_down_epa_allowed",
                "third_down_conversion_rate_allowed",
                "red_zone_td_rate_allowed",
            ]
        )

    defense = offense.rename(
        columns={
            "team_offense_key": "source_team_offense_key",
            "team": "opponent_team",
            "plays": "plays_allowed",
            "yards_gained": "yards_allowed",
            "points_scored": "points_allowed",
            "total_epa": "epa_allowed",
            "epa_per_play": "epa_allowed_per_play",
            "success_rate": "success_rate_allowed",
            "explosive_play_rate": "explosive_play_rate_allowed",
            "early_down_epa": "early_down_epa_allowed",
            "third_down_conversion_rate": "third_down_conversion_rate_allowed",
            "red_zone_td_rate": "red_zone_td_rate_allowed",
        }
    ).copy()

    if {"game_id", "home_team", "away_team"}.issubset(pbp.columns):
        matchup = pbp.loc[:, ["game_id", "home_team", "away_team"]].drop_duplicates(subset=["game_id"])
        defense = defense.merge(matchup, how="left", on="game_id")
        defense["team"] = defense.apply(
            lambda row: row["away_team"] if row["opponent_team"] == row["home_team"] else row["home_team"],
            axis=1,
        )
    else:
        defense["team"] = pd.NA

    defense["team_defense_key"] = (
        defense["team"].astype(str)
        + "_"
        + defense["game_id"].astype(str)
        + "_"
        + defense["season_type"].astype(str)
    )
    return defense[
        [
            "team_defense_key",
            "team",
            "game_id",
            "season",
            "season_type",
            "week",
            "plays_allowed",
            "yards_allowed",
            "points_allowed",
            "epa_allowed",
            "epa_allowed_per_play",
            "success_rate_allowed",
            "explosive_play_rate_allowed",
            "early_down_epa_allowed",
            "third_down_conversion_rate_allowed",
            "red_zone_td_rate_allowed",
        ]
    ]
