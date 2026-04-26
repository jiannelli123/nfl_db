# Architecture

## Overview

The NFL Data Platform is organized as a modular warehouse pipeline with clear boundaries between extraction, normalization, transformation, quality checks, and warehouse persistence.

Phase 1 centers on `nflverse` as the only partially implemented source. Additional public and licensed sources are represented as explicit adapters so future integrations can plug into stable interfaces without reshaping the rest of the codebase.

## Package structure

- `adapters/`: source-specific extractors and adapter interfaces
- `config.py`: environment-backed settings
- `db/`: SQLAlchemy engine and database helpers
- `orchestration/`: pipeline composition and CLI entry points
- `quality/`: deterministic validation helpers
- `transforms/`: dimension and fact builders

## Data flow

1. Load runtime settings from environment variables.
2. Instantiate source adapters.
3. Extract schedules, rosters, play-by-play, and weekly stat inputs.
4. Standardize key identifiers at adapter boundaries.
5. Build dimension tables.
6. Build fact tables at the target warehouse grain.
7. Run quality checks on required columns, keys, and nullability.
8. Persist tables and ETL metadata in later phases.

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
