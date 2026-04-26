"""Phase 3 nflverse pipeline orchestration."""

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
from nfl_data_platform.db.engine import create_engine_from_settings
from nfl_data_platform.db.load import load_phase1_tables, record_etl_step
from nfl_data_platform.orchestration.persistence import persist_phase1_run
from nfl_data_platform.orchestration.staging import stage_extracted_data
from nfl_data_platform.quality.checks import (
    CheckResult,
    check_expected_values,
    check_foreign_key_values,
    check_matching_row_counts,
    check_missing_weeks,
    check_non_null_columns,
    check_not_empty,
    check_recent_file,
    check_required_columns,
    check_row_count_drift,
    check_team_play_reconciliation,
    check_unique_key,
)
from nfl_data_platform.transforms.bridge_player_ids import build_bridge_player_ids
from nfl_data_platform.transforms.dimensions import build_dim_game, build_dim_player, build_dim_team
from nfl_data_platform.transforms.game_pbp import build_fact_game_pbp
from nfl_data_platform.transforms.player_defense import build_fact_player_defense
from nfl_data_platform.transforms.player_offense import build_fact_player_offense
from nfl_data_platform.transforms.player_special_teams import build_fact_player_special_teams
from nfl_data_platform.transforms.team_defense import build_fact_team_defense
from nfl_data_platform.transforms.team_offense import build_fact_team_offense
from nfl_data_platform.transforms.team_special_teams import build_fact_team_special_teams


@dataclass(slots=True)
class PipelineArtifacts:
    """Container for extracted and transformed warehouse dataframes."""

    schedules: pd.DataFrame
    rosters: pd.DataFrame
    pbp: pd.DataFrame
    weekly_player_stats: pd.DataFrame
    weekly_team_stats: pd.DataFrame
    dim_team: pd.DataFrame
    dim_player: pd.DataFrame
    dim_game: pd.DataFrame
    bridge_player_ids: pd.DataFrame
    fact_game_pbp: pd.DataFrame
    fact_team_offense: pd.DataFrame
    fact_team_defense: pd.DataFrame
    fact_player_offense: pd.DataFrame
    fact_team_special_teams: pd.DataFrame
    fact_player_defense: pd.DataFrame
    fact_player_special_teams: pd.DataFrame


@dataclass(slots=True)
class PipelineRunContext:
    """Execution parameters for a bounded pipeline run."""

    season: int | None = None
    week: int | None = None
    season_type: str = "REG"
    full_refresh: bool = False


def extract_phase1_data(settings: Settings, context: PipelineRunContext) -> dict[str, pd.DataFrame]:
    """Extract and bound nflreadpy inputs for the requested run window."""
    adapter = NFLVerseAdapter(data_dir=settings.nflverse_data_dir)
    seasons = settings.nflverse_seasons
    extracted = {
        "schedules": adapter.fetch_schedules(seasons),
        "rosters": adapter.fetch_rosters(seasons),
        "pbp": adapter.fetch_play_by_play(seasons),
        "weekly_player_stats": adapter.fetch_weekly_player_stats(seasons),
        "weekly_team_stats": adapter.fetch_weekly_team_stats(seasons),
    }
    filtered = {
        "schedules": _filter_run_window(extracted["schedules"], context, filter_week=True),
        "rosters": _filter_run_window(extracted["rosters"], context, filter_week=False),
        "pbp": _filter_run_window(extracted["pbp"], context, filter_week=True),
        "weekly_player_stats": _filter_run_window(extracted["weekly_player_stats"], context, filter_week=True),
        "weekly_team_stats": _filter_run_window(extracted["weekly_team_stats"], context, filter_week=True),
    }
    _validate_extracted_inputs(filtered)
    return filtered


