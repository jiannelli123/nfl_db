CREATE TABLE IF NOT EXISTS fact_player_defense (
    player_defense_key TEXT PRIMARY KEY,
    player_key TEXT,
    game_id TEXT,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    team TEXT,
    player_id TEXT,
    player_name TEXT NOT NULL,
    tackles INTEGER,
    assisted_tackles INTEGER,
    sacks NUMERIC(10, 2),
    qb_hits INTEGER,
    pressures INTEGER,
    interceptions INTEGER,
    passes_defended INTEGER,
    forced_fumbles INTEGER,
    pressure_rate NUMERIC(10, 6),
    source_name TEXT NOT NULL DEFAULT 'phase1_placeholder',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (player_id, game_id, season, season_type, week)
);

CREATE INDEX IF NOT EXISTS idx_fact_player_defense_player_game
    ON fact_player_defense (player_id, game_id);
