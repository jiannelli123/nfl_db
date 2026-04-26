"""Database loading helpers for the nflverse warehouse pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

if TYPE_CHECKING:
    from nfl_data_platform.orchestration.pipeline import PipelineArtifacts, PipelineRunContext


@dataclass(slots=True)
class TableLoadResult:
    """Structured result for a single table load step."""

    table_name: str
    run_status: str
    rows_written: int
    error_message: str | None = None


def load_phase1_tables(
    engine: Engine,
    artifacts: "PipelineArtifacts",
    context: "PipelineRunContext",
    etl_batch_id: str | None = None,
) -> dict[str, Any]:
    """Load current warehouse tables into the database and log each step."""
    etl_batch_id = etl_batch_id or str(uuid4())
    tables = [
        ("dim_team", artifacts.dim_team, "replace"),
        ("dim_player", artifacts.dim_player, "replace"),
        ("dim_game", artifacts.dim_game, "replace"),
        ("bridge_player_ids", artifacts.bridge_player_ids, "replace"),
        ("fact_game_pbp", artifacts.fact_game_pbp, "windowed"),
        ("fact_team_offense", artifacts.fact_team_offense, "windowed"),
        ("fact_team_defense", artifacts.fact_team_defense, "windowed"),
        ("fact_player_offense", artifacts.fact_player_offense, "windowed"),
        ("fact_team_special_teams", artifacts.fact_team_special_teams, "windowed"),
        ("fact_player_defense", artifacts.fact_player_defense, "windowed"),
        ("fact_player_special_teams", artifacts.fact_player_special_teams, "windowed"),
    ]

    results: list[TableLoadResult] = []
    for table_name, frame, load_strategy in tables:
        result = _load_table(
            engine=engine,
            table_name=table_name,
            frame=frame,
            load_strategy=load_strategy,
            context=context,
            etl_batch_id=etl_batch_id,
            pipeline_name="phase1",
        )
        results.append(result)

    total_rows = sum(result.rows_written for result in results if result.run_status == "success")
    return {
        "etl_batch_id": etl_batch_id,
        "table_results": results,
        "rows_written": total_rows,
    }


def load_draft_tables(
    engine: Engine,
    artifacts: dict[str, pd.DataFrame],
    context: "PipelineRunContext",
    etl_batch_id: str | None = None,
) -> dict[str, Any]:
    """Load draft warehouse tables into the database and log each step."""
    etl_batch_id = etl_batch_id or str(uuid4())
    tables = [
        ("dim_prospect", artifacts["dim_prospect"], "replace"),
        ("fact_draft_pick", artifacts["fact_draft_pick"], "draft_windowed"),
    ]

    results: list[TableLoadResult] = []
    for table_name, frame, load_strategy in tables:
        result = _load_table(
            engine=engine,
            table_name=table_name,
            frame=frame,
            load_strategy=load_strategy,
            context=context,
            etl_batch_id=etl_batch_id,
            pipeline_name="draft",
        )
        results.append(result)

    total_rows = sum(result.rows_written for result in results if result.run_status == "success")
    return {
        "etl_batch_id": etl_batch_id,
        "table_results": results,
        "rows_written": total_rows,
    }


def record_etl_step(
    engine: Engine,
    *,
    etl_batch_id: str,
    pipeline_name: str,
    step_name: str,
    source_name: str,
    context: "PipelineRunContext",
    run_status: str,
    rows_written: int,
    error_message: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> None:
    """Insert a standalone ETL log row for extract or transform steps."""
    _insert_etl_log_row(
        engine=engine,
        pipeline_name=pipeline_name,
        table_name=step_name,
        source_name=source_name,
        result=TableLoadResult(
            table_name=step_name,
            run_status=run_status,
            rows_written=rows_written,
            error_message=error_message,
        ),
        context=context,
        etl_batch_id=etl_batch_id,
        started_at=started_at or datetime.now(UTC),
        finished_at=finished_at or datetime.now(UTC),
    )


_ALLOWED_TABLE_NAMES: frozenset[str] = frozenset(
    [
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
        "dim_prospect",
        "fact_draft_pick",
        "etl_run_log",
    ]
)


def _load_table(
    engine: Engine,
    table_name: str,
    frame: pd.DataFrame,
    load_strategy: str,
    context: "PipelineRunContext",
    etl_batch_id: str,
    pipeline_name: str,
) -> TableLoadResult:
    """Load a single table and write a corresponding ETL log row."""
    if table_name not in _ALLOWED_TABLE_NAMES:
        raise ValueError(f"Refusing to load into unknown table: {table_name!r}")
    started_at = datetime.now(UTC)
    if frame.empty:
        result = TableLoadResult(
            table_name=table_name,
            run_status="skipped_empty",
            rows_written=0,
        )
        _insert_etl_log_row(
            engine=engine,
            pipeline_name=pipeline_name,
            table_name=table_name,
            source_name="nflverse",
            result=result,
            context=context,
            etl_batch_id=etl_batch_id,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
        return result

    try:
        prepared = _prepare_frame_for_table(
            engine=engine,
            table_name=table_name,
            frame=frame,
            etl_batch_id=etl_batch_id,
        )
        with engine.begin() as connection:
            if load_strategy == "replace":
                connection.exec_driver_sql(f"DELETE FROM {table_name}")
            elif load_strategy == "windowed":
                _delete_matching_windows(connection=connection, table_name=table_name, frame=prepared)
            elif load_strategy == "draft_windowed":
                _delete_matching_draft_years(connection=connection, table_name=table_name, frame=prepared)

            prepared.to_sql(table_name, con=connection, if_exists="append", index=False)

        result = TableLoadResult(
            table_name=table_name,
            run_status="success",
            rows_written=len(prepared),
        )
    except Exception as exc:
        result = TableLoadResult(
            table_name=table_name,
            run_status="failed",
            rows_written=0,
            error_message=str(exc),
        )
        _insert_etl_log_row(
            engine=engine,
            pipeline_name=pipeline_name,
            table_name=table_name,
            source_name="nflverse",
            result=result,
            context=context,
            etl_batch_id=etl_batch_id,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
        return result

    _insert_etl_log_row(
        engine=engine,
        pipeline_name=pipeline_name,
        table_name=table_name,
        source_name="nflverse",
        result=result,
        context=context,
        etl_batch_id=etl_batch_id,
        started_at=started_at,
        finished_at=datetime.now(UTC),
    )
    return result


def _prepare_frame_for_table(
    engine: Engine,
    table_name: str,
    frame: pd.DataFrame,
    etl_batch_id: str,
) -> pd.DataFrame:
    """Align a dataframe to the destination table schema and cast to DB types."""
    inspector = inspect(engine)
    column_info = inspector.get_columns(table_name)
    table_columns = {col["name"] for col in column_info}
    column_types = {col["name"]: type(col["type"]).__name__.upper() for col in column_info}
    prepared = frame.copy()

    if "source_name" in table_columns and "source_name" not in prepared.columns:
        prepared["source_name"] = "nflverse"
    if "etl_batch_id" in table_columns and "etl_batch_id" not in prepared.columns:
        prepared["etl_batch_id"] = etl_batch_id

    writable_columns = [
        column
        for column in prepared.columns
        if column in table_columns and column not in {"created_at", "updated_at"}
    ]
    prepared = prepared.loc[:, writable_columns].copy()

    for col in prepared.columns:
        db_type = column_types.get(col, "")
        if "DATE" in db_type or "TIMESTAMP" in db_type:
            prepared[col] = pd.to_datetime(prepared[col], errors="coerce")
            if db_type == "DATE":
                prepared[col] = prepared[col].dt.date
        elif "BOOL" in db_type:
            prepared[col] = prepared[col].where(prepared[col].isna(), prepared[col].astype(bool))
        elif any(t in db_type for t in ("INTEGER", "BIGINT", "SMALLINT")):
            prepared[col] = pd.to_numeric(prepared[col], errors="coerce").astype("Int64")
        elif any(t in db_type for t in ("NUMERIC", "FLOAT", "REAL", "DOUBLE")):
            prepared[col] = pd.to_numeric(prepared[col], errors="coerce")

    return prepared


def _delete_matching_windows(connection: Any, table_name: str, frame: pd.DataFrame) -> None:
    """Delete existing rows that match the incoming dataframe's season/week window."""
    window_columns = [
        column
        for column in ["season", "week", "season_type"]
        if column in frame.columns
    ]
    if not window_columns:
        return

    distinct_windows = frame.loc[:, window_columns].drop_duplicates()
    for _, row in distinct_windows.iterrows():
        where_clause = " AND ".join(f"{column} = :{column}" for column in window_columns)
        connection.execute(
            text(f"DELETE FROM {table_name} WHERE {where_clause}"),
            row.to_dict(),
        )