def build_phase1_artifacts(extracted: dict[str, pd.DataFrame]) -> PipelineArtifacts:
    """Build warehouse dimensions, bridge rows, and facts from extracted frames."""
    weekly_team_stats = _enrich_with_schedule_context(extracted["weekly_team_stats"], extracted["schedules"])
    weekly_player_stats = _enrich_with_schedule_context(extracted["weekly_player_stats"], extracted["schedules"])
    dim_team = build_dim_team(rosters=extracted["rosters"], schedules=extracted["schedules"])
    dim_player = build_dim_player(rosters=extracted["rosters"])
    dim_game = build_dim_game(schedules=extracted["schedules"])
    bridge_player_ids = build_bridge_player_ids(dim_player)
    fact_game_pbp = build_fact_game_pbp(extracted["pbp"])
    fact_team_offense = _attach_team_keys(
        build_fact_team_offense(extracted["pbp"], weekly_team_stats),
        dim_team,
    )
    fact_team_defense = _attach_team_keys(
        build_fact_team_defense(extracted["pbp"], weekly_team_stats),
        dim_team,
    )
    fact_player_offense = _attach_player_and_team_keys(
        build_fact_player_offense(weekly_player_stats),
        dim_player=dim_player,
        dim_team=dim_team,
    )
    fact_team_special_teams = _attach_team_keys(
        build_fact_team_special_teams(weekly_team_stats),
        dim_team,
    )
    fact_player_defense = _attach_player_and_team_keys(
        build_fact_player_defense(weekly_player_stats),
        dim_player=dim_player,
        dim_team=dim_team,
    )
    fact_player_special_teams = _attach_player_and_team_keys(
        build_fact_player_special_teams(weekly_player_stats),
        dim_player=dim_player,
        dim_team=dim_team,
    )
    return PipelineArtifacts(
        schedules=extracted["schedules"],
        rosters=extracted["rosters"],
        pbp=extracted["pbp"],
        weekly_player_stats=weekly_player_stats,
        weekly_team_stats=weekly_team_stats,
        dim_team=dim_team,
        dim_player=dim_player,
        dim_game=dim_game,
        bridge_player_ids=bridge_player_ids,
        fact_game_pbp=fact_game_pbp,
        fact_team_offense=fact_team_offense,
        fact_team_defense=fact_team_defense,
        fact_player_offense=fact_player_offense,
        fact_team_special_teams=fact_team_special_teams,
        fact_player_defense=fact_player_defense,
        fact_player_special_teams=fact_player_special_teams,
    )


def initialize_database(settings: Settings) -> dict[str, Any]:
    """Create a database engine and execute warehouse DDL files."""
    manager = create_engine_from_settings(settings)
    ddl_result = manager.apply_ddl_directory("sql/ddl")
    return {
        "manager": manager,
        "engine": manager.engine,
        "status": "initialized",
        "executed_ddl_files": ddl_result["executed_files"],
    }


def run_phase1_pipeline(settings: Settings, context: PipelineRunContext | None = None) -> dict[str, Any]:
    """Run the current nflverse pipeline end to end."""
    context = context or PipelineRunContext()
    db_result = initialize_database(settings)
    etl_batch_id = str(uuid4())
    extracted = extract_phase1_data(settings, context)
    staged_files = stage_extracted_data(settings.nflverse_data_dir, context, extracted)
    _log_stage_results(db_result["engine"], etl_batch_id, context, extracted)
    artifacts = build_phase1_artifacts(extracted)
    _log_transform_results(db_result["engine"], etl_batch_id, context, artifacts)
    quality_results = run_quality_checks(
        artifacts=artifacts,
        context=context,
        staged_files=staged_files,
        engine=db_result["engine"],
    )
    run_output_dir = persist_phase1_run(
        base_dir=settings.temp_data_dir,
        context=context,
        extracted=extracted,
        artifacts=artifacts,
        quality_results=quality_results,
    )
    load_result = load_phase1_tables(
        engine=db_result["engine"],
        artifacts=artifacts,
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
            f"{len(load_result['table_results'])} warehouse tables."
        ),
    }


