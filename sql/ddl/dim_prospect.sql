CREATE TABLE IF NOT EXISTS dim_prospect (
    prospect_key TEXT PRIMARY KEY,
    prospect_id TEXT,
    player_name TEXT NOT NULL,
    college_name TEXT,
    position TEXT,
    draft_year INTEGER NOT NULL,
    nflverse_player_id TEXT,
    pfr_player_id TEXT,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (draft_year, player_name, college_name)
);

CREATE INDEX IF NOT EXISTS idx_dim_prospect_draft_year
    ON dim_prospect (draft_year);
