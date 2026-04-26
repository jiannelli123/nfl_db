CREATE TABLE IF NOT EXISTS fact_draft_pick (
    draft_pick_key TEXT PRIMARY KEY,
    prospect_key TEXT NOT NULL,
    team_key TEXT,
    draft_year INTEGER NOT NULL,
    draft_round INTEGER NOT NULL,
    pick_number INTEGER NOT NULL,
    overall_pick INTEGER,
    team TEXT,
    player_name TEXT NOT NULL,
    prospect_id TEXT,
    source_name TEXT NOT NULL DEFAULT 'nflverse',
    etl_batch_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (draft_year, draft_round, pick_number)
);

CREATE INDEX IF NOT EXISTS idx_fact_draft_pick_prospect
    ON fact_draft_pick (prospect_key);

CREATE INDEX IF NOT EXISTS idx_fact_draft_pick_year
    ON fact_draft_pick (draft_year);
