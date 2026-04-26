"""Deterministic data quality checks for transformed outputs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class CheckResult:
    """Structured quality check result."""

    check_name: str
    target_name: str
    passed: bool
    detail: str


def check_required_columns(frame: pd.DataFrame, required_columns: list[str], target_name: str) -> CheckResult:
    """Ensure required columns are present."""
    missing = [column for column in required_columns if column not in frame.columns]
    return CheckResult(
        check_name="required_columns",
        target_name=target_name,
        passed=not missing,
        detail="missing columns: " + ", ".join(missing) if missing else "all required columns present",
    )


def check_not_empty(frame: pd.DataFrame, target_name: str) -> CheckResult:
    """Ensure a dataframe is not empty."""
    return CheckResult(
        check_name="not_empty",
        target_name=target_name,
        passed=not frame.empty,
        detail="frame contains rows" if not frame.empty else "frame is empty",
    )


def check_unique_key(frame: pd.DataFrame, key_columns: list[str], target_name: str) -> CheckResult:
    """Ensure key columns define unique rows."""
    if frame.empty:
        return CheckResult("unique_key", target_name, True, "frame is empty")
    duplicates = frame.duplicated(subset=key_columns).sum()
    return CheckResult(
        check_name="unique_key",
        target_name=target_name,
        passed=duplicates == 0,
        detail="keys are unique" if duplicates == 0 else f"found {duplicates} duplicate rows",
    )


def check_non_null_columns(frame: pd.DataFrame, required_columns: list[str], target_name: str) -> CheckResult:
    """Ensure key columns do not contain null values."""
    if frame.empty:
        return CheckResult("non_null_columns", target_name, True, "frame is empty")
    null_columns = [column for column in required_columns if frame[column].isna().any()]
    return CheckResult(
        check_name="non_null_columns",
        target_name=target_name,
        passed=not null_columns,
        detail="required columns are non-null"
        if not null_columns
        else "nulls found in: " + ", ".join(null_columns),
    )
