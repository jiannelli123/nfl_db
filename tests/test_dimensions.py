"""Tests for dimension builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.bridge_player_ids import build_bridge_player_ids
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
            {"player_id": "p1", "full_name": "Player One", "team_abbr": "BUF", "position": "WR", "status": "ACT", "season": 2024},
            {"player_id": "p1", "full_name": "Player One", "team_abbr": "KC", "position": "WR", "status": "ACT", "season": 2025},
        ]
    )

    result = build_dim_player(rosters)

    assert result.loc[0, "current_team"] == "KC"
    assert result.loc[0, "rookie_season"] == 2024
    assert result.loc[0, "status"] == "ACT"


def test_build_dim_player_uses_gsis_id_when_player_id_is_absent() -> None:
    rosters = pd.DataFrame(
        [
            {
                "gsis_id": "00-0023459",
                "full_name": "Aaron Rodgers",
                "team": "PIT",
                "position": "QB",
                "status": "ACT",
                "season": 2025,
            }
        ]
    )

    result = build_dim_player(rosters)

    assert result.loc[0, "player_id"] == "00-0023459"
    assert result.loc[0, "player_key"] == "00-0023459"
    assert result.loc[0, "player_name"] == "Aaron Rodgers"


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


def test_build_dim_game_uses_game_type_as_season_type_when_needed() -> None:
    schedules = pd.DataFrame(
        [
            {
                "game_id": "2025_01_BUF_KC",
                "season": 2025,
                "game_type": "REG",
                "week": 1,
                "gameday": "2025-09-04",
                "gametime": "20:20",
                "home_team": "BUF",
                "away_team": "KC",
                "stadium": "Arrowhead",
            }
        ]
    )

    result = build_dim_game(schedules)

    assert result.loc[0, "season_type"] == "REG"
    assert pd.isna(result.loc[0, "status"])


def test_build_bridge_player_ids_matches_dim_player() -> None:
    dim_player = pd.DataFrame(
        [{"player_key": "p1", "player_id": "p1", "player_name": "Player One"}]
    )

    result = build_bridge_player_ids(dim_player)

    assert result.loc[0, "bridge_player_ids_key"] == "p1_nflverse"
    assert result.loc[0, "nflverse_player_id"] == "p1"
