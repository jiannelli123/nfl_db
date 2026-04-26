"""Pro-Football-Reference adapter placeholder."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.adapters.base import BaseSourceAdapter


class ProFootballReferenceAdapter(BaseSourceAdapter):
    """Placeholder adapter for Pro-Football-Reference integration."""

    source_name = "pro_football_reference"
    is_restricted = False

    def fetch_schedules(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Review PFR schedule access requirements and legality.")

    def fetch_rosters(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add roster and snap share lineage mapping for PFR.")

    def fetch_play_by_play(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: PFR play extraction is not implemented in Phase 1.")

    def fetch_weekly_player_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add advanced and snap-count player ingestion for PFR.")

    def fetch_weekly_team_stats(self, seasons: tuple[int, ...]) -> pd.DataFrame:
        raise NotImplementedError("TODO: Add team advanced stat ingestion for PFR.")
