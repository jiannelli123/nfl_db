"""Player defense fact builders."""

from __future__ import annotations

import pandas as pd

from nfl_data_platform.transforms.normalization import (
    ensure_numeric_column,
    normalize_player_values,
    resolve_player_name_column,
    resolve_team_column,
    safe_rate,
)


def build_fact_player_defense(weekly_player_stats: pd.DataFrame) -> pd.DataFrame:
    """Build player defense facts from nflverse-compatible weekly player stats."""
    columns = [
        "player_defense_key",
        "player_id",
        "player_name",
        "team",
        "game_id",
        "season",
        "season_type",
        "week",
        "tackles",
        "assisted_tackles",
        "sacks",
        "qb_hits",
        "pressures",
        "interceptions",
        "passes_defended",
        "forced_fumbles",
        "pressure_rate",
    ]
    if weekly_player_stats.empty:
        return pd.DataFrame(columns=columns)

    frame = weekly_player_stats.copy()
    for column in ["player_id", "game_id", "season", "season_type", "week"]:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame["player_id"] = normalize_player_values(frame["player_id"])
    frame["player_name"] = resolve_player_name_column(frame)
    frame["team"] = resolve_team_column(frame)

    defensive_aliases = {
        "tackles": ["tackles", "def_tackles", "solo_tackles"],
        "assisted_tackles": ["assisted_tackles", "def_tackle_assists"],
        "sacks": ["sacks", "def_sacks"],
        "qb_hits": ["qb_hits", "hits"],
        "pressures": ["pressures"],
        "interceptions": ["interceptions", "def_interceptions"],
        "passes_defended": ["passes_defended", "def_pass_defended"],
        "forced_fumbles": ["forced_fumbles", "def_forced_fumbles"],
    }
    for target, aliases in defensive_aliases.items():
        default = pd.NA if target == "pressures" else 0
        series = pd.Series([default] * len(frame), index=frame.index)
        for alias in aliases:
            if alias in frame.columns:
                series = pd.to_numeric(frame[alias], errors="coerce").fillna(default)
                break
        frame[target] = series

    pressure_denominator = None
    for candidate in ["pass_rush_snaps", "pass_rush_plays"]:
        if candidate in frame.columns:
            pressure_denominator = frame[candidate]
            break
    if pressure_denominator is None or "pressures" not in frame.columns:
        frame["pressure_rate"] = pd.NA
    else:
        frame["pressure_rate"] = safe_rate(frame["pressures"], pressure_denominator)

    position = (
        frame.get("position", pd.Series([pd.NA] * len(frame), index=frame.index))
        .astype("string")
        .str.upper()
    )
    defensive_activity = pd.concat(
        [
            ensure_numeric_column(frame, "tackles", 0),
            ensure_numeric_column(frame, "assisted_tackles", 0),
            ensure_numeric_column(frame, "sacks", 0),
            ensure_numeric_column(frame, "qb_hits", 0),
            ensure_numeric_column(frame, "interceptions", 0),
            ensure_numeric_column(frame, "passes_defended", 0),
            ensure_numeric_column(frame, "forced_fumbles", 0),
        ],
        axis=1,
    ).sum(axis=1)
    defensive_positions = {"LB", "ILB", "OLB", "CB", "DB", "DE", "DL", "DT", "FS", "SS", "S", "NT"}
    frame = frame.loc[position.isin(defensive_positions) | defensive_activity.gt(0)].copy()
    if frame.empty:
        return pd.DataFrame(columns=columns)

    frame["player_defense_key"] = (
        frame["player_id"].astype(str)
        + "_"
        + frame["game_id"].astype(str)
        + "_"
        + frame["week"].astype(str)
    )
    return frame[columns].drop_duplicates(subset=["player_defense_key"]).copy()
