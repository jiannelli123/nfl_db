"""Tests for adapter scaffolding."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nfl_data_platform.adapters.ftn import FTNAdapter
from nfl_data_platform.adapters.ngs import NextGenStatsAdapter
from nfl_data_platform.adapters.nflverse import NFLVerseAdapter
from nfl_data_platform.adapters.pfr import ProFootballReferenceAdapter
from nfl_data_platform.adapters.player_profiler import PlayerProfilerAdapter
from nfl_data_platform.adapters.team_rankings import TeamRankingsAdapter


def test_nflverse_adapter_returns_empty_frame_without_backend() -> None:
    adapter = NFLVerseAdapter(data_dir=Path("./data"))

    result = adapter.fetch_schedules((2025,))

    assert isinstance(result, pd.DataFrame)


@pytest.mark.parametrize(
    ("adapter", "method_name"),
    [
        (NextGenStatsAdapter(), "fetch_weekly_player_stats"),
        (ProFootballReferenceAdapter(), "fetch_weekly_team_stats"),
        (FTNAdapter(), "fetch_weekly_team_stats"),
        (TeamRankingsAdapter(), "fetch_weekly_team_stats"),
        (PlayerProfilerAdapter(), "fetch_weekly_player_stats"),
    ],
)
def test_placeholder_adapters_raise_not_implemented(adapter: object, method_name: str) -> None:
    with pytest.raises(NotImplementedError):
        getattr(adapter, method_name)((2025,))