def _delete_matching_draft_years(connection: Any, table_name: str, frame: pd.DataFrame) -> None:
    """Delete existing rows for incoming draft years."""
    if "draft_year" not in frame.columns:
        return
    distinct_years = frame.loc[:, ["draft_year"]].drop_duplicates()
    for _, row in distinct_years.iterrows():
        connection.execute(
            text(f"DELETE FROM {table_name} WHERE draft_year = :draft_year"),
            row.to_dict(),
        )


def _insert_etl_log_row(
    engine: Engine,
    pipeline_name: str,
    table_name: str,
    source_name: str,
    result: TableLoadResult,
    context: "PipelineRunContext",
    etl_batch_id: str,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    """Insert a single ETL run log row."""
    with engine.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO etl_run_log (
                etl_run_log_key,
                etl_batch_id,
                pipeline_name,
                step_name,
                source_name,
                season,
                week,
                season_type,
                run_status,
                rows_written,
                error_message,
                started_at,
                finished_at
            ) VALUES (
                :etl_run_log_key,
                :etl_batch_id,
                :pipeline_name,
                :step_name,
                :source_name,
                :season,
                :week,
                :season_type,
                :run_status,
                :rows_written,
                :error_message,
                :started_at,
                :finished_at
            )
            """),
            {
                "etl_run_log_key": f"{etl_batch_id}_{table_name}",
                "etl_batch_id": etl_batch_id,
                "pipeline_name": pipeline_name,
                "step_name": table_name,
                "source_name": source_name,
                "season": context.season,
                "week": context.week,
                "season_type": context.season_type,
                "run_status": result.run_status,
                "rows_written": result.rows_written,
                "error_message": result.error_message,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
            },
        )
