CREATE TABLE IF NOT EXISTS dim_game (
    game_key TEXT PRIMARY KEY,
    game_id TEXT NOT NULL UNIQUE,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    gameday DATE,
    gametime TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    stadium TEXT,
    status TEXT,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_game_season_week ON dim_game (season, week);
CREATE INDEX IF NOT EXISTS idx_dim_game_home_away ON dim_game (home_team, away_team);
