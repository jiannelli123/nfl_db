"""Phase 1 pipeline orchestration scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from nfl_data_platform.adapters.nflverse import NFLVerseAdapter
from nfl_data_platform.config import Settings
from nfl_data_platform.db.engine import create_engine_from_settings
from nfl_data_platform.orchestration.persistence import persist_phase1_run
from nfl_data_platform.quality.checks import (
    CheckResult,
    check_not_empty,
    check_required_columns,
    check_unique_key,
)
from nfl_data_platform.transforms.dimensions import build_dim_game, build_dim_player, build_dim_team
from nfl_data_platform.transforms.player_offense import build_fact_player_offense
from nfl_data_platform.transforms.team_defense import build_fact_team_defense
from nfl_data_platform.transforms.team_offense import build_fact_team_offense


@dataclass(slots=True)
class PipelineArtifacts:
    """Container for extracted and transformed Phase 1 dataframes."""

    schedules: pd.DataFrame
    rosters: pd.DataFrame
    pbp: pd.DataFrame
    weekly_player_stats: pd.DataFrame
    weekly_team_stats: pd.DataFrame
    dim_team: pd.DataFrame
    dim_player: pd.DataFrame
    dim_game: pd.DataFrame
    fact_team_offense: pd.DataFrame
    fact_team_defense: pd.DataFrame
    fact_player_offense: pd.DataFrame


@dataclass(slots=True)
class PipelineRunContext:
    """Execution parameters for a bounded pipeline run."""

    season: int | None = None
    week: int | None = None
    season_type: str = "REG"
    full_refresh: bool = False


def extract_phase1_data(settings: Settings) -> dict[str, pd.DataFrame]:
    """Extract Phase 1 inputs from nflverse."""
    adapter = NFLVerseAdapter(data_dir=settings.nflverse_data_dir)
    seasons = settings.nflverse_seasons
    return {
        "schedules": adapter.fetch_schedules(seasons),
        "rosters": adapter.fetch_rosters(seasons),
        "pbp": adapter.fetch_play_by_play(seasons),
        "weekly_player_stats": adapter.fetch_weekly_player_stats(seasons),
        "weekly_team_stats": adapter.fetch_weekly_team_stats(seasons),
    }


def build_phase1_artifacts(extracted: dict[str, pd.DataFrame]) -> PipelineArtifacts:
    """Build Phase 1 dimension and fact outputs from extracted frames."""
    dim_team = build_dim_team(rosters=extracted["rosters"], schedules=extracted["schedules"])
    dim_player = build_dim_player(rosters=extracted["rosters"])
    dim_game = build_dim_game(schedules=extracted["schedules"])
    fact_team_offense = build_fact_team_offense(
        pbp=extracted["pbp"],
        weekly_team_stats=extracted["weekly_team_stats"],
    )
    fact_team_defense = build_fact_team_defense(
        pbp=extracted["pbp"],
        weekly_team_stats=extracted["weekly_team_stats"],
    )
    fact_player_offense = build_fact_player_offense(extracted["weekly_player_stats"])
    return PipelineArtifacts(
        schedules=extracted["schedules"],
        rosters=extracted["rosters"],
        pbp=extracted["pbp"],
        weekly_player_stats=extracted["weekly_player_stats"],
        weekly_team_stats=extracted["weekly_team_stats"],
        dim_team=dim_team,
        dim_player=dim_player,
        dim_game=dim_game,
        fact_team_offense=fact_team_offense,
        fact_team_defense=fact_team_defense,
        fact_player_offense=fact_player_offense,
    )


def run_quality_checks(artifacts: PipelineArtifacts) -> list[CheckResult]:
    """Run lightweight Phase 1 validations against transformed outputs."""
    results = [
        check_required_columns(artifacts.dim_team, ["team_key", "team_id"], "dim_team"),
        check_required_columns(artifacts.dim_player, ["player_key", "player_id"], "dim_player"),
        check_required_columns(artifacts.dim_game, ["game_key", "game_id"], "dim_game"),
        check_unique_key(artifacts.dim_team, ["team_key"], "dim_team"),
        check_unique_key(artifacts.dim_player, ["player_key"], "dim_player"),
        check_unique_key(artifacts.dim_game, ["game_key"], "dim_game"),
    ]

    if not artifacts.fact_team_offense.empty:
        results.append(check_not_empty(artifacts.fact_team_offense, "fact_team_offense"))
    if not artifacts.fact_team_defense.empty:
        results.append(check_not_empty(artifacts.fact_team_defense, "fact_team_defense"))
    if not artifacts.fact_player_offense.empty:
        results.append(check_not_empty(artifacts.fact_player_offense, "fact_player_offense"))
    return results


def initialize_database(settings: Settings) -> dict[str, Any]:
    """Create a database engine and return metadata for future DDL execution."""
    engine = create_engine_from_settings(settings)
    return {"engine": engine, "status": "initialized"}


def run_phase1_pipeline(settings: Settings, context: PipelineRunContext | None = None) -> dict[str, Any]:
    """Run the non-loading Phase 1 scaffold pipeline and return structured output."""
    context = context or PipelineRunContext()
    initialize_database(settings)
    extracted = extract_phase1_data(settings)
    artifacts = build_phase1_artifacts(extracted)
    quality_results = run_quality_checks(artifacts)
    run_output_dir = persist_phase1_run(
        base_dir=settings.temp_data_dir,
        context=context,
        extracted=extracted,
        artifacts=artifacts,
        quality_results=quality_results,
    )
    return {
        "context": context,
        "artifacts": artifacts,
        "quality_results": quality_results,
        "run_output_dir": run_output_dir,
        "load_status": "CSV snapshots written for validation. TODO: implement warehouse loads and etl_run_log persistence.",
    }
