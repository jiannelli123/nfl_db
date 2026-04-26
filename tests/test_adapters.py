"""Tests for adapter behavior."""

from __future__ import annotations

from pathlib import Path
import sys
import types

import pandas as pd
import pytest

from nfl_data_platform.adapters.ftn import FTNAdapter
from nfl_data_platform.adapters.ngs import NextGenStatsAdapter
from nfl_data_platform.adapters.nflverse import NFLVerseAdapter
from nfl_data_platform.adapters.pfr import ProFootballReferenceAdapter
from nfl_data_platform.adapters.player_profiler import PlayerProfilerAdapter
from nfl_data_platform.adapters.team_rankings import TeamRankingsAdapter


def test_nflverse_adapter_uses_nflreadpy_and_normalizes_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakePolarsFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def to_pandas(self) -> pd.DataFrame:
            return self._frame

    fake_module = types.SimpleNamespace(
        load_schedules=lambda seasons: _capture_call(
            calls,
            "load_schedules",
            seasons,
            FakePolarsFrame(pd.DataFrame([{"GAME_ID": "g1", "SEASON": 2025, "WEEK": 1}])),
        ),
        load_rosters=lambda seasons: _capture_call(
            calls,
            "load_rosters",
            seasons,
            FakePolarsFrame(pd.DataFrame([{"PLAYER_ID": "p1", "TEAM": "BUF", "SEASON": 2025}])),
        ),
        load_players=lambda: _capture_call(
            calls,
            "load_players",
            None,
            FakePolarsFrame(pd.DataFrame([{"PLAYER_ID": "p1", "FULL_NAME": "Player One"}])),
        ),
        load_draft_picks=lambda seasons: _capture_call(
            calls,
            "load_draft_picks",
            seasons,
            FakePolarsFrame(pd.DataFrame([{"DRAFT_YEAR": 2025, "ROUND": 1, "PICK": 1}])),
        ),
    )
    monkeypatch.setitem(sys.modules, "nflreadpy", fake_module)

    adapter = NFLVerseAdapter(data_dir=Path("./data"))
    schedules = adapter.fetch_schedules((2025,))
    rosters = adapter.fetch_rosters((2025,))
    draft_picks = adapter.fetch_draft_picks((2025,))

    assert ("load_schedules", [2025]) in calls
    assert ("load_rosters", [2025]) in calls
    assert ("load_players", None) in calls
    assert ("load_draft_picks", [2025]) in calls
    assert list(schedules.columns) == ["game_id", "season", "week"]
    assert rosters.loc[0, "player_name"] == "Player One"
    assert list(draft_picks.columns) == ["draft_year", "round", "pick"]


def test_nflverse_adapter_passes_seasons_to_optional_season_loaders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakePolarsFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def to_pandas(self) -> pd.DataFrame:
            return self._frame

    fake_module = types.SimpleNamespace(
        load_pbp=lambda seasons=None: _capture_call(
            calls,
            "load_pbp",
            seasons,
            FakePolarsFrame(pd.DataFrame([{"GAME_ID": "g1", "PLAY_ID": 1}])),
        ),
        load_players=lambda: _capture_call(
            calls,
            "load_players",
            None,
            FakePolarsFrame(pd.DataFrame([{"PLAYER_ID": "p1"}])),
        ),
    )
    monkeypatch.setitem(sys.modules, "nflreadpy", fake_module)

    adapter = NFLVerseAdapter(data_dir=Path("./data"))
    adapter.fetch_play_by_play((2024,))

    assert ("load_pbp", [2024]) in calls
    assert ("load_players", None) not in calls


def test_nflverse_adapter_raises_when_backend_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "nflreadpy", raising=False)

    original_import = __import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "nflreadpy":
            raise ImportError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    adapter = NFLVerseAdapter(data_dir=Path("./data"))

    with pytest.raises(RuntimeError, match="nflreadpy is required"):
        adapter.fetch_schedules((2025,))


def _capture_call(
    calls: list[tuple[str, object]],
    name: str,
    seasons: object,
    result: object,
) -> object:
    if isinstance(seasons, list):
        calls.append((name, list(seasons)))
    else:
        calls.append((name, seasons))
    return result


def test_nflverse_adapter_fetches_weekly_player_and_team_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakePolarsFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def to_pandas(self) -> pd.DataFrame:
            return self._frame

    fake_module = types.SimpleNamespace(
        load_player_stats=lambda seasons=None: _capture_call(
            calls,
            "load_player_stats",
            seasons,
            FakePolarsFrame(
                pd.DataFrame(
                    [{"PLAYER_ID": "p1", "GAME_ID": "g1", "SEASON": 2025, "WEEK": 1,
                      "SEASON_TYPE": "REG", "PASSING_YARDS": 300}]
                )
            ),
        ),
        load_team_stats=lambda seasons=None: _capture_call(
            calls,
            "load_team_stats",
            seasons,
            FakePolarsFrame(
                pd.DataFrame([{"TEAM": "BUF", "GAME_ID": "g1", "POINTS": 24}])
            ),
        ),
        load_players=lambda: _capture_call(
            calls,
            "load_players",
            None,
            FakePolarsFrame(pd.DataFrame([{"PLAYER_ID": "p1"}])),
        ),
    )
    monkeypatch.setitem(sys.modules, "nflreadpy", fake_module)

    adapter = NFLVerseAdapter(data_dir=Path("./data"))
    player_stats = adapter.fetch_weekly_player_stats((2025,))
    team_stats = adapter.fetch_weekly_team_stats((2025,))

    assert ("load_player_stats", [2025]) in calls
    assert ("load_team_stats", [2025]) in calls
    assert not player_stats.empty
    assert "player_id" in player_stats.columns
    assert "passing_yards" in player_stats.columns
    assert not team_stats.empty
    assert "team" in team_stats.columns


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
