"""Tests for dimension builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.dimensions import build_dim_game, build_dim_player, build_dim_team


def test_build_dim_team_deduplicates_and_sorts() -> None:
    rosters = pd.DataFrame(
        [
            {"team": "BUF", "season": 2024},
            {"team": "BUF", "season": 2025},
            {"team": "KC", "season": 2025},
        ]
    )
    schedules = pd.DataFrame(
        [
            {"home_team": "BUF", "away_team": "KC", "season": 2025},
            {"home_team": "KC", "away_team": "BUF", "season": 2024},
        ]
    )

    result = build_dim_team(rosters=rosters, schedules=schedules)

    assert list(result["team_id"]) == ["BUF", "KC"]
    assert result.loc[result["team_id"] == "BUF", "first_season"].item() == 2024


def test_build_dim_player_returns_latest_team_and_position() -> None:
    rosters = pd.DataFrame(
        [
            {"player_id": "p1", "player_name": "Player One", "team": "BUF", "position": "WR", "season": 2024},
            {"player_id": "p1", "player_name": "Player One", "team": "KC", "position": "WR", "season": 2025},
        ]
    )

    result = build_dim_player(rosters)

    assert result.loc[0, "current_team"] == "KC"
    assert result.loc[0, "rookie_season"] == 2024


def test_build_dim_game_uses_game_id_as_key() -> None:
    schedules = pd.DataFrame(
        [
            {
                "game_id": "2025_01_BUF_KC",
                "season": 2025,
                "season_type": "REG",
                "week": 1,
                "gameday": "2025-09-04",
                "gametime": "20:20",
                "home_team": "BUF",
                "away_team": "KC",
                "stadium": "Arrowhead",
                "status": "scheduled",
            }
        ]
    )

    result = build_dim_game(schedules)

    assert result.loc[0, "game_key"] == "2025_01_BUF_KC"
