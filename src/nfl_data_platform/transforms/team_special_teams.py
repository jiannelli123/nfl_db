"""Team special teams fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.derive_special_teams_metrics import (
    derive_team_special_teams_metrics,
)


def build_fact_team_special_teams(
    weekly_team_stats: pd.DataFrame,
    team_rankings_metrics: pd.DataFrame | None = None,
    ftn_metrics: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build team special teams facts from public-compatible source inputs."""
    return derive_team_special_teams_metrics(
        weekly_team_stats=weekly_team_stats,
        team_rankings_metrics=team_rankings_metrics,
        ftn_metrics=ftn_metrics,
    )
