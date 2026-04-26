# Local Setup

## Requirements

- Python 3.11+
- Docker Desktop or another local Docker runtime for warehouse development

If you are new to the project, read [`start_here.md`](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/start_here.md) first.
If you want practical run instructions, read [`how_to_use.md`](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/how_to_use.md).

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
```

Create local environment configuration:

```bash
cp .env.example .env
```

Start the local PostgreSQL warehouse:

```bash
docker compose up -d warehouse
```

Then verify connectivity:

```bash
nfl-data-platform check-db
```

Keep `DATABASE_URL` aligned with the `POSTGRES_*` values in `.env`.
Optional: update `NFLVERSE_DATA_DIR` if you want raw staged nflverse files written somewhere else.
Optional: update `TEMP_DATA_DIR` if you want CSV validation snapshots written somewhere else.

## Useful commands

Run tests:

```bash
python -m pytest
```

Run lint:

```bash
ruff check .
```

Verify the warehouse and apply DDL:

```bash
nfl-data-platform check-db
nfl-data-platform init-db
```

Stop the local warehouse:

```bash
docker compose down
```

Run the current nflverse pipeline:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

Raw staged nflverse files are written under `./data/nflverse/season_<season>/week_<week>/<season_type>/`.
CSV validation snapshots are written under `./data/temp/season_<season>/week_<week>/`.

Recommended first inspection path after a run:

- open `data/nflverse/.../` to see the staged raw nflverse extracts
- open `data/temp/.../extracted/` to see the normalized extracted frames used by the pipeline
- open `data/temp/.../transformed/` to see the cleaned tables
- open `data/temp/.../quality_results.csv` to see which checks passed
