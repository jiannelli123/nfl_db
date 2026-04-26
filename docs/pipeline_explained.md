# Pipeline Explained

## What this project is trying to do

This repository is building an NFL data pipeline.

A **data pipeline** is a repeatable process that:

1. gets data from a source
2. cleans and reshapes it
3. checks that it looks correct
4. stores it somewhere useful for analysis

In this project, the main source is `nflverse`, which is a public NFL data ecosystem.

The long-term goal is to build a warehouse of NFL data that is easy to query and analyze.
That warehouse is meant to contain:

- team information
- player information
- game information
- play-by-play data
- team stats
- player stats

Right now, the code is in **Phase 1**.
That means the project already has the structure and core logic for a pipeline, but some parts are still scaffolding and placeholders.

## The big idea in plain English

Here is the full idea of how the system is supposed to work:

1. Read settings like which season to run and where data should go.
2. Connect to a data source.
3. Pull raw NFL data into memory.
4. Convert raw data into a cleaner and more consistent shape.
5. Build tables for teams, players, games, and stats.
6. Run simple checks to make sure the output is not obviously broken.
7. Save the results for validation now, and later load them into a database.

Today, step 7 is only partly implemented.
The pipeline now saves CSV files to a temp folder so the outputs can be inspected.
It does **not** fully load all tables into the warehouse database yet.

## The important folders

### `src/nfl_data_platform/`

This is the main Python package.
It contains the code that actually runs the pipeline.

### `docs/`

This folder holds written explanations of the system.
You are reading one of them now.

### `sql/ddl/`

This contains SQL files that define the database tables.

Think of these as blueprints for the warehouse tables.
They describe what columns each table should have.

### `tests/`

This contains automated tests.

A test is a small program that checks whether the code behaves the way we expect.

### `data/temp/`

This is where the pipeline now writes CSV snapshots for validation.

Each run creates a folder that contains:

- extracted source data
- transformed output tables
- quality check results

## The main code files and what they do

### `config.py`

File:
[`config.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/config.py)

This file reads configuration from environment variables.

An **environment variable** is just a setting outside the code, such as:

- which database to use
- which seasons to process
- where source data lives
- where temp CSV outputs should be written

The main settings are:

- `DATABASE_URL`
- `NFLVERSE_SEASONS`
- `NFLVERSE_DATA_DIR`
- `TEMP_DATA_DIR`

Why this matters:

- it keeps environment-specific values out of the code
- the same code can run on different machines
- local, test, and production environments can behave differently without changing source files

### `orchestration/cli.py`

File:
[`cli.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/orchestration/cli.py)

This is the command-line entry point.

It gives you commands like:

- `init-db`
- `run-phase1`

You can think of this file as the front door of the project.
It reads command-line arguments and decides which pipeline action to run.

Why this matters:

- it makes the project easy to run from a terminal
- it keeps the user-facing commands separate from the lower-level logic

### `orchestration/pipeline.py`

File:
[`pipeline.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/orchestration/pipeline.py)

This is the heart of the pipeline.

It coordinates the main steps:

1. initialize the database connection
2. extract raw data
3. build cleaned output tables
4. run quality checks
5. write CSV snapshots

This file does not contain all the detailed transformation logic itself.
Instead, it calls other modules that each do one specific job.

That is a good design choice because it keeps responsibilities separated.

### `orchestration/persistence.py`

File:
[`persistence.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/orchestration/persistence.py)

This file was added so pipeline runs can be saved as CSV files.

It builds a folder path based on the run context, for example:

`data/temp/season_2025/week_1/reg_incremental`

Then it writes:

- extracted source frames into `extracted/`
- transformed tables into `transformed/`
- quality checks into `quality_results.csv`

Why this matters:

- you can inspect the output even before full database loading is implemented
- it makes debugging much easier
- it gives a simple validation layer for early pipeline development

### `adapters/base.py`

File:
[`base.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/adapters/base.py)

This defines a base interface for data adapters.

An **adapter** is code that knows how to talk to one specific data source.

The base adapter says that every source should know how to fetch:

- schedules
- rosters
- play-by-play
- weekly player stats
- weekly team stats

Why this matters:

- different sources can plug into the same pipeline shape
- the rest of the code does not need to know every detail about each source

### `adapters/nflverse.py`

File:
[`nflverse.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/adapters/nflverse.py)

