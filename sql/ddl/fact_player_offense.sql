CREATE TABLE IF NOT EXISTS fact_player_offense (
    player_offense_key TEXT PRIMARY KEY,
    player_key TEXT,
    game_id TEXT,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT,
    player_id TEXT,
    player_name TEXT NOT NULL,
    completions INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    passing_yards NUMERIC(14, 2) NOT NULL DEFAULT 0,
    passing_tds INTEGER NOT NULL DEFAULT 0,
    interceptions INTEGER NOT NULL DEFAULT 0,
    carries INTEGER NOT NULL DEFAULT 0,
    rushing_yards NUMERIC(14, 2) NOT NULL DEFAULT 0,
    rushing_tds INTEGER NOT NULL DEFAULT 0,
    targets INTEGER NOT NULL DEFAULT 0,
    receptions INTEGER NOT NULL DEFAULT 0,
    receiving_yards NUMERIC(14, 2) NOT NULL DEFAULT 0,
    receiving_tds INTEGER NOT NULL DEFAULT 0,
    target_share NUMERIC(10, 6),
    air_yards_share NUMERIC(10, 6),
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (player_id, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_player_offense_player_game
    ON fact_player_offense (player_id, game_id);
CREATE INDEX IF NOT EXISTS idx_fact_player_offense_season_week
    ON fact_player_offense (season, week);
