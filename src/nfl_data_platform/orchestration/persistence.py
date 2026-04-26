"""Temporary CSV persistence helpers for pipeline validation runs."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from nfl_data_platform.quality.checks import CheckResult

if TYPE_CHECKING:
    from nfl_data_platform.orchestration.pipeline import PipelineArtifacts, PipelineRunContext


def build_run_output_dir(base_dir: Path, context: "PipelineRunContext") -> Path:
    """Build a deterministic output directory for a bounded pipeline run."""
    season = context.season if context.season is not None else "all"
    week = context.week if context.week is not None else "all"
    season_type = context.season_type.lower()
    refresh = "full" if context.full_refresh else "incremental"
    return base_dir / f"season_{season}" / f"week_{week}" / f"{season_type}_{refresh}"


def persist_phase1_run(
    base_dir: Path,
    context: "PipelineRunContext",
    extracted: dict[str, pd.DataFrame],
    artifacts: "PipelineArtifacts",
    quality_results: list[CheckResult],
) -> Path:
    """Persist extracted inputs, transformed outputs, and quality results as CSV files."""
    run_dir = build_run_output_dir(base_dir=base_dir, context=context)
    extracted_dir = run_dir / "extracted"
    transformed_dir = run_dir / "transformed"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    transformed_dir.mkdir(parents=True, exist_ok=True)

    for name, frame in extracted.items():
        _write_csv(extracted_dir / f"{name}.csv", frame)

    transformed_frames = {
        "dim_team": artifacts.dim_team,
        "dim_player": artifacts.dim_player,
        "dim_game": artifacts.dim_game,
        "fact_team_offense": artifacts.fact_team_offense,
        "fact_team_defense": artifacts.fact_team_defense,
        "fact_player_offense": artifacts.fact_player_offense,
    }
    for name, frame in transformed_frames.items():
        _write_csv(transformed_dir / f"{name}.csv", frame)

    quality_frame = pd.DataFrame([asdict(result) for result in quality_results])
    _write_csv(run_dir / "quality_results.csv", quality_frame)
    return run_dir


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    """Write a dataframe to CSV with stable output semantics."""
    frame.to_csv(path, index=False)
