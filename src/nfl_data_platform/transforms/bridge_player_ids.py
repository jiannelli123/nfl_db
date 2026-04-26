"""Identity bridge builders."""

from __future__ import annotations

import pandas as pd


def build_bridge_player_ids(dim_player: pd.DataFrame) -> pd.DataFrame:
    """Build player identifier bridge rows from the canonical player dimension."""
    columns = [
        "bridge_player_ids_key",
        "player_key",
        "nflverse_player_id",
        "pfr_player_id",
        "ngs_player_id",
        "player_profiler_player_id",
        "pff_player_id",
        "source_name",
    ]
    if dim_player.empty:
        return pd.DataFrame(columns=columns)

    frame = dim_player.loc[:, ["player_key", "player_id"]].copy()
    frame = frame.dropna(subset=["player_key", "player_id"]).drop_duplicates(subset=["player_key"])
    frame["bridge_player_ids_key"] = frame["player_key"].astype(str) + "_nflverse"
    frame["nflverse_player_id"] = frame["player_id"]
    frame["pfr_player_id"] = pd.NA
    frame["ngs_player_id"] = pd.NA
    frame["player_profiler_player_id"] = pd.NA
    frame["pff_player_id"] = pd.NA
    frame["source_name"] = "identity_bridge"
    return frame[
        [
            "bridge_player_ids_key",
            "player_key",
            "nflverse_player_id",
            "pfr_player_id",
            "ngs_player_id",
            "player_profiler_player_id",
            "pff_player_id",
            "source_name",
        ]
    ].copy()
