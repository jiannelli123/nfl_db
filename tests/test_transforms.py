"""Tests for fact transform builders."""

from __future__ import annotations

import pandas as pd
import pytest

from nfl_data_platform.transforms.player_offense import build_fact_player_offense
from nfl_data_platform.transforms.team_defense import build_fact_team_defense
from nfl_data_platform.transforms.team_offense import build_fact_team_offense


@pytest.fixture
def sample_pbp() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "play_id": 1,
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "posteam": "BUF",
                "home_team": "BUF",
                "away_team": "KC",
                "epa": 2.0,
                "yards_gained": 25,
                "down": 1,
                "first_down": 1,
                "touchdown": 0,
                "yardline_100": 50,
            },
            {
                "game_id": "g1",
                "play_id": 2,
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "posteam": "BUF",
                "home_team": "BUF",
                "away_team": "KC",
                "epa": -1.0,
                "yards_gained": 5,
                "down": 3,
                "first_down": 0,
                "touchdown": 0,
                "yardline_100": 18,
            },
            {
                "game_id": "g1",
                "play_id": 3,
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "posteam": "KC",
                "home_team": "BUF",
                "away_team": "KC",
                "epa": 3.0,
                "yards_gained": 21,
                "down": 3,
                "first_down": 1,
                "touchdown": 1,
                "yardline_100": 10,
            },
        ]
    )


def test_build_fact_team_offense_calculates_starter_metrics(sample_pbp: pd.DataFrame) -> None:
    weekly_team_stats = pd.DataFrame(
        [
            {"team": "BUF", "game_id": "g1", "points": 17},
            {"team": "KC", "game_id": "g1", "points": 24},
        ]
    )

    result = build_fact_team_offense(sample_pbp, weekly_team_stats)
    buf_row = result.loc[result["team"] == "BUF"].iloc[0]

    assert buf_row["plays"] == 2
    assert buf_row["yards_gained"] == 30
    assert buf_row["points_scored"] == 17
    assert buf_row["epa_per_play"] == pytest.approx(0.5)
    assert buf_row["success_rate"] == pytest.approx(0.5)
    assert buf_row["explosive_play_rate"] == pytest.approx(0.5)
    assert buf_row["third_down_conversion_rate"] == pytest.approx(0.0)
    assert buf_row["red_zone_td_rate"] == pytest.approx(0.0)


def test_build_fact_team_defense_mirrors_opponent_outputs(sample_pbp: pd.DataFrame) -> None:
    weekly_team_stats = pd.DataFrame(
        [
            {"team": "BUF", "game_id": "g1", "points": 17},
            {"team": "KC", "game_id": "g1", "points": 24},
        ]
    )

    result = build_fact_team_defense(sample_pbp, weekly_team_stats)
    kc_defense = result.loc[result["team"] == "KC"].iloc[0]

    assert kc_defense["plays_allowed"] == 2
    assert kc_defense["yards_allowed"] == 30
    assert kc_defense["points_allowed"] == 17


def test_build_fact_player_offense_returns_expected_columns() -> None:
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
                "targets": 8,
                "receptions": 6,
                "receiving_yards": 81,
            }
        ]
    )

    result = build_fact_player_offense(weekly_player_stats)

    assert result.loc[0, "team"] == "BUF"
    assert result.loc[0, "targets"] == 8
    assert result.loc[0, "player_offense_key"] == "p1_g1_1"
