"""FTN and DVOA adapter placeholder."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class FTNAdapter(BaseSourceAdapter):
    """Placeholder adapter for FTN/DVOA integration."""

    source_name = "ftn"
    is_restricted = True

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add schedule linkage only if FTN requires local joins.")

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: FTN roster access is not required in Phase 1.")

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: FTN play-by-play access is not implemented.")

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Player-level FTN fields are not yet scoped.")

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Implement licensed FTN/DVOA team metrics ingestion.")

    def fetch_draft_picks(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: FTN draft ingestion is not scoped.")
