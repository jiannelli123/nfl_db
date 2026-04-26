# Database Schema

## Purpose

This document explains the warehouse schema for the NFL Data Platform.

A **schema** is the structure of a database.
It describes:

- what tables exist
- what each table is for
- how rows are organized
- how tables connect to each other

This document focuses only on the current warehouse tables in the implemented nflverse-backed pipeline:

- `dim_team`
- `dim_player`
- `dim_prospect`
- `dim_game`
- `fact_game_pbp`
- `fact_draft_pick`
- `fact_team_offense`
- `fact_team_defense`
- `fact_team_special_teams`
- `fact_player_offense`
- `fact_player_defense`
- `fact_player_special_teams`
- `bridge_player_ids`
- `etl_run_log`

## Simple warehouse model

This schema follows a common analytics pattern:

- **dimension tables** describe entities
- **fact tables** store events or measurements
- **bridge tables** map identifiers across systems
- **log tables** record pipeline activity

In plain language:

- dimensions answer "who" or "what"
- facts answer "what happened"
- bridges answer "how do these IDs match"
- logs answer "what did the pipeline do"

## High-level layout

### Dimension tables

- `dim_team`
- `dim_player`
- `dim_prospect`
- `dim_game`

### Fact tables

- `fact_game_pbp`
- `fact_draft_pick`
- `fact_team_offense`
- `fact_team_defense`
- `fact_team_special_teams`
- `fact_player_offense`
- `fact_player_defense`
- `fact_player_special_teams`

### Support tables

- `bridge_player_ids`
- `etl_run_log`

## How the tables relate

The warehouse is centered around games, teams, players, and plays.

At a high level:

- `dim_team` describes teams
- `dim_player` describes players
- `dim_prospect` describes draft prospect identities
- `dim_game` describes games
- `fact_game_pbp` stores play-level data
- `fact_draft_pick` stores draft picks
- team fact tables summarize team performance in a game
- player fact tables summarize player performance in a game
- `bridge_player_ids` connects player IDs across systems
- `etl_run_log` records what the pipeline ran

## Table-by-table reference

### `dim_team`

Purpose:
- Stores one row per canonical team.

Primary key:
- `team_key`

Important columns:
- `team_id`
- `team_abbr`
- `team_name`
- `conference`
- `division`
- `franchise_name`
- `first_season`
- `last_seen_season`

How to think about it:
- This is the master team table.
- If another table needs team context, this is the place that should define the team.

### `dim_player`

Purpose:
- Stores one row per canonical player.

Primary key:
- `player_key`

Important columns:
- `player_id`
- `player_name`
- `current_team`
- `position`
- `status`
- `rookie_season`
- `last_seen_season`

How to think about it:
- This is the master player table.
- It is meant to describe the player, not every game they played.

### `dim_game`

Purpose:
- Stores one row per game.

Primary key:
- `game_key`

Important columns:
- `game_id`
- `season`
- `season_type`
- `week`
- `gameday`
- `gametime`
- `home_team`
- `away_team`
- `stadium`
- `status`

How to think about it:
- This is the master game table.
- It gives the context needed to understand game-level and play-level facts.

### `dim_prospect`

Purpose:
- Stores one row per draft prospect identity.

Primary key:
- `prospect_key`

Important columns:
- `prospect_id`
- `player_name`
- `college_name`
- `position`
- `draft_year`
- `nflverse_player_id`
- `pfr_player_id`

How to think about it:
- This is intentionally separate from `dim_player`.
- It models who a player was at draft time, not their later NFL roster identity.

### `fact_game_pbp`

Purpose:
- Stores play-by-play data at the play level.

Primary key:
- `pbp_key`

Natural identifiers:
- `game_id`
- `play_id`

Grain:
- One row per play or play-level event.

Important columns:
- `posteam`
- `defteam`
- `down`
- `ydstogo`
- `yardline_100`
- `play_type`
- `yards_gained`
- `epa`
- `success`
- `first_down`
- `touchdown`

How to think about it:
- This is the most detailed football action table in the warehouse.
- Other team and player fact tables can be built from this level of detail.

### `fact_draft_pick`

Purpose:
- Stores one row per draft pick.

Primary key:
- `draft_pick_key`

Grain:
- One row per draft year, round, and pick number.

Important columns:
- `prospect_key`
- `draft_year`
- `draft_round`
- `pick_number`
- `overall_pick`
- `team`
- `team_key`
- `player_name`

How to think about it:
- This is the historical draft event table.
- It links a prospect to the team and slot where they were drafted.
- `team_key` is nullable because historical draft team strings may not always normalize cleanly.

### `fact_team_offense`

Purpose:
- Stores offensive team metrics for a game.

Primary key:
- `team_offense_key`

Grain:
- One row per team per game per season/week/season type.

