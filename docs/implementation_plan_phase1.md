# Phase 1 Implementation Plan

## Summary

Build the initial repository scaffold for an NFL warehouse platform with:
- modular Python package structure
- PostgreSQL DDL for dimensions, facts, bridge, and ETL logging tables
- `nflverse` extraction scaffolding
- dimension builders
- starter team offense, team defense, and player offense transforms
- deterministic tests and CI

## Design decisions

- `nflverse` is the only partially implemented data source in Phase 1
- pandas is the default concrete dataframe path
- adapters remain explicit and source-specific
- warehouse load behavior is deferred behind orchestration hooks
- licensed or unclear sources remain placeholders with TODO markers

## Deliverables

- scaffold under `src/nfl_data_platform/`
- DDL under `sql/ddl/`
- documentation under `docs/`
- tests under `tests/`
- GitHub Actions workflow for Ruff and pytest

## Out of scope

- full production scheduler integration
- full multi-source implementation
- complete warehouse loading and persistence logic
- advanced derived metrics that depend on additional sources
