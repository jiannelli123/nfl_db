CREATE TABLE IF NOT EXISTS fact_team_defense (
    team_defense_key TEXT PRIMARY KEY,
    team_key TEXT,
    game_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT NOT NULL,
    plays_allowed INTEGER NOT NULL DEFAULT 0,
    yards_allowed NUMERIC(14, 2) NOT NULL DEFAULT 0,
    points_allowed NUMERIC(14, 2) NOT NULL DEFAULT 0,
    epa_allowed NUMERIC(14, 6) NOT NULL DEFAULT 0,
    epa_allowed_per_play NUMERIC(14, 6) NOT NULL DEFAULT 0,
    success_rate_allowed NUMERIC(10, 6) NOT NULL DEFAULT 0,
    explosive_play_rate_allowed NUMERIC(10, 6) NOT NULL DEFAULT 0,
    early_down_epa_allowed NUMERIC(14, 6),
    third_down_conversion_rate_allowed NUMERIC(10, 6),
    red_zone_td_rate_allowed NUMERIC(10, 6),
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (team, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_team_defense_team_game ON fact_team_defense (team, game_id);
CREATE INDEX IF NOT EXISTS idx_fact_team_defense_season_week ON fact_team_defense (season, week);
