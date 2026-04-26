CREATE TABLE IF NOT EXISTS dim_team (
    team_key TEXT PRIMARY KEY,
    team_id TEXT NOT NULL UNIQUE,
    team_abbr TEXT NOT NULL,
    team_name TEXT NOT NULL,
    conference TEXT,
    division TEXT,
    franchise_name TEXT,
    first_season INTEGER,
    last_seen_season INTEGER,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_team_team_abbr ON dim_team (team_abbr);
