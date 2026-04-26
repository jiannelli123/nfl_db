# NFL Data Platform

Production-style NFL analytics repository for ingesting source data, standardizing identifiers, deriving metrics, and loading curated warehouse tables.

## Current status

The repository now includes a Phase 3 nflverse implementation using `nflreadpy` as the first real source backend.

Implemented so far:
- repository and package scaffold under `src/nfl_data_platform/`
- PostgreSQL DDL for dimension, fact, bridge, and ETL log tables
- `nflreadpy`-backed nflverse extraction for schedules, rosters/player identity, play-by-play, weekly player stats, and weekly team stats
- separate `nflreadpy`-backed draft extraction for draft picks
- bounded raw staging under `data/nflverse/`
- dimension builders for teams, players, and games
- draft dimension builder for prospects
- player identity bridge generation for `bridge_player_ids`
- play-by-play fact builder for `fact_game_pbp`
- draft pick fact builder for `fact_draft_pick`
- transforms for team offense, team defense, team special teams, player offense, player defense, and player special teams
- warehouse loading for `dim_team`, `dim_player`, `dim_game`, `dim_prospect`, `bridge_player_ids`, `fact_game_pbp`, `fact_draft_pick`, `fact_team_offense`, `fact_team_defense`, `fact_team_special_teams`, `fact_player_offense`, `fact_player_defense`, and `fact_player_special_teams`
- ETL step logging into `etl_run_log`
- stronger quality checks for identifiers, duplicates, referential integrity, run-window coverage, freshness, row-count drift, and simple reconciliation
- deterministic pytest coverage and GitHub Actions lint/test workflow

Still deferred:
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

## Documentation map

Start with:
- `docs/start_here.md` for a beginner-first introduction
- `docs/how_to_use.md` for practical run instructions
- `docs/pipeline_explained.md` for a plain-English walkthrough of the codebase

Then use:
- `docs/architecture.md` for higher-level system design
- `docs/orchestration.md` for runtime flow
- `docs/data_dictionary.md` for table definitions
- `docs/db_schema.md` for warehouse relationships and grain
- `docs/metric_definitions.md` for metric meaning
- `docs/source_catalog.md` for source lineage and adapter intent

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

4. Start the local warehouse:

```bash
docker compose up -d warehouse
```

5. Verify the database connection:

```bash
nfl-data-platform check-db
```

6. Run tests:

```bash
python -m pytest
```

7. Create the warehouse tables:

```bash
nfl-data-platform init-db
```

8. Run the current nflverse pipeline:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

9. Run the separate draft pipeline:

```bash
nfl-data-platform run-draft --season 2025
```

Each run:
- extracts data from `nflreadpy`
- stages raw source files under `./data/nflverse/season_<season>/week_<week>/<season_type>/`
- loads the implemented warehouse tables into the configured database
- writes validation snapshots under `./data/temp/`

Draft runs use:
- raw staging under `./data/nflverse/draft/season_<season>/`
- validation snapshots under `./data/temp/draft/season_<season>/`

If nflverse extraction returns an empty required dataset for the requested run window, the pipeline fails instead of silently loading empty business outputs.
If you are just getting oriented, read `docs/start_here.md` before digging into the code.
