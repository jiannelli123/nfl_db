CREATE TABLE IF NOT EXISTS fact_player_special_teams (
    player_special_teams_key TEXT PRIMARY KEY,
    player_key TEXT,
    game_id TEXT,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT,
    player_id TEXT,
    player_name TEXT NOT NULL,
    field_goal_attempts INTEGER,
    field_goals_made INTEGER,
    extra_point_attempts INTEGER,
    extra_points_made INTEGER,
    punts INTEGER,
    punt_yards NUMERIC(14, 2),
    kick_returns INTEGER,
    kick_return_yards NUMERIC(14, 2),
    punt_returns INTEGER,
    punt_return_yards NUMERIC(14, 2),
    source_name TEXT NOT NULL DEFAULT 'phase1_placeholder',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (player_id, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_player_special_teams_player_game
    ON fact_player_special_teams (player_id, game_id);
