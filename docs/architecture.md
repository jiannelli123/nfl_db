# Architecture

## Overview

The NFL Data Platform is organized as a modular warehouse pipeline with clear boundaries between extraction, normalization, transformation, quality checks, and warehouse persistence.

The current implementation uses `nflreadpy` as the real nflverse backend. Additional public and licensed sources are still represented as explicit placeholder adapters so future integrations can plug into stable interfaces without reshaping the rest of the codebase.

## Package structure

- `adapters/`: source-specific extractors and adapter interfaces
- `config.py`: environment-backed settings
- `db/`: SQLAlchemy engine and database helpers
- `orchestration/`: pipeline composition and CLI entry points
- `quality/`: deterministic validation helpers
- `transforms/`: dimension and fact builders

## Data flow

1. Load runtime settings from environment variables.
2. Create a database engine and execute DDL files.
3. Instantiate the nflverse adapter backed by `nflreadpy`.
4. Extract schedules, rosters/player identity, play-by-play, weekly player stats, and weekly team stats.
5. Persist bounded raw staging files under `NFLVERSE_DATA_DIR`.
6. Standardize key identifiers at adapter boundaries.
7. Build dimensions plus `bridge_player_ids`.
8. Build fact tables at the target warehouse grain.
9. Run quality checks on required columns, duplicates, null identifiers, run-window coverage, and simple reconciliation.
10. Load the implemented tables into the warehouse.
11. Write CSV snapshots for validation.
12. Persist ETL metadata for each load step.

## Identifier strategy

Canonical warehouse keys are kept separate from source identifiers:
- dimension tables own stable warehouse keys
- `bridge_player_ids` links players across nflverse and future external systems
- fact tables preserve source identifiers needed for lineage and replay

## Refresh model

The pipeline is designed for reproducibility and weekly reruns:
- runs accept `season`, `week`, and `season_type`
- future stat corrections can be handled by replaying filtered pipeline ranges
- `etl_run_log` captures step status and source lineage for later operational use

## Current Phase 3 reality

Implemented now:
- table DDL can be executed during `init-db`
- real nflverse extraction works through `nflreadpy`
- bounded raw staging files are written for each run
- dimensions, bridge, and the current warehouse fact tables can be built in memory
- current warehouse tables can be loaded into the warehouse
- ETL step metadata is recorded in `etl_run_log`
- ETL logging covers extract, transform, and load steps for a batch
- CSV snapshots are written for inspection

Still pending:
- non-nflverse source implementation
- more advanced reconciliation and operational monitoring
