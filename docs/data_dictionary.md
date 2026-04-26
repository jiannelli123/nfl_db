# Data Dictionary

## `dim_team`
Grain: one row per canonical team.
Keys: `team_key` primary key, `team_id` unique source-aligned identifier.
Purpose: canonical team metadata, abbreviations, conference, division, and franchise lineage fields.

## `dim_player`
Grain: one row per canonical player.
Keys: `player_key` primary key, `player_id` source-aligned identifier when available.
Purpose: player identity, roster context, and current status attributes.

## `dim_prospect`
Grain: one row per draft prospect identity.
Keys: `prospect_key` primary key, `prospect_id` source-aligned identifier when available.
Purpose: prospect identity, college, position, and draft-class attributes for the separate draft pipeline.

## `bridge_player_ids`
Grain: one row per canonical player and source-system mapping.
Keys: `bridge_player_ids_key` primary key.
Purpose: resolve player identifiers across nflverse, PFR, NGS, PlayerProfiler, and future licensed feeds. In the current Phase 3 pipeline, only `nflverse_player_id` is populated.

## `dim_game`
Grain: one row per game.
Keys: `game_key` primary key, `game_id` unique source-aligned identifier.
Purpose: schedule metadata, team matchup context, venue, season, week, and game status.

## `fact_game_pbp`
Grain: one row per play or event in play-by-play.
Keys: `pbp_key` primary key plus `game_id` and `play_id`.
Purpose: normalized play context for downstream team and player metric derivation.

## `fact_draft_pick`
Grain: one row per draft pick.
Keys: `draft_pick_key` primary key plus draft year, round, and pick grain columns.
Purpose: draft pick history with prospect linkage, overall pick context, and team selection data.

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
Purpose: team special teams metrics for kicking, punting, returns, and public ratings such as TeamRankings or DVOA enrichments when available.

## `fact_player_offense`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_offense_key` primary key plus natural grain columns.
Purpose: player passing, rushing, receiving, and usage metrics.

## `fact_player_defense`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_defense_key` primary key plus natural grain columns.
Purpose: player defense metrics derived directly from nflverse-compatible weekly player stats, including tackles, sacks, qb hits, interceptions, passes defended, and forced fumbles. Unavailable pressure fields remain null instead of being inferred.

## `fact_player_special_teams`
Grain: one row per player, season, week, season type, team, and game.
Keys: `player_special_teams_key` primary key plus natural grain columns.
Purpose: player-level special teams metrics for kicking, punting, and return production, with zero-filled defaults when public source coverage is incomplete.

## `etl_run_log`
Grain: one row per ETL run step.
Keys: `etl_run_log_key` primary key, `etl_batch_id`.
Purpose: capture execution timing, status, source lineage, row counts, and failure messages.
