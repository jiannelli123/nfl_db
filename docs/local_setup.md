# Local Setup

## Requirements

- Python 3.11+
- PostgreSQL for warehouse development

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

Update `DATABASE_URL` to point at a local PostgreSQL instance.
Optional: update `TEMP_DATA_DIR` if you want CSV validation snapshots written somewhere else.

## Useful commands

Run tests:

```bash
pytest
```

Run lint:

```bash
ruff check .
```

Inspect planned DDL application:

```bash
nfl-data-platform init-db
```

Run the Phase 1 scaffold:

```bash
nfl-data-platform run-phase1 --season 2025 --week 1
```

CSV snapshots for each run are written under `./data/temp/season_<season>/week_<week>/`.
