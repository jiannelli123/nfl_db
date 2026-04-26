CREATE TABLE IF NOT EXISTS dim_player (
    player_key TEXT PRIMARY KEY,
    player_id TEXT UNIQUE,
    player_name TEXT NOT NULL,
    current_team TEXT,
    position TEXT,
    status TEXT,
    rookie_season INTEGER,
    last_seen_season INTEGER,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_player_player_id ON dim_player (player_id);
CREATE INDEX IF NOT EXISTS idx_dim_player_current_team ON dim_player (current_team);
