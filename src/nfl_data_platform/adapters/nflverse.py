"""nflverse adapter implementation using nflreadpy."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

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
        return self._load_from_backend("load_schedules", seasons)

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch roster and player identity data with normalized nflverse fields."""
        rosters = self._load_from_backend("load_rosters", seasons)
        players = self._load_from_backend("load_players", seasons)
        if rosters.empty:
            return rosters
        if players.empty:
            return rosters

        join_columns = [column for column in ["player_id"] if column in players.columns and column in rosters.columns]
        if not join_columns:
            return rosters

        preferred_player_columns = [
            "player_id",
            "display_name",
            "full_name",
            "first_name",
            "last_name",
            "status",
            "birth_date",
            "college_name",
        ]
        player_frame = players.loc[:, [column for column in preferred_player_columns if column in players.columns]]
        merged = rosters.merge(player_frame, how="left", on=join_columns)
        if "player_name" not in merged.columns:
            merged["player_name"] = merged.get("full_name", merged.get("display_name"))
        merged["player_name"] = merged["player_name"].fillna(merged.get("full_name"))
        merged["player_name"] = merged["player_name"].fillna(merged.get("display_name"))
        return merged

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch play-by-play with expected columns like game_id, play_id, posteam, and epa."""
        return self._load_from_backend("load_pbp", seasons)

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch weekly player stats keyed by player, team, week, and season."""
        return self._load_from_backend("load_player_stats", seasons)

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch weekly team stats keyed by team, week, season, and season type."""
        return self._load_from_backend("load_team_stats", seasons)

    def fetch_draft_picks(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Fetch draft picks keyed by draft year, round, and pick number."""
        return self._load_from_backend("load_draft_picks", seasons)

    def _load_from_backend(self, function_name: str, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Call an nflreadpy backend function and normalize the result."""
        backend_function = self._resolve_backend_function(function_name)
        frame = self._invoke_backend_function(backend_function, seasons)
        return self._normalize_frame(self._convert_to_pandas(frame))

    def _resolve_backend_function(self, function_name: str) -> Any:
        """Resolve a supported import function from nflreadpy."""
        try:
            import nflreadpy as nfl  # type: ignore
        except ImportError:
            raise RuntimeError(
                "nflreadpy is required for the current nflverse extraction pipeline. Install it with "
                "'pip install nflreadpy' or reinstall project dependencies."
            ) from None

        if not hasattr(nfl, function_name):
            raise RuntimeError(f"nflreadpy does not expose the expected function '{function_name}'.")
        return getattr(nfl, function_name)

    @staticmethod
    def _invoke_backend_function(function: Any, seasons: tuple[int, ...]) -> Any:
        """Call a backend loader with the right nflreadpy-compatible signature."""
        signature = inspect.signature(function)
        parameters = signature.parameters
        if "seasons" in parameters:
            return function(list(seasons))

        positional_parameters = [
            parameter
            for parameter in parameters.values()
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if not positional_parameters:
            return function()
        return function(list(seasons))

    @staticmethod
    def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for downstream transform stability."""
        if frame.empty:
            return frame
        normalized_columns = {column: str(column).strip().lower() for column in frame.columns}
        return frame.rename(columns=normalized_columns)

    @staticmethod
    def _convert_to_pandas(frame: Any) -> pd.DataFrame:
        """Convert nflreadpy output into a pandas DataFrame."""
        if isinstance(frame, pd.DataFrame):
            return frame
        if hasattr(frame, "to_pandas"):
            return frame.to_pandas()
        return pd.DataFrame(frame)