def run_quality_checks(
    artifacts: PipelineArtifacts,
    context: PipelineRunContext,
    *,
    staged_files: dict[str, Path],
    engine: Engine,
) -> list[CheckResult]:
    """Run warehouse quality checks across transformed outputs and staged files."""
    expected_values: dict[str, object] = {}
    if context.season is not None:
        expected_values["season"] = context.season
    if context.week is not None:
        expected_values["week"] = context.week
    expected_values["season_type"] = context.season_type

    results = [
        check_required_columns(artifacts.dim_team, ["team_key", "team_id"], "dim_team"),
        check_required_columns(artifacts.dim_player, ["player_key", "player_id"], "dim_player"),
        check_required_columns(artifacts.dim_game, ["game_key", "game_id"], "dim_game"),
        check_required_columns(
            artifacts.bridge_player_ids,
            ["bridge_player_ids_key", "player_key", "nflverse_player_id"],
            "bridge_player_ids",
        ),
        check_required_columns(artifacts.fact_game_pbp, ["pbp_key", "game_id", "play_id"], "fact_game_pbp"),
        check_required_columns(
            artifacts.fact_player_defense,
            ["player_defense_key", "player_id", "game_id"],
            "fact_player_defense",
        ),
        check_unique_key(artifacts.dim_team, ["team_key"], "dim_team"),
        check_unique_key(artifacts.dim_player, ["player_key"], "dim_player"),
        check_unique_key(artifacts.dim_game, ["game_key"], "dim_game"),
        check_unique_key(artifacts.bridge_player_ids, ["bridge_player_ids_key"], "bridge_player_ids"),
        check_unique_key(artifacts.fact_game_pbp, ["pbp_key"], "fact_game_pbp"),
        check_unique_key(
            artifacts.fact_player_offense,
            ["player_id", "game_id", "season", "season_type", "week"],
            "fact_player_offense",
        ),
        check_unique_key(
            artifacts.fact_player_defense,
            ["player_id", "game_id", "season", "season_type", "week"],
            "fact_player_defense",
        ),
        check_unique_key(
            artifacts.fact_team_special_teams,
            ["team", "game_id", "season", "season_type", "week"],
            "fact_team_special_teams",
        ),
        check_unique_key(
            artifacts.fact_player_special_teams,
            ["player_id", "game_id", "season", "season_type", "week"],
            "fact_player_special_teams",
        ),
        check_non_null_columns(artifacts.dim_team, ["team_key", "team_id"], "dim_team"),
        check_non_null_columns(artifacts.dim_player, ["player_key", "player_id"], "dim_player"),
        check_non_null_columns(artifacts.dim_game, ["game_key", "game_id"], "dim_game"),
        check_non_null_columns(
            artifacts.bridge_player_ids,
            ["bridge_player_ids_key", "player_key", "nflverse_player_id"],
            "bridge_player_ids",
        ),
        check_non_null_columns(artifacts.fact_game_pbp, ["pbp_key", "game_id", "play_id"], "fact_game_pbp"),
        check_non_null_columns(
            artifacts.fact_player_defense,
            ["player_defense_key", "player_id", "game_id"],
            "fact_player_defense",
        ),
        check_matching_row_counts(artifacts.bridge_player_ids, artifacts.dim_player, "bridge_player_ids", "dim_player"),
        check_matching_row_counts(artifacts.fact_team_offense, artifacts.fact_team_defense, "fact_team_offense", "fact_team_defense"),
        check_team_play_reconciliation(artifacts.fact_game_pbp, artifacts.fact_team_offense),
        check_foreign_key_values(artifacts.bridge_player_ids, "player_key", artifacts.dim_player, "player_key", "bridge_player_ids.player_key"),
        check_foreign_key_values(artifacts.fact_game_pbp, "game_id", artifacts.dim_game, "game_id", "fact_game_pbp.game_id"),
        check_foreign_key_values(artifacts.fact_team_offense, "team", artifacts.dim_team, "team_id", "fact_team_offense.team"),
        check_foreign_key_values(artifacts.fact_team_defense, "team", artifacts.dim_team, "team_id", "fact_team_defense.team"),
        check_foreign_key_values(artifacts.fact_team_special_teams, "team", artifacts.dim_team, "team_id", "fact_team_special_teams.team"),
        check_foreign_key_values(artifacts.fact_player_offense, "player_id", artifacts.dim_player, "player_id", "fact_player_offense.player_id"),
        check_foreign_key_values(artifacts.fact_player_defense, "player_id", artifacts.dim_player, "player_id", "fact_player_defense.player_id"),
        check_foreign_key_values(artifacts.fact_player_special_teams, "player_id", artifacts.dim_player, "player_id", "fact_player_special_teams.player_id"),
    ]

    scoped_frames = {
        "dim_game": artifacts.dim_game,
        "fact_game_pbp": artifacts.fact_game_pbp,
        "fact_team_offense": artifacts.fact_team_offense,
        "fact_team_defense": artifacts.fact_team_defense,
        "fact_player_offense": artifacts.fact_player_offense,
        "fact_team_special_teams": artifacts.fact_team_special_teams,
        "fact_player_defense": artifacts.fact_player_defense,
        "fact_player_special_teams": artifacts.fact_player_special_teams,
    }
    for name, frame in scoped_frames.items():
        if not frame.empty:
            results.append(check_expected_values(frame, expected_values, name))
            results.append(check_not_empty(frame, name))
            results.append(check_missing_weeks(frame, name, expected_week=context.week))
            results.append(
                check_row_count_drift(
                    current_row_count=len(frame),
                    previous_row_count=_fetch_previous_row_count(engine, name, context),
                    target_name=name,
                )
            )
    for name, path in staged_files.items():
        results.append(check_recent_file(path, f"staged:{name}"))
    return results


