"""Tests for CLI wiring."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from nfl_data_platform.orchestration import cli


def test_init_db_command_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(
        cli,
        "initialize_database",
        lambda settings: {"status": "initialized", "executed_ddl_files": ["dim_team.sql"]},
    )
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "init-db"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "initialized" in output
    assert "dim_team.sql" in output


def test_run_phase1_command_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(
        cli,
        "run_phase1_pipeline",
        lambda settings, context: {
            "quality_results": [object(), object()],
            "run_output_dir": "data/temp/season_2025/week_all/reg_incremental",
            "load_status": "Loaded 12 rows across 8 Phase 1 tables.",
        },
    )
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "run-phase1", "--season", "2025"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "2 quality check results" in output
    assert "CSV output directory" in output


def test_run_draft_command_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(
        cli,
        "run_draft_pipeline",
        lambda settings, context: {
            "quality_results": [object()],
            "run_output_dir": "data/temp/draft/season_2025/incremental",
            "load_status": "Loaded 32 rows across 2 draft tables.",
        },
    )
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "run-draft", "--season", "2025"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Draft pipeline completed with 1 quality check results." in output
    assert "CSV output directory" in output


def test_check_db_command_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(
        cli,
        "create_engine_from_settings",
        lambda settings: SimpleNamespace(
            check_connection=lambda: SimpleNamespace(
                status="ok",
                driver="sqlite+pysqlite",
                dialect="sqlite",
                database=":memory:",
                server_version="3.45.1",
            )
        ),
    )
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "check-db"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Database connectivity: ok" in output
    assert "Dialect: sqlite" in output