This is the main source adapter currently used in Phase 1.

Its job is to:

- call nflverse-compatible Python functions
- turn the result into a pandas DataFrame
- normalize column names to lowercase

Important detail:

If the backend library is not available, this adapter currently returns an empty DataFrame instead of crashing.

Why this matters:

- this is convenient for scaffolding and tests
- but it also means a run can appear successful while producing empty outputs

So if you see empty CSV files, it usually means the source adapter did not return real data.

### `transforms/dimensions.py`

File:
[`dimensions.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/transforms/dimensions.py)

This file builds dimension tables.

A **dimension table** stores descriptive information about entities.

Examples:

- `dim_team`: one row per team
- `dim_player`: one row per player
- `dim_game`: one row per game

What these functions do:

- collect raw fields from source tables
- group and deduplicate them
- build stable keys like `team_key`, `player_key`, and `game_key`

Why this matters:

- dimensions give the warehouse a consistent structure
- facts can point to dimensions using shared keys
- analysts can join tables more easily

### `transforms/team_offense.py`

File:
[`team_offense.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/transforms/team_offense.py)

This file creates `fact_team_offense`.

A **fact table** stores measured events or metrics.

In this case, the output is one row per team per game with offensive metrics such as:

- plays
- yards gained
- points scored
- total EPA
- EPA per play
- success rate
- explosive play rate
- early down EPA
- third down conversion rate
- red zone touchdown rate

This logic comes mostly from play-by-play data.

Why this matters:

- raw play-by-play is very detailed
- analysts usually want team-level summaries too
- this transform turns many play rows into one useful team-game row

### `transforms/team_defense.py`

File:
[`team_defense.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/transforms/team_defense.py)

This file builds `fact_team_defense`.

Instead of calculating everything from scratch, it mirrors the offensive output from the opponent.

Example:

- if Buffalo gained 300 yards on offense against Kansas City
- then Kansas City allowed 300 yards on defense in that same game

Why this matters:

- it reuses logic that already exists
- it keeps offense and defense metrics aligned

### `transforms/player_offense.py`

File:
[`player_offense.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/transforms/player_offense.py)

This file builds `fact_player_offense`.

It creates one row per player per game with fields like:

- completions
- attempts
- passing yards
- carries
- rushing yards
- targets
- receptions
- receiving yards

This version is still simple.
Some planned metrics like `target_share` and `air_yards_share` are marked as TODO.

Why this matters:

- it gets the player offense table shape in place early
- more advanced metrics can be added later without redesigning the whole pipeline

### `quality/checks.py`

File:
[`checks.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/quality/checks.py)

This file contains simple data validation checks.

Examples:

- are required columns present?
- are key columns unique?
- is a DataFrame empty?
- do required columns contain nulls?

Why this matters:

- pipelines often fail in subtle ways
- a file may exist but still be wrong
- these checks catch basic structural problems before data gets trusted

Right now the checks are intentionally lightweight.
They are useful, but they are not a full data quality framework yet.

### `db/engine.py`

File:
[`engine.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/db/engine.py)

This file creates a SQLAlchemy database engine from the configured database URL.

A **database engine** is an object that knows how to connect to a database.

Important detail:

At the moment, the project creates the engine, but it does not yet fully load pipeline outputs into the database.

So the database part is only partially wired.

## How one pipeline run works

Here is what happens during `run-phase1`.

### Step 1: settings are loaded

The code reads settings from the environment.

This tells the pipeline:

- what database URL to use
- what season to process
- where temp outputs should go

### Step 2: the database engine is created

The project checks that `DATABASE_URL` looks valid and creates an engine.

Right now this mainly proves that configuration is present.

### Step 3: raw data is extracted

The `NFLVerseAdapter` tries to fetch:

- schedules
- rosters
- play-by-play
- weekly player stats
- weekly team stats

These are returned as pandas DataFrames.

A **DataFrame** is like a spreadsheet in memory.
It has rows and columns.

### Step 4: dimension tables are built

The code creates:

- `dim_team`
- `dim_player`
- `dim_game`

These tables describe the core entities in the warehouse.

### Step 5: fact tables are built

The code creates:

- `fact_team_offense`
- `fact_team_defense`
- `fact_player_offense`

These tables hold game and player metrics.