def _filter_run_window(
    frame: pd.DataFrame,
    context: PipelineRunContext,
    filter_week: bool,
) -> pd.DataFrame:
    """Filter extracted data to the requested run window when columns are present."""
    filtered = frame.copy()
    if filtered.empty:
        return filtered
    if context.season is not None and "season" in filtered.columns:
        filtered = filtered.loc[filtered["season"] == context.season].copy()
    if "season_type" in filtered.columns:
        filtered = filtered.loc[filtered["season_type"].fillna(context.season_type) == context.season_type].copy()
    if filter_week and context.week is not None and "week" in filtered.columns:
        filtered = filtered.loc[filtered["week"] == context.week].copy()
    return filtered


_REQUIRED_DATASETS: frozenset[str] = frozenset(["schedules", "rosters", "pbp"])


def _validate_extracted_inputs(extracted: dict[str, pd.DataFrame]) -> None:
    """Fail fast when core required datasets are empty; warn for optional ones."""
    import warnings

    empty_required = [name for name in _REQUIRED_DATASETS if extracted.get(name, pd.DataFrame()).empty]
    if empty_required:
        raise ValueError(
            "Required nflreadpy extracts returned no rows for: " + ", ".join(sorted(empty_required))
        )
    empty_optional = [
        name for name, frame in extracted.items() if name not in _REQUIRED_DATASETS and frame.empty
    ]
    if empty_optional:
        warnings.warn(
            "Optional nflreadpy extracts returned no rows for: " + ", ".join(sorted(empty_optional)),
            stacklevel=3,
        )


