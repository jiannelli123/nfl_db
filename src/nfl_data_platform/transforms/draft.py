"""Draft dimension and fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.normalization import (
    first_available_column,
    normalize_player_values,
    normalize_team_values,
)


def build_dim_prospect(draft_picks: pd.DataFrame) -> pd.DataFrame:
    """Build a canonical prospect dimension from draft picks."""
    columns = [
        "prospect_key",
        "prospect_id",
        "player_name",
        "college_name",
        "position",
        "draft_year",
        "nflverse_player_id",
        "pfr_player_id",
    ]
    if draft_picks.empty:
        return pd.DataFrame(columns=columns)

    frame = _normalize_draft_frame(draft_picks)
    frame = frame.dropna(subset=["player_name", "draft_year"]).copy()
    frame["prospect_key"] = [
        _build_prospect_key(
            draft_year=row["draft_year"],
            prospect_id=row["prospect_id"],
            player_name=row["player_name"],
            college_name=row["college_name"],
        )
        for _, row in frame.iterrows()
    ]
    result = (
        frame.loc[:, columns]
        .sort_values(["draft_year", "player_name", "college_name"], na_position="last")
        .drop_duplicates(subset=["prospect_key"])
        .reset_index(drop=True)
    )
    return result


def build_fact_draft_pick(draft_picks: pd.DataFrame) -> pd.DataFrame:
    """Build a draft-pick fact table from normalized draft rows."""
    columns = [
        "draft_pick_key",
        "prospect_key",
        "draft_year",
        "draft_round",
        "pick_number",
        "overall_pick",
        "team",
        "player_name",
        "prospect_id",
    ]
    if draft_picks.empty:
        return pd.DataFrame(columns=columns)

    frame = _normalize_draft_frame(draft_picks)
    frame = frame.dropna(subset=["draft_year", "draft_round", "pick_number", "player_name"]).copy()
    frame["prospect_key"] = [
        _build_prospect_key(
            draft_year=row["draft_year"],
            prospect_id=row["prospect_id"],
            player_name=row["player_name"],
            college_name=row["college_name"],
        )
        for _, row in frame.iterrows()
    ]
    frame["draft_pick_key"] = (
        frame["draft_year"].astype(int).astype(str)
        + "_"
        + frame["draft_round"].astype(int).astype(str)
        + "_"
        + frame["pick_number"].astype(int).astype(str)
    )
    return frame.loc[:, columns].drop_duplicates(subset=["draft_pick_key"]).reset_index(drop=True)


def _normalize_draft_frame(draft_picks: pd.DataFrame) -> pd.DataFrame:
    """Map draft input aliases into a stable transform contract."""
    frame = draft_picks.copy()
    frame["draft_year"] = pd.to_numeric(
        first_available_column(frame, ["draft_year", "season", "year"]), errors="coerce"
    )
    frame["draft_round"] = pd.to_numeric(
        first_available_column(frame, ["draft_round", "round", "round_number"]), errors="coerce"
    )
    frame["pick_number"] = pd.to_numeric(
        first_available_column(frame, ["pick_number", "pick", "pick_in_round"]), errors="coerce"
    )
    frame["overall_pick"] = pd.to_numeric(
        first_available_column(frame, ["overall_pick", "pick_overall", "pick_total", "overall"]), errors="coerce"
    )
    frame["team"] = normalize_team_values(
        first_available_column(frame, ["team", "team_abbr", "club_code", "franchise"])
    )
    frame["player_name"] = first_available_column(
        frame,
        ["player_name", "pfr_player_name", "full_name", "display_name", "name", "player"],
    )
    frame["college_name"] = first_available_column(frame, ["college_name", "college", "school"])
    frame["position"] = first_available_column(frame, ["position", "pos"])
    frame["nflverse_player_id"] = normalize_player_values(
        first_available_column(frame, ["player_id", "nflverse_player_id", "gsis_id"])
    )
    frame["pfr_player_id"] = normalize_player_values(
        first_available_column(frame, ["pfr_player_id", "pfr_id"])
    )
    frame["prospect_id"] = frame["nflverse_player_id"].fillna(frame["pfr_player_id"])
    return frame


def _build_prospect_key(
    *,
    draft_year: object,
    prospect_id: object,
    player_name: object,
    college_name: object,
) -> str:
    """Build a deterministic prospect key from best available identity fields."""
    if pd.notna(prospect_id):
        return f"{int(float(draft_year))}_{str(prospect_id).strip()}"
    normalized_name = str(player_name).strip().lower().replace(" ", "_")
    normalized_college = str(college_name).strip().lower().replace(" ", "_") if pd.notna(college_name) else "unknown_college"
    return f"{int(float(draft_year))}_{normalized_name}_{normalized_college}"
