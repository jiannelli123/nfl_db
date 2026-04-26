"""Tests for raw staging helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nfl_data_platform.orchestration.pipeline import PipelineRunContext
from nfl_data_platform.orchestration.staging import build_stage_dir, stage_extracted_data


def test_stage_extracted_data_writes_bounded_csvs(tmp_path: Path) -> None:
    context = PipelineRunContext(season=2025, week=1, season_type="REG")
    extracted = {"schedules": pd.DataFrame([{"game_id": "g1"}])}

    staged = stage_extracted_data(tmp_path, context, extracted)

    assert build_stage_dir(tmp_path, context) == tmp_path / "season_2025" / "week_1" / "reg"
    assert staged["schedules"].exists()
