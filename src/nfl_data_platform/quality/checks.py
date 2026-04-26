"""Deterministic data quality checks for transformed outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

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


def check_expected_values(
    frame: pd.DataFrame,
    expected_values: dict[str, object],
    target_name: str,
) -> CheckResult:
    """Ensure rows match expected scalar values for requested columns."""
    if frame.empty:
        return CheckResult("expected_values", target_name, True, "frame is empty")
    mismatched: list[str] = []
    for column, expected in expected_values.items():
        if column not in frame.columns:
            mismatched.append(f"{column} missing")
            continue
        if frame[column].dropna().empty:
            continue
        if not frame[column].dropna().eq(expected).all():
            mismatched.append(f"{column}!={expected}")
    return CheckResult(
        check_name="expected_values",
        target_name=target_name,
        passed=not mismatched,
        detail="all expected values present" if not mismatched else "mismatches: " + ", ".join(mismatched),
    )


def check_matching_row_counts(
    left_frame: pd.DataFrame,
    right_frame: pd.DataFrame,
    left_name: str,
    right_name: str,
) -> CheckResult:
    """Ensure two frames contain the same row count."""
    passed = len(left_frame) == len(right_frame)
    return CheckResult(
        check_name="matching_row_counts",
        target_name=f"{left_name}:{right_name}",
        passed=passed,
        detail=f"row counts match at {len(left_frame)}" if passed else f"{left_name}={len(left_frame)}, {right_name}={len(right_frame)}",
    )


def check_team_play_reconciliation(
    fact_game_pbp: pd.DataFrame,
    fact_team_offense: pd.DataFrame,
) -> CheckResult:
    """Ensure aggregated offensive play counts align between play and team facts."""
    if fact_game_pbp.empty or fact_team_offense.empty:
        return CheckResult("team_play_reconciliation", "fact_game_pbp:fact_team_offense", True, "frame is empty")
    required_pbp = {"posteam", "game_id", "season", "season_type", "week"}
    required_team = {"team", "game_id", "season", "season_type", "week", "plays"}
    if not required_pbp.issubset(fact_game_pbp.columns) or not required_team.issubset(fact_team_offense.columns):
        return CheckResult("team_play_reconciliation", "fact_game_pbp:fact_team_offense", False, "required columns missing")

    pbp_counts = (
        fact_game_pbp.loc[fact_game_pbp["posteam"].notna()]
        .groupby(["posteam", "game_id", "season", "season_type", "week"], as_index=False)
        .size()
        .rename(columns={"posteam": "team", "size": "pbp_plays"})
    )
    offense_counts = fact_team_offense.loc[:, ["team", "game_id", "season", "season_type", "week", "plays"]].copy()
    merged = offense_counts.merge(
        pbp_counts,
        how="outer",
        on=["team", "game_id", "season", "season_type", "week"],
    ).fillna(0)
    mismatched = merged.loc[merged["plays"] != merged["pbp_plays"]]
    return CheckResult(
        check_name="team_play_reconciliation",
        target_name="fact_game_pbp:fact_team_offense",
        passed=mismatched.empty,
        detail="play counts reconcile" if mismatched.empty else f"found {len(mismatched)} mismatched team-game rows",
    )


def check_foreign_key_values(
    frame: pd.DataFrame,
    column: str,
    reference_frame: pd.DataFrame,
    reference_column: str,
    target_name: str,
) -> CheckResult:
    """Ensure a value set resolves into a reference dataframe."""
    if frame.empty or column not in frame.columns:
        return CheckResult("foreign_key_values", target_name, True, "frame is empty or column missing")
    if reference_frame.empty or reference_column not in reference_frame.columns:
        return CheckResult("foreign_key_values", target_name, False, "reference frame missing")
    values = set(frame[column].dropna().astype(str))
    allowed = set(reference_frame[reference_column].dropna().astype(str))
    missing = sorted(values - allowed)
    return CheckResult(
        check_name="foreign_key_values",
        target_name=target_name,
        passed=not missing,
        detail="all foreign keys resolved" if not missing else "unresolved values: " + ", ".join(missing[:10]),
    )


def check_missing_weeks(
    frame: pd.DataFrame,
    target_name: str,
    expected_week: int | None = None,
) -> CheckResult:
    """Ensure requested weekly coverage is present without gaps."""
    if frame.empty or "week" not in frame.columns:
        return CheckResult("missing_weeks", target_name, True, "frame is empty or has no week column")
    observed = sorted(pd.to_numeric(frame["week"], errors="coerce").dropna().astype(int).unique().tolist())
    if not observed:
        return CheckResult("missing_weeks", target_name, False, "no observed weeks")
    if expected_week is not None:
        passed = expected_week in observed
        return CheckResult(
            check_name="missing_weeks",
            target_name=target_name,
            passed=passed,
            detail=f"week {expected_week} present" if passed else f"week {expected_week} missing; observed={observed}",
        )
    expected_range = list(range(min(observed), max(observed) + 1))
    missing = [str(week) for week in expected_range if week not in observed]
    return CheckResult(
        check_name="missing_weeks",
        target_name=target_name,
        passed=not missing,
        detail="no week gaps detected" if not missing else "missing weeks: " + ", ".join(missing),
    )


def check_row_count_drift(
    current_row_count: int,
    previous_row_count: int | None,
    target_name: str,
    threshold_ratio: float = 0.5,
) -> CheckResult:
    """Flag material row-count drift relative to a prior successful run."""
    if previous_row_count is None:
        return CheckResult("row_count_drift", target_name, True, "no prior row count available")
    if previous_row_count == 0:
        passed = current_row_count == 0
        return CheckResult(
            check_name="row_count_drift",
            target_name=target_name,
            passed=passed,
            detail="both runs are zero-row" if passed else f"previous=0 current={current_row_count}",
        )
    delta_ratio = abs(current_row_count - previous_row_count) / previous_row_count
    passed = delta_ratio <= threshold_ratio
    return CheckResult(
        check_name="row_count_drift",
        target_name=target_name,
        passed=passed,
        detail=(
            f"current={current_row_count} previous={previous_row_count}"
            if passed
            else f"drift {delta_ratio:.2%} exceeds threshold; current={current_row_count} previous={previous_row_count}"
        ),
    )


def check_recent_file(path: Path, target_name: str, max_age_hours: int = 24) -> CheckResult:
    """Ensure a staged file exists and was updated within the freshness window."""
    if not path.exists():
        return CheckResult("freshness", target_name, False, "file does not exist")
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    passed = datetime.now(UTC) - modified_at <= timedelta(hours=max_age_hours)
    return CheckResult(
        check_name="freshness",
        target_name=target_name,
        passed=passed,
        detail=f"file modified at {modified_at.isoformat()}",
    )
