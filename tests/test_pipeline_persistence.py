"""Tests for Phase 1 CSV persistence."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from uuid import uuid4

from nfl_data_platform.config import Settings
from nfl_data_platform.orchestration.pipeline import PipelineRunContext, run_phase1_pipeline


def test_run_phase1_pipeline_writes_csv_outputs(
    monkeypatch,
) -> None:
    test_root = Path("data/temp") / f"test_pipeline_persistence_{uuid4().hex}"

    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        nflverse_seasons=(2025,),
        nflverse_data_dir=test_root / "nflverse",
        temp_data_dir=test_root / "temp",
    )

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
                    "home_team": "BUF",
                    "away_team": "KC",
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

    monkeypatch.setattr(
        "nfl_data_platform.orchestration.pipeline.extract_phase1_data",
        lambda _settings, _context: extracted,
    )

    result = run_phase1_pipeline(
        settings=settings,
        context=PipelineRunContext(season=2025, week=1, season_type="REG", full_refresh=False),
    )

    run_dir = Path(result["run_output_dir"])
    assert run_dir.exists()
    assert (run_dir / "extracted" / "schedules.csv").exists()
    assert (run_dir / "extracted" / "pbp.csv").exists()
    assert (run_dir / "transformed" / "dim_team.csv").exists()
    assert (run_dir / "transformed" / "bridge_player_ids.csv").exists()
    assert (run_dir / "transformed" / "fact_game_pbp.csv").exists()
    assert (run_dir / "transformed" / "fact_team_offense.csv").exists()
    assert (run_dir / "quality_results.csv").exists()
    assert result["staged_files"]["schedules"].exists()

    quality_results = pd.read_csv(run_dir / "quality_results.csv")
    assert set(quality_results.columns) == {"check_name", "target_name", "passed", "detail"}
    assert not quality_results.empty
    assert result["load_result"]["rows_written"] >= 5