Important columns:
- `team`
- `game_id`
- `season`
- `season_type`
- `week`
- `plays`
- `yards_gained`
- `points_scored`
- `total_epa`
- `epa_per_play`
- `success_rate`
- `explosive_play_rate`
- `early_down_epa`
- `third_down_conversion_rate`
- `red_zone_td_rate`

How to think about it:
- This is a summarized offensive performance table.
- Instead of many play rows, it gives one team-game summary row.

### `fact_team_defense`

Purpose:
- Stores defensive team metrics for a game.

Primary key:
- `team_defense_key`

Grain:
- One row per team per game per season/week/season type.

Important columns:
- `team`
- `game_id`
- `season`
- `season_type`
- `week`
- `plays_allowed`
- `yards_allowed`
- `points_allowed`
- `epa_allowed`
- `epa_allowed_per_play`
- `success_rate_allowed`
- `explosive_play_rate_allowed`
- `early_down_epa_allowed`
- `third_down_conversion_rate_allowed`
- `red_zone_td_rate_allowed`

How to think about it:
- This is the defensive mirror of team offense.
- It describes what the defense allowed in a game.

### `fact_team_special_teams`

Purpose:
- Stores team-level special teams metrics.

Primary key:
- `team_special_teams_key`

Grain:
- One row per team per game per season/week/season type.

Expected use:
- kicking
- punting
- returns
- field position and public special teams metrics

How to think about it:
- This table is now populated from nflverse-compatible weekly team stats.
- TeamRankings ratings and DVOA-style enrichments remain optional and may be null until those sources are wired later.

### `fact_player_offense`

Purpose:
- Stores player offense metrics for a game.

Primary key:
- `player_offense_key`

Grain:
- One row per player per game per season/week/season type.

Important columns:
- `player_id`
- `player_name`
- `team`
- `game_id`
- `completions`
- `attempts`
- `passing_yards`
- `passing_tds`
- `interceptions`
- `carries`
- `rushing_yards`
- `rushing_tds`
- `targets`
- `receptions`
- `receiving_yards`
- `receiving_tds`
- `target_share`
- `air_yards_share`

How to think about it:
- This table summarizes what one player did offensively in one game.

### `fact_player_defense`

Purpose:
- Stores player defense metrics for a game.

Primary key:
- `player_defense_key`

Grain:
- One row per player per game per season/week/season type.

Expected use:
- tackles
- sacks
- pressures
- coverage stats
- other defensive player metrics

How to think about it:
- This is the defensive player summary table.
- It is populated only from fields that exist directly in nflverse-compatible weekly player stats.
- Pressure fields stay null when the source does not provide both the numerator and denominator.

### `fact_player_special_teams`

Purpose:
- Stores player special teams metrics for a game.

Primary key:
- `player_special_teams_key`

Grain:
- One row per player per game per season/week/season type.

Expected use:
- kicking
- punting
- returns
- special teams usage

How to think about it:
- This is the player-level special teams fact table.

### `bridge_player_ids`

Purpose:
- Maps one canonical player to different source-system IDs.

Primary key:
- `bridge_player_ids_key`

Expected use:
- connect nflverse IDs to IDs from future sources like PFR, NGS, and PlayerProfiler

How to think about it:
- Different data sources may use different player IDs.
- This table helps the warehouse understand that those different IDs may represent the same person.
- In the current nflverse implementation, the `nflverse_player_id` column is the only populated source ID field.

### `etl_run_log`

Purpose:
- Records what the pipeline did during a run.

Primary key:
- `etl_run_log_key`

Important columns:
- `etl_batch_id`
- `pipeline_name`
- `step_name`
- `source_name`
- `season`
- `week`
- `season_type`
- `run_status`
- `rows_written`
- `error_message`
- `started_at`
- `finished_at`

How to think about it:
- This is the audit log for the pipeline.
- It answers questions like:
  - what ran?
  - when did it run?
  - did it succeed?
  - how many rows were written?

## Key design ideas

### Separate dimensions from facts

Why:
- dimensions stay relatively stable
- facts are event-driven and usually much larger
- this makes analysis cleaner and more consistent

### Keep canonical keys separate from source IDs

Why:
- source systems can change
- one player may have multiple IDs across vendors
- warehouse keys give the project a stable internal identity model

### Keep play-level and summary-level tables

Why:
- play-level data is flexible and detailed
- summary tables are faster and easier for many common analyses

### Log ETL activity

Why:
- debugging is easier
- reruns are easier to track
- failures become more visible

## What is defined now vs what may still evolve

The schema files already define the warehouse structure for the tables listed above.

What may still evolve later:

- additional columns
- stronger foreign key relationships
- more indexes
- more source-specific lineage fields
- richer enrichments and advanced metrics from future sources

## Suggested reading next

After this file, the most useful follow-up docs are:

- [data_dictionary.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/data_dictionary.md)
- [metric_definitions.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/metric_definitions.md)
- [pipeline_explained.md](/C:/Users/jiann/OneDrive/Projects/nfl_db/docs/pipeline_explained.md)
