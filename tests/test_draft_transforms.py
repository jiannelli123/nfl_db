"""Tests for draft dimension and fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.draft import build_dim_prospect, build_fact_draft_pick


def test_build_dim_prospect_deduplicates_identity_rows() -> None:
    draft_picks = pd.DataFrame(
        [
            {
                "draft_year": 2025,
                "round": 1,
                "pick": 1,
                "team": "ten",
                "player_name": "Cam Ward",
                "player_id": "00-0001",
                "college_name": "Miami",
                "position": "QB",
            },
            {
                "draft_year": 2025,
                "round": 1,
                "pick": 2,
                "team": "cle",
                "player_name": "Cam Ward",
                "player_id": "00-0001",
                "college_name": "Miami",
                "position": "QB",
            },
        ]
    )

    result = build_dim_prospect(draft_picks)

    assert len(result) == 1
    assert result.loc[0, "prospect_key"] == "2025_00-0001"
    assert result.loc[0, "nflverse_player_id"] == "00-0001"


def test_build_fact_draft_pick_creates_grain_and_normalizes_team() -> None:
    draft_picks = pd.DataFrame(
        [
            {
                "draft_year": 2025,
                "round": 1,
                "pick": 3,
                "pick_overall": 3,
                "team": "nyg",
                "player_name": "Travis Hunter",
                "pfr_player_id": "HuntTr00",
                "college": "Colorado",
            }
        ]
    )

    result = build_fact_draft_pick(draft_picks)

    assert result.loc[0, "draft_pick_key"] == "2025_1_3"
    assert result.loc[0, "team"] == "NYG"
    assert result.loc[0, "overall_pick"] == 3
    assert result.loc[0, "prospect_key"] == "2025_HuntTr00"