### Step 6: quality checks are run

The pipeline checks whether:

- required columns exist
- keys are unique
- some fact outputs are non-empty

The results are stored in a list of structured check results.

### Step 7: CSV snapshots are written

The code writes the run output into a folder under `data/temp/`.

This gives you files you can open in Excel, a text editor, pandas, or another tool.

### Step 8: the pipeline returns status information

The CLI prints:

- how many quality results were produced
- where the CSV output directory is
- a message saying warehouse loading is still TODO

## Why CSV snapshots were added

Before the CSV step existed, the pipeline mostly worked in memory.
That meant the code could run, but it was harder to inspect what actually happened.

Saving CSVs helps because:

- it makes the pipeline easier to debug
- it gives a simple audit trail for a run
- it lets you validate data before full database loading is finished
- it is friendlier for people who want to inspect output without writing SQL

## What the SQL files are for

The files under `sql/ddl/` define the intended warehouse tables.

Examples include:

- `dim_team.sql`
- `dim_player.sql`
- `dim_game.sql`
- `fact_game_pbp.sql`
- `fact_team_offense.sql`
- `fact_team_defense.sql`
- `fact_player_offense.sql`
- `etl_run_log.sql`

These files describe what the database should eventually store.

They matter because they define:

- table names
- column names
- data types
- keys
- uniqueness rules

Right now, these SQL blueprints exist even though the pipeline is not yet loading all outputs into the warehouse.

## What is implemented vs what is still missing

### Implemented now

- project structure
- CLI commands
- settings loading
- database engine creation
- nflverse adapter scaffolding
- dimension builders
- starter fact builders
- lightweight quality checks
- CSV output snapshots
- automated tests

### Not fully implemented yet

- real DDL execution inside `init-db`
- full database loads
- ETL run logging into `etl_run_log`
- full population of `fact_game_pbp`
- special teams fact generation
- player defense fact generation
- richer validation rules
- stronger handling for empty-source runs
- additional external source integrations

## Why the code is organized this way

This project follows a modular design.

That means:

- configuration is in one place
- source access is in one place
- transforms are in separate files
- quality checks are separate from transforms
- orchestration is separate from business logic

This is helpful because:

- each file has a clearer job
- the code is easier to test
- one part can change without rewriting everything
- future contributors can understand the project faster

## What a beginner should focus on first

If you are new to programming or data engineering, the most useful mental model is:

1. **Config** says what run to do.
2. **Adapter** gets raw data.
3. **Transform** turns raw data into useful tables.
4. **Quality checks** ask, "Does this output look sane?"
5. **Persistence** saves the result somewhere.

If you keep that model in mind, most of the project will make sense.

## How to inspect a run

After running the pipeline, look inside a folder like:

[`data/temp/season_2025/week_1/reg_incremental`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/temp/season_2025/week_1/reg_incremental)

Inside that folder:

- `extracted/` holds source-level data
- `transformed/` holds cleaned output tables
- `quality_results.csv` tells you what checks passed or failed

This is the easiest way to understand what the pipeline is doing in practice.

## A simple example of the pipeline logic

Imagine one game:

- Buffalo vs Kansas City
- the raw play-by-play has many rows, one per play

The pipeline does not leave that information only as a long play list.
It also summarizes it.

For example, it can produce a single `fact_team_offense` row for Buffalo in that game with:

- total offensive plays
- total yards gained
- total EPA
- success rate

That summary is much easier to analyze than manually inspecting every play.

## Current limitation to remember

One of the most important current limitations is this:

If the nflverse backend is not available, the adapter returns empty DataFrames.

That means:

- the pipeline can still complete
- CSV files can still be written
- but the outputs may be empty

So a successful run does not always mean useful data was loaded.
It may only mean the code path completed without crashing.

## Final summary

This codebase is building a structured NFL data platform.

Its current pipeline:

- reads configuration
- extracts source data
- transforms raw data into warehouse-style tables
- runs simple quality checks
- saves CSV snapshots for inspection

The code is organized well for future growth, but it is still in an early stage.
The biggest missing piece is full warehouse loading and stronger production behavior.

If you want to understand the project in one sentence, it is this:

**The code is taking NFL data from a source, reshaping it into cleaner analytics tables, checking the result, and saving snapshots so the outputs can be reviewed while the full warehouse system is still being built.**
