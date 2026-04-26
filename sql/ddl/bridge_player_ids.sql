CREATE TABLE IF NOT EXISTS bridge_player_ids (
    bridge_player_ids_key TEXT PRIMARY KEY,
    player_key TEXT NOT NULL,
    nflverse_player_id TEXT,
    pfr_player_id TEXT,
    ngs_player_id TEXT,
    player_profiler_player_id TEXT,
    pff_player_id TEXT,
    source_name TEXT NOT NULL DEFAULT 'identity_bridge',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bridge_player_ids_player_key ON bridge_player_ids (player_key);
CREATE INDEX IF NOT EXISTS idx_bridge_player_ids_nflverse ON bridge_player_ids (nflverse_player_id);
