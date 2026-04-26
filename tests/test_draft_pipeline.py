"""Tests for the draft pipeline flow."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pandas as pd

from nfl_data_platform.config import Settings
from nfl_data_platform.db.engine import create_engine_from_settings
from nfl_data_platform.db.load import load_draft_tables
from nfl_data_platform.orchestration.draft_pipeline import (
    PipelineRunContext,
    build_draft_artifacts,
    run_draft_pipeline,
    run_draft_quality_checks,
)


def test_load_draft_tables_writes_rows_and_etl_log() -> None:
    db_path = Path(f"data/temp/test_draft_load_{uuid4().hex}.sqlite")
    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=Path("./data/temp"),
    )
    manager = create_engine_from_settings(settings)
    manager.apply_ddl_directory("sql/ddl")

    dim_team = pd.DataFrame(
        [
            {
                "team_key": "ten",
                "team_id": "TEN",
                "team_abbr": "TEN",
                "team_name": "Tennessee Titans",
                "first_season": 1999,
                "last_seen_season": 2025,
            }
        ]
    )
    dim_team.to_sql("dim_team", manager.engine, if_exists="append", index=False)
    extracted = {
        "draft_picks": pd.DataFrame(
            [
                {
                    "draft_year": 2025,
                    "round": 1,
                    "pick": 1,
                    "pick_overall": 1,
                    "team": "TEN",
                    "player_name": "Cam Ward",
                    "player_id": "00-0001",
                    "college_name": "Miami",
                    "position": "QB",
                }
            ]
        )
    }

    artifacts = build_draft_artifacts(extracted, dim_team)
    result = load_draft_tables(
        engine=manager.engine,
        artifacts={
            "dim_prospect": artifacts.dim_prospect,
            "fact_draft_pick": artifacts.fact_draft_pick,
        },
        context=PipelineRunContext(season=2025, season_type="DRAFT"),
    )

    dim_prospect = pd.read_sql("SELECT * FROM dim_prospect", manager.engine)
    fact_draft_pick = pd.read_sql("SELECT * FROM fact_draft_pick", manager.engine)
    etl_log = pd.read_sql("SELECT * FROM etl_run_log WHERE pipeline_name = 'draft'", manager.engine)

    assert len(dim_prospect) == 1
    assert len(fact_draft_pick) == 1
    assert len(etl_log) == 2
    assert result["rows_written"] == 2

    manager.engine.dispose()
    db_path.unlink()


def test_run_draft_quality_checks_detects_missing_prospect_reference() -> None:
    artifacts = build_draft_artifacts(
        {
            "draft_picks": pd.DataFrame(
                [
                    {
                        "draft_year": 2025,
                        "round": 1,
                        "pick": 1,
                        "pick_overall": 1,
                        "team": "TEN",
                        "player_name": "Cam Ward",
                        "player_id": "00-0001",
                    }
                ]
            )
        },
        dim_team=pd.DataFrame([{"team_key": "ten", "team_id": "TEN"}]),
    )
    broken_artifacts = artifacts.__class__(
        draft_picks=artifacts.draft_picks,
        dim_prospect=artifacts.dim_prospect.iloc[0:0].copy(),
        fact_draft_pick=artifacts.fact_draft_pick,
    )

    db_path = Path(f"data/temp/test_draft_qc_{uuid4().hex}.sqlite")
    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        nflverse_seasons=(2025,),
        nflverse_data_dir=Path("./data"),
        temp_data_dir=Path("./data/temp"),
    )
    manager = create_engine_from_settings(settings)
    manager.apply_ddl_directory("sql/ddl")
    pd.DataFrame(
        [
            {
                "team_key": "ten",
                "team_id": "TEN",
                "team_abbr": "TEN",
                "team_name": "Tennessee Titans",
                "first_season": 1999,
                "last_seen_season": 2025,
            }
        ]
    ).to_sql("dim_team", manager.engine, if_exists="append", index=False)

    draft_root = Path(f"data/temp/test_draft_stage_{uuid4().hex}")
    draft_root.mkdir(parents=True, exist_ok=True)
    staged = draft_root / "draft_picks.csv"
    broken_artifacts.draft_picks.to_csv(staged, index=False)

    results = run_draft_quality_checks(
        artifacts=broken_artifacts,
        context=PipelineRunContext(season=2025, season_type="DRAFT"),
        staged_files={"draft_picks": staged},
        engine=manager.engine,
    )

    assert any(not result.passed and result.check_name == "foreign_key_values" for result in results)

    manager.engine.dispose()
    db_path.unlink()
    staged.unlink()
    draft_root.rmdir()


def test_run_draft_pipeline_writes_staged_and_csv_outputs(monkeypatch) -> None:
    test_root = Path("data/temp") / f"test_draft_pipeline_{uuid4().hex}"
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        nflverse_seasons=(2025,),
        nflverse_data_dir=test_root / "nflverse",
        temp_data_dir=test_root / "temp",
    )
    extracted = {
        "draft_picks": pd.DataFrame(
            [
                {
                    "draft_year": 2025,
                    "round": 1,
                    "pick": 1,
                    "pick_overall": 1,
                    "team": "TEN",
                    "player_name": "Cam Ward",
                    "player_id": "00-0001",
                    "college_name": "Miami",
                    "position": "QB",
                }
            ]
        )
    }

    monkeypatch.setattr(
        "nfl_data_platform.orchestration.draft_pipeline.extract_draft_data",
        lambda _settings, _context: extracted,
    )

    result = run_draft_pipeline(
        settings=settings,
        context=PipelineRunContext(season=2025, season_type="DRAFT"),
    )

    run_dir = Path(result["run_output_dir"])
    assert run_dir.exists()
    assert (run_dir / "extracted" / "draft_picks.csv").exists()
    assert (run_dir / "transformed" / "dim_prospect.csv").exists()
    assert (run_dir / "transformed" / "fact_draft_pick.csv").exists()
    assert (run_dir / "quality_results.csv").exists()
    assert result["staged_files"]["draft_picks"].exists()
