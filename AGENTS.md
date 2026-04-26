# AGENTS.md

## Project intent
This repository is an NFL data platform focused on ingestion, normalization, metric derivation, and analytical storage.

## Technical standards
- Use Python 3.11+
- Prefer simple, modular code
- Add type hints to public functions
- Add docstrings to modules and important functions
- Keep logic split into small files by responsibility
- Avoid large monolithic scripts

## Architecture rules
- Store package code under `src/nfl_data_platform/`
- SQL DDL belongs under `sql/ddl/`
- Analytical views belong under `sql/views/`
- Documentation belongs under `docs/`
- Tests belong under `tests/`

## Data model rules
Always maintain these warehouse tables:
- dim_team
- dim_player
- dim_game
- fact_game_pbp
- fact_team_offense
- fact_team_defense
- fact_team_special_teams
- fact_player_offense
- fact_player_defense
- fact_player_special_teams

## Source integration rules
Primary source is nflverse.
Other sources should be integrated through adapters with clear interfaces.
Do not fabricate undocumented APIs.
For paid or restricted sources, create interfaces and placeholders with TODOs.

## Metric rules
Support these metric families where source data permits:
- EPA/play
- success rate
- explosive play rate
- early down EPA
- third down conversion rate
- red zone TD rate
- CPOE
- target share
- air yards share
- yards per route run
- pressure rate
- special teams kicking and punting metrics
- DVOA fields at team level when available

## Workflow rules
For complex tasks:
1. inspect existing files first
2. propose a short plan
3. implement in small steps
4. keep diffs focused
5. update docs when behavior changes

## Coding behavior
- Do not refactor unrelated files
- Do not rename files unless necessary
- Preserve consistent naming across tables, columns, and Python modules
- When uncertain, choose explicitness over abstraction

## Testing expectations
- Add or update tests for new logic
- Add lightweight validation for transforms and config
- Prefer deterministic tests

## Documentation expectations
When a new table or metric is introduced, update:
- docs/data_dictionary.md
- docs/metric_definitions.md
- docs/source_catalog.md if source lineage changes