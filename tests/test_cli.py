"""Tests for CLI wiring."""

from __future__ import annotations

import sys

import pytest

from nfl_data_platform.orchestration import cli


def test_init_db_command_runs(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(cli, "initialize_database", lambda settings: {"status": "initialized"})
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "init-db"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "initialized" in output


def test_run_phase1_command_runs(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("NFLVERSE_SEASONS", "2025")
    monkeypatch.setattr(
        cli,
        "run_phase1_pipeline",
        lambda settings, context: {
            "quality_results": [object(), object()],
            "run_output_dir": "data/temp/season_2025/week_all/reg_incremental",
            "load_status": "CSV snapshots written for validation.",
        },
    )
    monkeypatch.setattr(sys, "argv", ["nfl-data-platform", "run-phase1", "--season", "2025"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "2 quality check results" in output
    assert "CSV output directory" in output
