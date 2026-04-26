# Orchestration

## Phase 1 commands

The CLI is exposed through `nfl-data-platform` and currently supports:
- `init-db`: validate configuration and list DDL files intended for execution
- `run-phase1`: execute the scaffolded extraction, transform, and validation flow

## Runtime parameters

Supported arguments:
- `--season`
- `--week`
- `--season-type`
- `--full-refresh`

These arguments shape filtered reruns and will later support stat-correction backfills.

## Pipeline steps

1. load settings
2. create database engine
3. instantiate `NFLVerseAdapter`
4. extract schedules, rosters, weekly team stats, weekly player stats, and play-by-play
5. build dimensions
6. build team offense, team defense, and player offense facts
7. run lightweight quality checks
8. emit a structured result for future persistence in `etl_run_log`

## Reproducibility notes

- source-specific identifiers are preserved for lineage
- run parameters are explicit and serializable
- future warehouse loading should associate each write with an `etl_batch_id`
- future corrections should rerun a bounded season/week window rather than mutate rows ad hoc
