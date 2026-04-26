"""Tests for quality check helpers."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.quality.checks import (
    check_expected_values,
    check_matching_row_counts,
    check_non_null_columns,
    check_not_empty,
    check_required_columns,
    check_row_count_drift,
    check_team_play_reconciliation,
    check_unique_key,
)


def test_check_required_columns_detects_missing_fields() -> None:
    frame = pd.DataFrame([{"team_key": "buf"}])

    result = check_required_columns(frame, ["team_key", "team_id"], "dim_team")

    assert not result.passed
    assert "team_id" in result.detail


def test_check_unique_key_detects_duplicates() -> None:
    frame = pd.DataFrame([{"team_key": "buf"}, {"team_key": "buf"}])

    result = check_unique_key(frame, ["team_key"], "dim_team")

    assert not result.passed


def test_check_non_null_columns_detects_nulls() -> None:
    frame = pd.DataFrame([{"team_key": None}])

    result = check_non_null_columns(frame, ["team_key"], "dim_team")

    assert not result.passed


def test_check_not_empty_passes_for_rows() -> None:
    frame = pd.DataFrame([{"team_key": "buf"}])

    result = check_not_empty(frame, "dim_team")

    assert result.passed


def test_check_expected_values_detects_mismatch() -> None:
    frame = pd.DataFrame([{"season": 2024}])

    result = check_expected_values(frame, {"season": 2025}, "dim_game")

    assert not result.passed


def test_check_matching_row_counts_detects_difference() -> None:
    left = pd.DataFrame([{"x": 1}])
    right = pd.DataFrame([{"x": 1}, {"x": 2}])

    result = check_matching_row_counts(left, right, "left", "right")

    assert not result.passed


def test_check_row_count_drift_passes_within_threshold() -> None:
    result = check_row_count_drift(current_row_count=90, previous_row_count=100, target_name="t")

    assert result.passed


def test_check_row_count_drift_fails_above_threshold() -> None:
    result = check_row_count_drift(current_row_count=49, previous_row_count=100, target_name="t")

    assert not result.passed


def test_check_row_count_drift_passes_at_exact_threshold() -> None:
    result = check_row_count_drift(current_row_count=50, previous_row_count=100, target_name="t")

    assert result.passed


def test_check_row_count_drift_passes_with_no_prior_count() -> None:
    result = check_row_count_drift(current_row_count=100, previous_row_count=None, target_name="t")

    assert result.passed


def test_check_team_play_reconciliation_detects_mismatch() -> None:
    fact_game_pbp = pd.DataFrame(
        [
            {"posteam": "BUF", "game_id": "g1", "season": 2025, "season_type": "REG", "week": 1},
        ]
    )
    fact_team_offense = pd.DataFrame(
        [
            {"team": "BUF", "game_id": "g1", "season": 2025, "season_type": "REG", "week": 1, "plays": 2},
        ]
    )

    result = check_team_play_reconciliation(fact_game_pbp, fact_team_offense)

    assert not result.passed
