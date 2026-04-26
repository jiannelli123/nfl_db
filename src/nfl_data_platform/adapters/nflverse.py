"""nflverse adapter scaffolding for Phase 1 ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class NFLVerseAdapter(BaseSourceAdapter):
    """Adapter for nflverse-compatible public datasets."""

    source_name = "nflverse"
    is_restricted = False

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch schedules with expected columns like game_id, season, week, and teams."""
        return self._load_from_backend("import_schedules", seasons)

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch roster data with expected columns like player_id, team, and position."""
        return self._load_from_backend("import_seasonal_rosters", seasons)

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch play-by-play with expected columns like game_id, play_id, posteam, and epa."""
        return self._load_from_backend("import_pbp_data", seasons)

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch weekly player stats keyed by player, team, week, and season."""
        return self._load_from_backend("import_weekly_data", seasons)

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch weekly team stats keyed by team, week, season, and season type."""
        return self._load_from_backend("import_weekly_team_data", seasons)

    def _load_from_backend(self, function_name: str, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Call an nflverse backend function if available, otherwise return an empty frame.

        TODO: Confirm final backend package choice between nfl_data_py and nflreadpy.
        TODO: Add local file caching once the concrete ingestion path is finalized.
        """
        backend_function = self._resolve_backend_function(function_name)
        if backend_function is None:
            return pd.DataFrame()

        try:
            frame = backend_function(list(seasons))
        except TypeError:
            frame = backend_function(seasons)
        return self._normalize_frame(pd.DataFrame(frame))

    def _resolve_backend_function(self, function_name: str) -> Callable[[Any], Any] | None:
        """Resolve a supported import function from an installed nflverse library."""
        try:
            import nfl_data_py as nfl  # type: ignore

            if hasattr(nfl, function_name):
                return getattr(nfl, function_name)
        except ImportError:
            pass

        # TODO: Add explicit nflreadpy integration once target functions are finalized.
        return None

    @staticmethod
    def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for downstream transform stability."""
        if frame.empty:
            return frame
        normalized_columns = {column: str(column).strip().lower() for column in frame.columns}
        return frame.rename(columns=normalized_columns)
