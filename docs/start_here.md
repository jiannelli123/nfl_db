# Start Here

## Who this is for

This guide is for someone who:

- is new to this project
- understands only a little programming
- wants to know where to begin without reading every file first

If that sounds like you, this is the right place to start.

## What this project does

This project is building an NFL data pipeline.

A **pipeline** is just a repeatable set of steps that moves data from one place to another.

In this project, the steps are roughly:

1. get NFL data from a source
2. clean it up
3. reshape it into useful tables
4. check that the output looks reasonable
5. save the results

The main source right now is `nflverse`, through the Python package `nflreadpy`.

## What the project produces

The goal is to create structured NFL tables for analysis, such as:

- teams
- players
- games
- play-by-play
- team offense
- team defense
- team special teams
- player offense
- player defense
- player special teams
- draft prospects
- draft picks

You can think of these as organized spreadsheets that are easier to analyze than raw source files.

## What is already working

Right now, the project can:

- load settings from environment variables
- create the warehouse tables from SQL files
- pull real data from the nflverse adapter through `nflreadpy`
- pull draft pick data from `nflreadpy`
- stage raw source files under `data/nflverse/`
- build several cleaned tables in Python
- run basic quality checks
- load the warehouse tables into the database
- write ETL step rows into `etl_run_log`
- save run outputs as CSV files in `data/temp/`

## What is not finished yet

Right now, the project does **not** yet:

- implement the non-nflverse sources
- add advanced licensed/public enrichments beyond direct nflverse-compatible fields

So the project is usable end to end with nflverse, but it is still in an early multi-source stage.

## The most important folders

### `src/nfl_data_platform/`

This is where the main Python code lives.

### `sql/ddl/`

This contains SQL files that define the database tables.

Think of them as blueprints for the warehouse.

### `docs/`

This is where the written explanations live.

### `tests/`

This is where the automated checks live.

### `data/temp/`

This is where each pipeline run writes CSV outputs for inspection.

## The three files to understand first

If you only read three code files first, read these:

1. [`src/nfl_data_platform/orchestration/cli.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/orchestration/cli.py)
2. [`src/nfl_data_platform/orchestration/pipeline.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/orchestration/pipeline.py)
3. [`src/nfl_data_platform/adapters/nflverse.py`](/C:/Users/jiann/OneDrive/Projects/nfl_db/src/nfl_data_platform/adapters/nflverse.py)

Why these three:

- `cli.py` shows how the project is run
- `pipeline.py` shows the order of the main steps
- `nflverse.py` shows how source data is fetched

## The simplest mental model

If the project feels overwhelming, use this mental model:

1. **Config** tells the code what run to do.
2. **Adapter** fetches raw data.
3. **Transform** turns raw data into useful tables.
4. **Quality checks** test whether the output looks sane.
5. **Persistence** saves the results so you can inspect them.

That is the whole pipeline in one simple idea.

## What a run looks like

When you run the pipeline, this is what happens:

1. the code reads settings
2. the database table definitions are executed
3. the nflverse adapter tries to fetch raw data
4. the raw source files are staged under `data/nflverse/`
5. transform functions build output tables
6. quality checks run
7. warehouse tables are loaded into the database
8. ETL log rows are written
9. CSV files are written into `data/temp/`

There is also a separate draft run:

```bash
nfl-data-platform run-draft --season 2025
```

That command builds draft-specific outputs without mixing them into the weekly game pipeline.

## Where to look after a run

After running the pipeline, look in a folder like this:

[`data/temp/season_2025/week_1/reg_incremental`](/C:/Users/jiann/OneDrive/Projects/nfl_db/data/temp/season_2025/week_1/reg_incremental)

Inside that folder:

- `extracted/` contains raw source-level data
- `transformed/` contains cleaned output tables
- `quality_results.csv` contains validation results

This is the easiest place to understand what the code actually did.
If you also want to inspect the database side, look at the loaded warehouse tables and `etl_run_log`.

## A very important warning

Right now, required empty extracts are treated as failures.

That is a good thing because it makes the pipeline more trustworthy.
If a required source dataset is empty for the requested run window, the run should stop instead of quietly loading empty business tables.

## Recommended reading order

If you want to go deeper, read in this order:

1. [start_here.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/start_here.md)
2. [pipeline_explained.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/pipeline_explained.md)
3. [architecture.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/architecture.md)
4. [orchestration.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/orchestration.md)
5. [data_dictionary.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/data_dictionary.md)
6. [metric_definitions.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/metric_definitions.md)

## What to do next if you want to help build it

The best next area to work on is usually one of these:

- make source extraction more reliable
- improve data validation
- add more fact tables

If you are brand new, the safest way to learn is:

1. run the tests
2. run the pipeline
3. open the CSV outputs
4. compare what you see with the transform code

That will teach you how the pieces connect without needing to understand every implementation detail at once.
