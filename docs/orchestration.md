# Orchestration

## Current commands

The CLI is exposed through `nfl-data-platform` and currently supports:
- `init-db`: validate configuration and execute DDL files
- `run-phase1`: execute the current nflverse extraction, staging, transformation, validation, database loading, and CSV snapshot writing flow
- `run-draft`: execute the separate nflverse draft extraction, staging, transformation, validation, database loading, and CSV snapshot writing flow

## Runtime parameters

Supported arguments:
- `--season`
- `--week`
- `--season-type`
- `--full-refresh`

These arguments shape filtered reruns and will later support stat-correction backfills.

Draft runs currently use:
- `--season`
- `--full-refresh`

## Pipeline steps

1. load settings
2. create database engine and execute DDL files
3. instantiate `NFLVerseAdapter`
4. extract schedules, rosters/player identity, weekly team stats, weekly player stats, and play-by-play through `nflreadpy`
5. stage raw source files under `NFLVERSE_DATA_DIR`
6. build dimensions, `bridge_player_ids`, and `fact_game_pbp`
7. build team offense, team defense, team special teams, player offense, player defense, and player special teams facts
8. run expanded quality checks
9. load the implemented tables into the warehouse
10. write ETL step rows into `etl_run_log`
11. write CSV snapshots for validation
12. emit a structured result including staged file locations, load status, and batch metadata

## Draft pipeline steps

1. load settings
2. create database engine and execute DDL files
3. instantiate `NFLVerseAdapter`
4. extract draft picks through `nflreadpy.load_draft_picks`
5. stage raw draft files under `NFLVERSE_DATA_DIR/draft/`
6. build `dim_prospect` and `fact_draft_pick`
7. run draft-specific quality checks
8. load draft tables into the warehouse
9. write ETL step rows into `etl_run_log`
10. write CSV snapshots for validation

## Reproducibility notes

- source-specific identifiers are preserved for lineage
- run parameters are explicit and serializable
- staged raw extracts are replayable for a bounded season/week window
- warehouse writes are associated with an `etl_batch_id`
- ETL logs now include extract, transform, and load steps for the same batch
- future corrections should rerun a bounded season/week window rather than mutate rows ad hoc
