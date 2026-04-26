# Metric Definitions

## Phase 1 implemented metrics

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
- `target_share` and `air_yards_share` remain TODO until a stable source feed is wired in Phase 2

## Deferred metrics

The following metrics are planned but not fully implemented in Phase 1:
- CPOE and time to throw from Next Gen Stats
- separation and route-running metrics from Next Gen Stats or PlayerProfiler
- snap-share-based usage metrics from PFR and PlayerProfiler
- pressure rate and advanced pass rush metrics from defensive sources
- DVOA family fields from FTN or compatible licensed/public distribution
- public special teams ratings and kicking/punting enhancements from TeamRankings and other sources

## Formula caveats

- formulas depend on source column availability and may be refined as additional adapters come online
- success and explosive play thresholds are encoded in transform logic and documented there
- red zone and third down rates depend on consistent play context fields in the normalized play-by-play input
