CREATE TABLE IF NOT EXISTS etl_run_log (
    etl_run_log_key TEXT PRIMARY KEY,
    etl_batch_id TEXT NOT NULL,
    pipeline_name TEXT NOT NULL,
    step_name TEXT NOT NULL,
    source_name TEXT NOT NULL,
    season INTEGER,
    week INTEGER,
    season_type TEXT,
    run_status TEXT NOT NULL,
    rows_written INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_etl_run_log_batch_id ON etl_run_log (etl_batch_id);
CREATE INDEX IF NOT EXISTS idx_etl_run_log_status ON etl_run_log (run_status);
