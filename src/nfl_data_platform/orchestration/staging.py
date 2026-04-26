"""Filesystem staging helpers for raw nflverse extracts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nfl_data_platform.orchestration.pipeline import PipelineRunContext


def stage_extracted_data(
    base_dir: Path,
    context: "PipelineRunContext",
    extracted: dict[str, pd.DataFrame],
) -> dict[str, Path]:
    """Persist extracted raw datasets as bounded CSV files."""
    stage_dir = build_stage_dir(base_dir=base_dir, context=context)
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_files: dict[str, Path] = {}
    for name, frame in extracted.items():
        path = stage_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        staged_files[name] = path
    return staged_files


def build_stage_dir(base_dir: Path, context: "PipelineRunContext") -> Path:
    """Build a deterministic staging directory for a run window."""
    season = context.season if context.season is not None else "all"
    week = context.week if context.week is not None else "all"
    season_type = context.season_type.lower()
    return base_dir / f"season_{season}" / f"week_{week}" / season_type


def stage_draft_data(
    base_dir: Path,
    context: "PipelineRunContext",
    extracted: dict[str, pd.DataFrame],
) -> dict[str, Path]:
    """Persist extracted draft datasets under a separate bounded directory."""
    stage_dir = build_draft_stage_dir(base_dir=base_dir, context=context)
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_files: dict[str, Path] = {}
    for name, frame in extracted.items():
        path = stage_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        staged_files[name] = path
    return staged_files


def build_draft_stage_dir(base_dir: Path, context: "PipelineRunContext") -> Path:
    """Build a deterministic staging directory for a draft run."""
    season = context.season if context.season is not None else "all"
    return base_dir / "draft" / f"season_{season}"
