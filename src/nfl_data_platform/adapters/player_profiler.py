"""PlayerProfiler adapter placeholder."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class PlayerProfilerAdapter(BaseSourceAdapter):
    """Placeholder adapter for PlayerProfiler usage metrics."""

    source_name = "player_profiler"
    is_restricted = True

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Schedule ingestion is not needed for PlayerProfiler.")

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add PlayerProfiler identifier mapping after access review.")

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: PlayerProfiler play-level data is not implemented.")

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Implement licensed player usage metrics ingestion.")

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Team-level PlayerProfiler data is not scoped.")

    def fetch_draft_picks(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: PlayerProfiler draft ingestion is not implemented.")
