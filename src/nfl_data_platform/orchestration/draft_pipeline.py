"""Separate draft-data pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from nfl_data_platform.adapters.nflverse import NFLVerseAdapter
from nfl_data_platform.config import Settings
from nfl_data_platform.db.load import load_draft_tables, record_etl_step
from nfl_data_platform.orchestration.persistence import persist_draft_run
from nfl_data_platform.orchestration.pipeline import PipelineRunContext, initialize_database
from nfl_data_platform.orchestration.staging import stage_draft_data
from nfl_data_platform.quality.checks import (
    CheckResult,
    check_expected_values,
    check_foreign_key_values,
    check_non_null_columns,
    check_not_empty,
    check_recent_file,
    check_required_columns,
    check_row_count_drift,
    check_unique_key,
)
from nfl_data_platform.transforms.draft import build_dim_prospect, build_fact_draft_pick


@dataclass(slots=True)
class DraftPipelineArtifacts:
    """Container for extracted and transformed draft dataframes."""

    draft_picks: pd.DataFrame
    dim_prospect: pd.DataFrame
    fact_draft_pick: pd.DataFrame


def extract_draft_data(settings: Settings, context: PipelineRunContext) -> dict[str, pd.DataFrame]:
    """Extract bounded draft picks from nflreadpy."""
    adapter = NFLVerseAdapter(data_dir=settings.nflverse_data_dir)
    seasons = settings.nflverse_seasons
    draft_picks = adapter.fetch_draft_picks(seasons)
    if context.season is not None and "draft_year" in draft_picks.columns:
        draft_picks = draft_picks.loc[draft_picks["draft_year"] == context.season].copy()
    elif context.season is not None and "season" in draft_picks.columns:
        draft_picks = draft_picks.loc[draft_picks["season"] == context.season].copy()
    if draft_picks.empty:
        raise ValueError("Required nflreadpy draft extracts returned no rows for the requested draft year.")
    return {"draft_picks": draft_picks}


def build_draft_artifacts(extracted: dict[str, pd.DataFrame], dim_team: pd.DataFrame) -> DraftPipelineArtifacts:
    """Build draft dimensions and facts from extracted draft rows."""
    dim_prospect = build_dim_prospect(extracted["draft_picks"])
    fact_draft_pick = build_fact_draft_pick(extracted["draft_picks"])
    if not fact_draft_pick.empty and not dim_team.empty and "team" in fact_draft_pick.columns:
        lookup = dim_team.loc[:, ["team_id", "team_key"]].drop_duplicates(subset=["team_id"])
        fact_draft_pick = fact_draft_pick.merge(lookup, how="left", left_on="team", right_on="team_id")
        fact_draft_pick = fact_draft_pick.drop(columns=["team_id"], errors="ignore")
        ordered_columns = []
        for column in ["team_key", *fact_draft_pick.columns]:
            if column in fact_draft_pick.columns and column not in ordered_columns:
                ordered_columns.append(column)
        fact_draft_pick = fact_draft_pick.loc[:, ordered_columns].copy()
    return DraftPipelineArtifacts(
        draft_picks=extracted["draft_picks"],
        dim_prospect=dim_prospect,
        fact_draft_pick=fact_draft_pick,
    )


def run_draft_pipeline(settings: Settings, context: PipelineRunContext | None = None) -> dict[str, Any]:
    """Run the separate nflverse draft pipeline end to end."""
    context = context or PipelineRunContext(season_type="DRAFT")
    db_result = initialize_database(settings)
    etl_batch_id = str(uuid4())
    extracted = extract_draft_data(settings, context)
    staged_files = stage_draft_data(settings.nflverse_data_dir, context, extracted)
    _log_draft_stage_results(db_result["engine"], etl_batch_id, context, extracted)
    import warnings

    dim_team = pd.read_sql(text("SELECT team_key, team_id FROM dim_team"), db_result["engine"])
    if dim_team.empty:
        warnings.warn(
            "dim_team is empty — team_key will be NULL on all draft rows. Run run-phase1 first.",
            stacklevel=2,
        )
    artifacts = build_draft_artifacts(extracted, dim_team)
    _log_draft_transform_results(db_result["engine"], etl_batch_id, context, artifacts)
    quality_results = run_draft_quality_checks(
        artifacts=artifacts,
        context=context,
        staged_files=staged_files,
        engine=db_result["engine"],
    )
    run_output_dir = persist_draft_run(
        base_dir=settings.temp_data_dir,
        context=context,
        extracted=extracted,
        artifacts={
            "dim_prospect": artifacts.dim_prospect,
            "fact_draft_pick": artifacts.fact_draft_pick,
        },
        quality_results=quality_results,
    )
    load_result = load_draft_tables(
        engine=db_result["engine"],
        artifacts={
            "dim_prospect": artifacts.dim_prospect,
            "fact_draft_pick": artifacts.fact_draft_pick,
        },
        context=context,
        etl_batch_id=etl_batch_id,
    )
    return {
        "context": context,
        "artifacts": artifacts,
        "quality_results": quality_results,
        "staged_files": staged_files,
        "run_output_dir": run_output_dir,
        "load_result": load_result,
        "load_status": (
            f"Loaded {load_result['rows_written']} rows across "
            f"{len(load_result['table_results'])} draft tables."
        ),
    }


def run_draft_quality_checks(
    artifacts: DraftPipelineArtifacts,
    context: PipelineRunContext,
    *,
    staged_files: dict[str, Path],
    engine: Engine,
) -> list[CheckResult]:
    """Run draft-specific warehouse quality checks."""
    expected_values = {"draft_year": context.season} if context.season is not None else {}
    results = [
        check_required_columns(
            artifacts.dim_prospect,
            ["prospect_key", "player_name", "draft_year"],
            "dim_prospect",
        ),
        check_required_columns(
            artifacts.fact_draft_pick,
            ["draft_pick_key", "prospect_key", "draft_year", "draft_round", "pick_number"],
            "fact_draft_pick",
        ),
        check_unique_key(artifacts.dim_prospect, ["prospect_key"], "dim_prospect"),
        check_unique_key(artifacts.fact_draft_pick, ["draft_pick_key"], "fact_draft_pick"),
        check_non_null_columns(artifacts.dim_prospect, ["prospect_key", "player_name", "draft_year"], "dim_prospect"),
        check_non_null_columns(
            artifacts.fact_draft_pick,
            ["draft_pick_key", "prospect_key", "draft_year", "draft_round", "pick_number"],
            "fact_draft_pick",
        ),
        check_foreign_key_values(
            artifacts.fact_draft_pick,
            "prospect_key",
            artifacts.dim_prospect,
            "prospect_key",
            "fact_draft_pick.prospect_key",
        ),
    ]
    if "team_key" in artifacts.fact_draft_pick.columns:
        results.append(
            check_foreign_key_values(
                artifacts.fact_draft_pick.loc[artifacts.fact_draft_pick["team_key"].notna()],
                "team_key",
                pd.read_sql(text("SELECT team_key FROM dim_team"), engine),
                "team_key",
                "fact_draft_pick.team_key",
            )
        )

    for name, frame in {
        "dim_prospect": artifacts.dim_prospect,
        "fact_draft_pick": artifacts.fact_draft_pick,
    }.items():
        if not frame.empty:
            results.append(check_not_empty(frame, name))
            if expected_values:
                results.append(check_expected_values(frame, expected_values, name))
            results.append(
                check_row_count_drift(
                    len(frame),
                    _fetch_previous_draft_row_count(engine, name, context),
                    name,
                )
            )
    for name, path in staged_files.items():
        results.append(check_recent_file(path, f"staged:{name}"))
    return results


def _log_draft_stage_results(
    engine: Engine,
    etl_batch_id: str,
    context: PipelineRunContext,
    extracted: dict[str, pd.DataFrame],
) -> None:
    """Record draft extract step row counts in the ETL log."""
    timestamp = datetime.now(UTC)
    for dataset_name, frame in extracted.items():
        record_etl_step(
            engine,
            etl_batch_id=etl_batch_id,
            pipeline_name="draft",
            step_name=f"extract_{dataset_name}",
            source_name="nflreadpy",
            context=context,
            run_status="success",
            rows_written=len(frame),
            started_at=timestamp,
            finished_at=timestamp,
        )


def _log_draft_transform_results(
    engine: Engine,
    etl_batch_id: str,
    context: PipelineRunContext,
    artifacts: DraftPipelineArtifacts,
) -> None:
    """Record draft transform step row counts in the ETL log."""
    timestamp = datetime.now(UTC)
    for table_name in ["dim_prospect", "fact_draft_pick"]:
        frame = getattr(artifacts, table_name)
        record_etl_step(
            engine,
            etl_batch_id=etl_batch_id,
            pipeline_name="draft",
            step_name=f"transform_{table_name}",
            source_name="nflverse",
            context=context,
            run_status="success",
            rows_written=len(frame),
            started_at=timestamp,
            finished_at=timestamp,
        )


def _fetch_previous_draft_row_count(engine: Engine, step_name: str, context: PipelineRunContext) -> int | None:
    """Fetch the most recent successful draft row count for the requested draft year."""
    history = pd.read_sql_query(
        text("""
        SELECT rows_written
        FROM etl_run_log
        WHERE pipeline_name = 'draft'
          AND step_name = :step_name
          AND run_status = 'success'
          AND season = :season
        ORDER BY finished_at DESC
        LIMIT 1
        """),
        engine,
        params={"step_name": step_name, "season": context.season},
    )
    if history.empty:
        return None
    return int(history.loc[0, "rows_written"])
