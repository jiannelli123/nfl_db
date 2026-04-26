CREATE TABLE IF NOT EXISTS fact_team_offense (
    team_offense_key TEXT PRIMARY KEY,
    team_key TEXT,
    game_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT NOT NULL,
    plays INTEGER NOT NULL DEFAULT 0,
    yards_gained NUMERIC(14, 2) NOT NULL DEFAULT 0,
    points_scored NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_epa NUMERIC(14, 6) NOT NULL DEFAULT 0,
    epa_per_play NUMERIC(14, 6) NOT NULL DEFAULT 0,
    success_rate NUMERIC(10, 6) NOT NULL DEFAULT 0,
    explosive_play_rate NUMERIC(10, 6) NOT NULL DEFAULT 0,
    early_down_epa NUMERIC(14, 6),
    third_down_conversion_rate NUMERIC(10, 6),
    red_zone_td_rate NUMERIC(10, 6),
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (team, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_team_offense_team_game ON fact_team_offense (team, game_id);
CREATE INDEX IF NOT EXISTS idx_fact_team_offense_season_week ON fact_team_offense (season, week);
