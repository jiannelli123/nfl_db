# Metric Definitions

## Phase 3 implemented metrics

### Team offense
- `plays`: count of offensive plays in scope
- `yards_gained`: sum of play yards
- `points_scored`: scoreboard points associated with the team-game row
- `total_epa`: sum of offensive EPA
- `epa_per_play`: `total_epa / plays`
- `success_rate`: successful plays divided by offensive plays
- `explosive_play_rate`: explosive plays divided by offensive plays
- `early_down_epa`: average EPA on first and second down plays
- `third_down_conversion_rate`: first downs or touchdowns on third down divided by third downs faced
- `red_zone_td_rate`: touchdowns in red zone divided by red zone plays

### Team defense
- allowed metrics are calculated from opponent play rows at the same game grain
- rate formulas mirror team offense using opponent outcomes

### Player offense
- starter fields include passing, rushing, and receiving volume from weekly player stats
- `target_share` and `air_yards_share` remain TODO until a stable denominator strategy is added in a later phase

### Team special teams
- `field_goal_attempts` and `field_goals_made`: kicking attempts and made kicks at the team-game grain
- `extra_point_attempts` and `extra_points_made`: extra point volume and conversions
- `punts` and `punt_yards`: punt counts and punt yardage
- `kick_returns` and `punt_returns`: public return counts at the team-game grain
- `team_rankings_special_teams_rating`: optional public special teams rating enrichment
- `dvoa_special_teams`: optional FTN-style special teams efficiency enrichment

Assumptions:
- team special teams inputs come from nflverse-compatible weekly team stats when core counting columns exist
- public ratings such as TeamRankings and DVOA are optional enrichments and may be null until wired
- alias columns like `fg_att` and `xp_att` are treated as equivalent to the warehouse field names

### Player special teams
- `field_goal_attempts` and `field_goals_made`: player kicking volume when available
- `extra_point_attempts` and `extra_points_made`: player extra point volume when available
- `punts` and `punt_yards`: player punting volume when available
- `kick_returns` and `kick_return_yards`: player kickoff return production
- `punt_returns` and `punt_return_yards`: player punt return production

Assumptions:
- missing public special teams columns default to zero instead of failing the transform
- alias columns like `kickoff_returns` and `kickoff_return_yards` are accepted as nflverse-compatible inputs

### Player defense
- `tackles`: direct nflverse-compatible tackle total when present
- `assisted_tackles`: direct assisted tackle total when present
- `sacks`: direct sack total when present
- `qb_hits`: direct quarterback hit total when present
- `pressures`: left null unless a direct source field exists
- `interceptions`: direct interception total when present
- `passes_defended`: direct pass-defense total when present
- `forced_fumbles`: direct forced-fumble total when present
- `pressure_rate`: only populated when both a pressure numerator and pass-rush denominator are present

Assumptions:
- player defense only maps fields that exist directly in nflverse-compatible weekly player stats
- pressure metrics are not inferred from sacks or qb hits
- rate stats remain null when the denominator is missing or zero

## Deferred metrics

The following metrics are planned but not fully implemented:
- CPOE and time to throw from Next Gen Stats
- separation and route-running metrics from Next Gen Stats or PlayerProfiler
- snap-share-based usage metrics from PFR and PlayerProfiler
- pressure rate and advanced pass rush metrics from defensive sources
- DVOA family fields from FTN or compatible licensed/public distribution beyond the current optional special teams enrichment
- richer public special teams ratings and kicking/punting enhancements from TeamRankings and other sources

## Formula caveats

- formulas depend on source column availability and may be refined as additional adapters come online
- success and explosive play thresholds are encoded in transform logic and documented there
- red zone and third down rates depend on consistent play context fields in the normalized play-by-play input
