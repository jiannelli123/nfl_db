# NFL Data Platform

Production-style NFL analytics repository for ingesting source data, standardizing identifiers, deriving metrics, and loading curated warehouse tables.

## Phase 1 scope

Phase 1 establishes the project scaffold, warehouse DDL, `nflverse` ingestion interfaces, dimension builders, starter fact transforms, documentation, tests, and CI.

Implemented in Phase 1:
- repository and package scaffold under `src/nfl_data_platform/`
- PostgreSQL DDL for dimension, fact, bridge, and ETL log tables
- `nflverse` adapter scaffolding with guarded imports
- dimension builders for teams, players, and games
- starter transforms for team offense, team defense, and player offense
- pipeline CLI scaffolding for local runs and future orchestration expansion
- deterministic pytest coverage and GitHub Actions lint/test workflow

Deferred after Phase 1:
- full warehouse load implementation
- complete source integrations for NGS, PFR, FTN, TeamRankings, PlayerProfiler, PFF, and betting APIs
- production scheduling and stateful retry handling
- advanced metrics that require additional lineage or licensed feeds

## Repository layout

```text
docs/                   Project documentation
sql/ddl/                Warehouse table DDL
sql/views/              Analytical view placeholders
src/nfl_data_platform/  Python package
tests/                  Deterministic unit tests
```

## Quick start

1. Create a Python 3.11+ environment.
2. Install the package with dev dependencies:

```bash
pip install -e .[dev]
```

3. Copy environment defaults:

```bash
cp .env.example .env
```

4. Run tests:

```bash
pytest
```

5. Run the Phase 1 pipeline scaffold:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

Each run writes extracted inputs, transformed outputs, and quality results as CSVs under `./data/temp/`.
