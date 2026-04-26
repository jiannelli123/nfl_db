# Data Dictionary

## `dim_team`
Grain: one row per canonical team.
Keys: `team_key` primary key, `team_id` unique source-aligned identifier.
Purpose: canonical team metadata, abbreviations, conference, division, and franchise lineage fields.

## `dim_player`
Grain: one row per canonical player.
Keys: `player_key` primary key, `player_id` source-aligned identifier when available.
Purpose: player identity, roster context, and current status attributes.

## `dim_game`
Grain: one row per game.
Keys: `game_key` primary key, `game_id` unique source-aligned identifier.
Purpose: schedule metadata, team matchup context, venue, season, week, and game status.

## `fact_game_pbp`
Grain: one row per play or event in play-by-play.
Keys: `pbp_key` primary key plus `game_id` and `play_id`.
Purpose: normalized play context for downstream team and player metric derivation.

## `fact_team_offense`
Grain: one row per team, season, week, season type, and game.
Keys: `team_offense_key` primary key plus natural grain columns.
Purpose: curated offensive team metrics such as plays, yards, EPA, success rate, and conversion metrics.

## `fact_team_defense`
Grain: one row per team, season, week, season type, and game.
Keys: `team_defense_key` primary key plus natural grain columns.
Purpose: defensive metrics derived from opponent play and weekly summaries.

## `fact_team_special_teams`
Grain: one row per team, season, week, season type, and game.
Keys: `team_special_teams_key` primary key plus natural grain columns.
Purpose: placeholder schema for kicking, punting, returns, and public special teams ratings.

## `fact_player_offense`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_offense_key` primary key plus natural grain columns.
Purpose: player passing, rushing, receiving, and usage metrics.

## `fact_player_defense`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_defense_key` primary key plus natural grain columns.
Purpose: placeholder schema for tackles, pressures, coverage, and advanced defensive measures.

## `fact_player_special_teams`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_special_teams_key` primary key plus natural grain columns.
Purpose: placeholder schema for kicking, punting, returns, and snap-aligned special teams metrics.

## `bridge_player_ids`
Grain: one row per canonical player and source-system mapping.
Keys: `bridge_player_ids_key` primary key.
Purpose: resolve player identifiers across nflverse, PFR, NGS, PlayerProfiler, and future licensed feeds.

## `etl_run_log`
Grain: one row per ETL run step.
Keys: `etl_run_log_key` primary key, `etl_batch_id`.
Purpose: capture execution timing, status, source lineage, row counts, and failure messages.
