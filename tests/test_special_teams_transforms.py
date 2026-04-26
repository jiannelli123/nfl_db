"""Tests for special teams metric derivation."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.player_special_teams import (
    build_fact_player_special_teams,
)
from nfl_data_platform.transforms.team_special_teams import build_fact_team_special_teams


def test_build_fact_team_special_teams_derives_public_metrics() -> None:
    weekly_team_stats = pd.DataFrame(
        [
            {
                "team": "BUF",
                "game_id": "g1",
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "fg_att": 2,
                "fg_made": 2,
                "xp_att": 3,
                "xp_made": 3,
                "punts": 4,
                "punt_yards": 188,
                "kickoff_returns": 1,
                "punt_returns": 2,
            }
        ]
    )
    team_rankings_metrics = pd.DataFrame(
        [{"team": "BUF", "game_id": "g1", "special_teams_rating": 4.2}]
    )
    ftn_metrics = pd.DataFrame(
        [{"team": "BUF", "game_id": "g1", "special_teams_dvoa": 1.7}]
    )

    result = build_fact_team_special_teams(
        weekly_team_stats=weekly_team_stats,
        team_rankings_metrics=team_rankings_metrics,
        ftn_metrics=ftn_metrics,
    )

    assert result.loc[0, "team_special_teams_key"] == "BUF_g1_REG"
    assert result.loc[0, "field_goal_attempts"] == 2
    assert result.loc[0, "field_goals_made"] == 2
    assert result.loc[0, "extra_point_attempts"] == 3
    assert result.loc[0, "kick_returns"] == 1
    assert result.loc[0, "team_rankings_special_teams_rating"] == 4.2
    assert result.loc[0, "dvoa_special_teams"] == 1.7


def test_build_fact_player_special_teams_handles_aliases_and_defaults() -> None:
    weekly_player_stats = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "player_name": "Player One",
                "recent_team": "BUF",
                "game_id": "g1",
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "kickoff_returns": 2,
                "kickoff_return_yards": 54,
                "punt_returns": 1,
                "punt_return_yards": 12,
            }
        ]
    )

    result = build_fact_player_special_teams(weekly_player_stats)

    assert result.loc[0, "player_special_teams_key"] == "p1_g1_1"
    assert result.loc[0, "team"] == "BUF"
    assert result.loc[0, "kick_returns"] == 2
    assert result.loc[0, "kick_return_yards"] == 54
    assert result.loc[0, "field_goal_attempts"] == 0


def test_build_fact_team_special_teams_returns_expected_shape_when_empty() -> None:
    result = build_fact_team_special_teams(pd.DataFrame())

    assert "team_special_teams_key" in result.columns
    assert "team_rankings_special_teams_rating" in result.columns
    assert result.empty