def _enrich_with_schedule_context(frame: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    """Fill missing game_id/season/week/season_type from schedules.

    When frame already has game_id, joins on that directly.
    When frame has team/week/season/season_type but no game_id, derives game_id
    by matching each team (home or away) against the schedule.
    """
    if frame.empty or schedules.empty:
        return frame.copy()

    if "game_id" not in frame.columns and {
        "team", "week", "season", "season_type"
    }.issubset(frame.columns) and "game_id" in schedules.columns:
        required = [c for c in ["game_id", "season", "season_type", "week", "home_team", "away_team"]
                    if c in schedules.columns]
        sched = schedules.loc[:, required].drop_duplicates(subset=["game_id"])
        home = sched.rename(columns={"home_team": "team"}).drop(columns=["away_team"], errors="ignore")
        away = sched.rename(columns={"away_team": "team"}).drop(columns=["home_team"], errors="ignore")
        combined = pd.concat([home, away], ignore_index=True)
        join_cols = [c for c in ["team", "week", "season", "season_type"] if c in combined.columns]
        team_lookup = combined.drop_duplicates(subset=join_cols)
        enriched = frame.merge(team_lookup[join_cols + ["game_id"]], how="left", on=join_cols)
        return enriched

    if "game_id" not in frame.columns or "game_id" not in schedules.columns:
        return frame.copy()

    schedule_columns = [
        column for column in ["game_id", "season", "season_type", "week"] if column in schedules.columns
    ]
    lookup = schedules.loc[:, schedule_columns].drop_duplicates(subset=["game_id"])
    enriched = frame.merge(lookup, how="left", on="game_id", suffixes=("", "_schedule"))
    for column in ["season", "season_type", "week"]:
        schedule_column = f"{column}_schedule"
        if schedule_column in enriched.columns:
            if column not in enriched.columns:
                enriched[column] = enriched[schedule_column]
            else:
                enriched[column] = enriched[column].fillna(enriched[schedule_column])
            enriched = enriched.drop(columns=[schedule_column])
    return enriched


def _attach_team_keys(frame: pd.DataFrame, dim_team: pd.DataFrame) -> pd.DataFrame:
    """Attach team_key to a fact frame when a team column is available."""
    if frame.empty or "team" not in frame.columns or dim_team.empty:
        return frame
    lookup = dim_team.loc[:, ["team_id", "team_key"]].drop_duplicates(subset=["team_id"])
    enriched = frame.merge(lookup, how="left", left_on="team", right_on="team_id")
    enriched = enriched.drop(columns=["team_id"], errors="ignore")
    ordered = ["team_key", *[column for column in frame.columns if column != "team_key"]]
    return enriched.loc[:, [column for column in ordered if column in enriched.columns]].copy()


def _attach_player_and_team_keys(
    frame: pd.DataFrame,
    *,
    dim_player: pd.DataFrame,
    dim_team: pd.DataFrame,
) -> pd.DataFrame:
    """Attach player_key and team_key to a player-grain fact frame."""
    if frame.empty:
        return frame
    enriched = frame.copy()
    if "player_id" in enriched.columns and not dim_player.empty:
        player_lookup = dim_player.loc[:, ["player_id", "player_key"]].drop_duplicates(subset=["player_id"])
        enriched = enriched.merge(player_lookup, how="left", on="player_id")
    enriched = _attach_team_keys(enriched, dim_team)
    ordered = [column for column in ["player_key", "team_key", *frame.columns] if column in enriched.columns]
    return enriched.loc[:, ordered].copy()


def _log_stage_results(
    engine: Engine,
    etl_batch_id: str,
    context: PipelineRunContext,
    extracted: dict[str, pd.DataFrame],
) -> None:
    """Record extract step row counts in the ETL log."""
    timestamp = datetime.now(UTC)
    for dataset_name, frame in extracted.items():
        record_etl_step(
            engine,
            etl_batch_id=etl_batch_id,
            pipeline_name="phase1",
            step_name=f"extract_{dataset_name}",
            source_name="nflreadpy",
            context=context,
            run_status="success",
            rows_written=len(frame),
            started_at=timestamp,
            finished_at=timestamp,
        )


def _log_transform_results(
    engine: Engine,
    etl_batch_id: str,
    context: PipelineRunContext,
    artifacts: PipelineArtifacts,
) -> None:
    """Record transform step row counts in the ETL log."""
    timestamp = datetime.now(UTC)
    for table_name in [
        "dim_team",
        "dim_player",
        "dim_game",
        "bridge_player_ids",
        "fact_game_pbp",
        "fact_team_offense",
        "fact_team_defense",
        "fact_player_offense",
        "fact_team_special_teams",
        "fact_player_defense",
        "fact_player_special_teams",
    ]:
        frame = getattr(artifacts, table_name)
        record_etl_step(
            engine,
            etl_batch_id=etl_batch_id,
            pipeline_name="phase1",
            step_name=f"transform_{table_name}",
            source_name="nflverse",
            context=context,
            run_status="success",
            rows_written=len(frame),
            started_at=timestamp,
            finished_at=timestamp,
        )


def _fetch_previous_row_count(engine: Engine, step_name: str, context: PipelineRunContext) -> int | None:
    """Fetch the most recent successful prior row count for a step and run window."""
    filters = [
        "pipeline_name = 'phase1'",
        "step_name = :step_name",
        "run_status = 'success'",
    ]
    params: dict[str, object] = {"step_name": step_name}
    if context.season is not None:
        filters.append("season = :season")
        params["season"] = context.season
    if context.week is not None:
        filters.append("week = :week")
        params["week"] = context.week
    filters.append("season_type = :season_type")
    params["season_type"] = context.season_type
    history = pd.read_sql_query(
        text(
            "SELECT rows_written FROM etl_run_log WHERE "
            + " AND ".join(filters)
            + " ORDER BY finished_at DESC LIMIT 1"
        ),
        engine,
        params=params,
    )
    if history.empty:
        return None
    return int(history.loc[0, "rows_written"])
