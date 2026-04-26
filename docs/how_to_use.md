# How To Use The System

## Purpose

This guide explains how to use the project in a practical way.

It is meant for someone who wants to:

- install the project
- run the pipeline
- inspect the outputs
- understand what happened
- troubleshoot common problems

If you want the fastest path from "I have the repo" to "I can use it", start here.

## Before you begin

You need:

- Python 3.11 or newer
- a database connection string in `.env`
- Docker Desktop or another local Docker runtime for the bundled PostgreSQL service
- the project dependencies installed

The main source used by this project right now is `nflverse`, through `nflreadpy`.

## Step 1: install dependencies

From the project root, run:

```bash
pip install -e .[dev]
```

This installs:

- the project itself
- test tools like `pytest`
- the nflverse backend package `nflreadpy`

## Step 2: create your local environment file

Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env`.

The most important settings are:

```env
POSTGRES_DB=nfl_data_platform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nfl_data_platform
```

Other useful settings:

- `POSTGRES_PORT`
- `NFLVERSE_SEASONS`
- `NFLVERSE_DATA_DIR`
- `TEMP_DATA_DIR`

What they mean:

- `POSTGRES_PORT`: host port for the local Docker PostgreSQL container
- `NFLVERSE_SEASONS`: default season list the adapter should fetch
- `NFLVERSE_DATA_DIR`: where raw staged source files are written
- `TEMP_DATA_DIR`: where CSV validation snapshots are written

## Step 3: start the local warehouse

Start PostgreSQL from the repository root:

```bash
docker compose up -d warehouse
```

This starts the bundled local database defined in [`docker-compose.yml`](/C:/Users/jiann/OneDrive/Projects/nfl_db/docker-compose.yml).

## Step 4: verify the database connection

Run:

```bash
nfl-data-platform check-db
```

What this does:

- reads the database settings
- opens a real database connection
- runs a simple connectivity query
- prints the detected driver, dialect, database name, and server version

If this step fails, fix the database settings before moving on.

## Step 5: run the tests

Before running the full pipeline, make sure the project is healthy:

```bash
python -m pytest
```

If the tests pass, the code is in a good state for a local run.

## Step 6: create the database tables

Run:

```bash
nfl-data-platform init-db
```

What this does:

- reads the database settings
- creates a database engine
- executes the SQL files in `sql/ddl/`

In simple terms, this creates the warehouse tables the pipeline will use.

## Step 7: run the pipeline

Example:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

Even though the command is still named `run-phase1`, it now runs the current nflverse pipeline.

What this command does:

1. reads settings
2. extracts nflverse data with `nflreadpy`
3. stages raw files
4. builds warehouse tables in memory
5. runs quality checks
6. loads the warehouse tables into the database
7. writes CSV snapshots for inspection
8. writes ETL log rows to `etl_run_log`

### Run the separate draft pipeline

Example:

```bash
nfl-data-platform run-draft --season 2025
```

What this command does:

1. reads settings
2. extracts draft picks with `nflreadpy.load_draft_picks`
3. stages raw draft files
4. builds `dim_prospect` and `fact_draft_pick`
5. runs draft-specific quality checks
6. loads draft tables into the database
7. writes CSV snapshots for inspection
8. writes ETL log rows to `etl_run_log`

## What gets loaded

The current run loads these tables:

- `dim_team`
- `dim_player`
- `dim_game`
- `bridge_player_ids`
- `fact_game_pbp`
- `fact_team_offense`
- `fact_team_defense`
- `fact_team_special_teams`
- `fact_player_offense`
- `fact_player_defense`
- `fact_player_special_teams`

The draft run loads these tables:

- `dim_prospect`
- `fact_draft_pick`

## Where the files go

### Raw staged source files

These are written under a path like:

[`data/nflverse/season_2025/week_1/reg`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/nflverse/season_2025/week_1/reg)

These files are the raw extracted datasets for that run window.

Typical files:

- `schedules.csv`
- `rosters.csv`
- `pbp.csv`
- `weekly_player_stats.csv`
- `weekly_team_stats.csv`

Draft raw files are written under a path like:

[`data/nflverse/draft/season_2025`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/nflverse/draft/season_2025)

Typical draft files:

- `draft_picks.csv`

### CSV validation snapshots

These are written under a path like:

[`data/temp/season_2025/week_1/reg_incremental`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/temp/season_2025/week_1/reg_incremental)

Inside that folder:

- `extracted/` contains normalized extracted frames
- `transformed/` contains warehouse-style output tables
- `quality_results.csv` contains check results

Draft snapshots are written under a path like:

[`data/temp/draft/season_2025/incremental`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/temp/draft/season_2025/incremental)

## What to inspect after a run

If you want to confirm the run worked, inspect these in order:

1. `quality_results.csv`
2. `transformed/`
3. the database tables
4. `etl_run_log`

### `quality_results.csv`

This tells you which checks passed or failed.

Look for:

- duplicate-key failures
- null identifier failures
- missing week failures
- reconciliation failures
- freshness failures

### `transformed/`

This shows what the pipeline actually built before or alongside database loading.

This is often the easiest place to debug data shape issues.

### Database tables

After a successful run, the warehouse tables should contain rows for the requested season and week.

### `etl_run_log`

This table helps you understand:

- what steps ran
- whether they succeeded
- how many rows each step wrote
- whether any step was skipped because a frame was empty

## Common commands

Start the local PostgreSQL container:

```bash
docker compose up -d warehouse
```

Verify connectivity and initialize the warehouse:

```bash
nfl-data-platform check-db
nfl-data-platform init-db
```

Run tests:

```bash
python -m pytest
```

Run lint:

```bash
ruff check .
```

Run one week:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

Run a full season window:

```bash
nfl-data-platform run-phase1 --season 2025
```

Run a postseason window:

```bash
nfl-data-platform run-phase1 --season 2025 --season-type POST
```

Run a draft year:

```bash
nfl-data-platform run-draft --season 2025
```

## Common problems and what they mean

### Problem: `nflreadpy is required`

Meaning:

- the nflverse backend package is not installed in your current environment

Fix:

```bash
pip install -e .[dev]
```

or:

```bash
pip install nflreadpy
```

### Problem: required extracts returned no rows

Meaning:

- the requested run window did not return one or more required source datasets
- or the source backend could not produce the expected data for that filter

Fix:

- confirm the requested season/week is valid
- confirm `nflreadpy` is working in your environment
- inspect the staged output directory and ETL log

### Problem: database connection fails

Meaning:

- `DATABASE_URL` is missing or invalid
- or the database is not reachable

Fix:

- recheck `.env`
- confirm the database is running
- rerun `nfl-data-platform init-db`

### Problem: quality checks fail

Meaning:

- the pipeline ran, but the output did not meet one or more validation rules

Fix:

- open `quality_results.csv`
- find the failed check row
- inspect the matching transformed CSV
- compare that file to the related transform module in `src/nfl_data_platform/transforms/`

## Best way to learn the system

If you are still getting comfortable with the project, this is the best hands-on learning loop:

1. run `python -m pytest`
2. run `docker compose up -d warehouse`
3. run `nfl-data-platform check-db`
4. run `nfl-data-platform init-db`
5. run `nfl-data-platform run-phase1 --season 2025 --week 1`
6. open `data/temp/.../quality_results.csv`
7. open `data/temp/.../transformed/`
8. compare those outputs to the transform code

That gives you a real understanding of what the pipeline is doing.

## Suggested next docs

After this guide, the most useful follow-up docs are:

- [start_here.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/start_here.md)
- [pipeline_explained.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/pipeline_explained.md)
- [orchestration.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/orchestration.md)
- [data_dictionary.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/data_dictionary.md)
