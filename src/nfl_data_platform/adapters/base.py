"""Base interfaces for data source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseSourceAdapter(ABC):
    """Abstract source adapter with dataframe-based extract contracts."""

    source_name: str
    is_restricted: bool

    @abstractmethod
    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Return normalized schedule data for the requested seasons."""

    @abstractmethod
    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Return normalized roster data for the requested seasons."""

    @abstractmethod
    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Return normalized play-by-play data for the requested seasons."""

    @abstractmethod
    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Return normalized weekly player statistics for the requested seasons."""

    @abstractmethod
    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        """Return normalized weekly team statistics for the requested seasons."""
