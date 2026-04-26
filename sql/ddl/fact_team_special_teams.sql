CREATE TABLE IF NOT EXISTS fact_team_special_teams (
    team_special_teams_key TEXT PRIMARY KEY,
    team_key TEXT,
    game_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT NOT NULL,
    field_goal_attempts INTEGER,
    field_goals_made INTEGER,
    extra_point_attempts INTEGER,
    extra_points_made INTEGER,
    punts INTEGER,
    punt_yards NUMERIC(14, 2),
    kick_returns INTEGER,
    punt_returns INTEGER,
    team_rankings_special_teams_rating NUMERIC(14, 6),
    dvoa_special_teams NUMERIC(14, 6),
    source_name TEXT NOT NULL DEFAULT 'phase1_placeholder',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (team, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_team_special_teams_team_game
    ON fact_team_special_teams (team, game_id);
