"""Next Gen Stats adapter placeholder."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class NextGenStatsAdapter(BaseSourceAdapter):
    """Placeholder adapter for restricted or undocumented Next Gen Stats access."""

    source_name = "next_gen_stats"
    is_restricted = True

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Implement a documented Next Gen Stats schedule adapter.")

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Implement documented Next Gen Stats roster access.")

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Review legal access for tracking-linked play detail.")

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Implement documented NGS player metrics ingestion.")

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Confirm whether team-level NGS exports are available.")

    def fetch_draft_picks(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Next Gen Stats draft ingestion is not implemented.")
