CREATE TABLE IF NOT EXISTS fact_game_pbp (
    pbp_key TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    play_id BIGINT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT NOT NULL,
    week INTEGER NOT NULL,
    posteam TEXT,
    defteam TEXT,
    home_team TEXT,
    away_team TEXT,
    down INTEGER,
    ydstogo INTEGER,
    yardline_100 NUMERIC(10, 2),
    play_type TEXT,
    yards_gained NUMERIC(10, 2),
    epa NUMERIC(14, 6),
    success BOOLEAN,
    first_down BOOLEAN,
    touchdown BOOLEAN,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, play_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_game_pbp_game_id ON fact_game_pbp (game_id);
CREATE INDEX IF NOT EXISTS idx_fact_game_pbp_season_week ON fact_game_pbp (season, week);
