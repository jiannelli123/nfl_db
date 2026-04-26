"""TeamRankings adapter placeholder."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class TeamRankingsAdapter(BaseSourceAdapter):
    """Placeholder adapter for TeamRankings public metrics."""

    source_name = "team_rankings"
    is_restricted = False

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: TeamRankings schedule extraction is not implemented.")

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: TeamRankings roster access is out of scope.")

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: TeamRankings does not provide Phase 1 play-by-play input.")

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Player-level TeamRankings metrics are not scoped.")

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add public special teams metric ingestion in a later phase.")
