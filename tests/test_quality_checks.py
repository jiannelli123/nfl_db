"""Tests for quality check helpers."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.quality.checks import (
    check_non_null_columns,
    check_not_empty,
    check_required_columns,
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
