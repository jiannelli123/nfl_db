"""Player special teams fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.derive_special_teams_metrics import (
    derive_player_special_teams_metrics,
)


def build_fact_player_special_teams(weekly_player_stats: pd.DataFrame) -> pd.DataFrame:
    """Build player special teams facts from weekly player stats."""
    return derive_player_special_teams_metrics(weekly_player_stats)
