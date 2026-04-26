"""Tests for Phase 1 warehouse loading."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nfl_data_platform.config import Settings
from nfl_data_platform.db.engine import create_engine_from_settings
from nfl_data_platform.db.load import load_phase1_tables
from nfl_data_platform.orchestration.pipeline import (
    PipelineRunContext,
    build_phase1_artifacts,
)


def test_load_phase1_tables_writes_tables_and_etl_log(tmp_path: Path) -> None:
    db_path = tmp_path / "test_phase1_load.sqlite"

    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=tmp_path,
    )
    manager = create_engine_from_settings(settings)
    manager.apply_ddl_directory("sql/ddl")

    extracted = {
        "schedules": pd.DataFrame(
            [
                {
                    "game_id": "g1",
                    "season": 2025,
                    "season_type": "REG",
                    "week": 1,
                    "home_team": "BUF",
                    "away_team": "KC",
                    "gameday": "2025-09-05",
                    "gametime": "20:20",
                    "stadium": "Highmark Stadium",
                    "status": "scheduled",
                }
            ]
        ),
        "rosters": pd.DataFrame(
            [
                {
                    "player_id": "p1",
                    "player_name": "Player One",
                    "team": "BUF",
                    "position": "WR",
                    "season": 2025,
                }
            ]
        ),
        "pbp": pd.DataFrame(
            [
                {
                    "game_id": "g1",
                    "play_id": 1,
                    "season": 2025,
                    "season_type": "REG",
                    "week": 1,
                    "posteam": "BUF",
                    "defteam": "KC",
                    "home_team": "BUF",
                    "away_team": "KC",
                    "play_type": "pass",
                    "ydstogo": 10,
                    "epa": 1.5,
                    "yards_gained": 22,
                    "down": 1,
                    "first_down": 1,
                    "touchdown": 0,
                    "yardline_100": 45,
                }
            ]
        ),
        "weekly_player_stats": pd.DataFrame(
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
                    "receiving_yards": 88,
                }
            ]
        ),
        "weekly_team_stats": pd.DataFrame([{"team": "BUF", "game_id": "g1", "points": 17}]),
    }

    artifacts = build_phase1_artifacts(extracted)
    result = load_phase1_tables(
        engine=manager.engine,
        artifacts=artifacts,
        context=PipelineRunContext(season=2025, week=1, season_type="REG"),
    )

    dim_team = pd.read_sql("SELECT * FROM dim_team", manager.engine)
    bridge_player_ids = pd.read_sql("SELECT * FROM bridge_player_ids", manager.engine)
    fact_game_pbp = pd.read_sql("SELECT * FROM fact_game_pbp", manager.engine)
    etl_log = pd.read_sql("SELECT * FROM etl_run_log", manager.engine)

    assert len(dim_team) == 2
    assert len(bridge_player_ids) == 1
    assert len(fact_game_pbp) == 1
    assert len(etl_log) == 11
    assert result["rows_written"] >= 5
    assert set(etl_log["run_status"]) <= {"success", "skipped_empty"}

    manager.engine.dispose()


def test_load_phase1_tables_continues_after_table_failure(tmp_path: Path) -> None:
    """A single table failure should be recorded but not abort subsequent tables."""
    db_path = tmp_path / "test_failure.sqlite"

    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=tmp_path,
    )
    manager = create_engine_from_settings(settings)
    manager.apply_ddl_directory("sql/ddl")

    extracted = {
        "schedules": pd.DataFrame(
            [{"game_id": "g1", "season": 2025, "season_type": "REG", "week": 1,
              "home_team": "BUF", "away_team": "KC", "gameday": "2025-09-05",
              "gametime": "20:20", "stadium": "Highmark Stadium", "status": "scheduled"}]
        ),
        "rosters": pd.DataFrame(
            [{"player_id": "p1", "player_name": "Player One", "team": "BUF",
              "position": "WR", "season": 2025}]
        ),
        "pbp": pd.DataFrame(
            [{"game_id": "g1", "play_id": 1, "season": 2025, "season_type": "REG",
              "week": 1, "posteam": "BUF", "defteam": "KC", "home_team": "BUF",
              "away_team": "KC", "play_type": "pass", "ydstogo": 10, "epa": 1.5,
              "yards_gained": 22, "down": 1, "first_down": 1, "touchdown": 0,
              "yardline_100": 45}]
        ),
        "weekly_player_stats": pd.DataFrame(
            [{"player_id": "p1", "player_name": "Player One", "recent_team": "BUF",
              "game_id": "g1", "season": 2025, "season_type": "REG", "week": 1,
              "targets": 8, "receptions": 6, "receiving_yards": 88}]
        ),
        "weekly_team_stats": pd.DataFrame([{"team": "BUF", "game_id": "g1", "points": 17}]),
    }
    artifacts = build_phase1_artifacts(extracted)

    # Drop dim_team so its load will fail with "no such table"
    with manager.engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE dim_team")

    result = load_phase1_tables(
        engine=manager.engine,
        artifacts=artifacts,
        context=PipelineRunContext(season=2025, week=1, season_type="REG"),
    )

    statuses = {r.table_name: r.run_status for r in result["table_results"]}
    assert statuses["dim_team"] == "failed"
    # Remaining tables should still have been attempted
    assert any(s == "success" for s in statuses.values())

    manager.engine.dispose()
