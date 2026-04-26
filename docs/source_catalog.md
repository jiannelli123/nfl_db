# Source Catalog

## nflverse
Status: Phase 1 scaffold with partial implementation.
Purpose: primary source for schedules, rosters, play-by-play, weekly player stats, and weekly team stats.
Access pattern: Python package integration through `nfl_data_py` or `nflreadpy`, guarded by optional imports.
Notes: authoritative baseline source for initial warehouse construction.

## Next Gen Stats
Status: placeholder adapter.
Purpose: CPOE, separation, time to throw, and related tracking metrics.
Access pattern: TODO after confirming legal/public access path.
Notes: do not implement undocumented or restricted APIs.

## Pro-Football-Reference
Status: placeholder adapter.
Purpose: snap counts, advanced stats, and roster context support.
Access pattern: TODO after legality and scraping review.
Notes: retain adapter boundary only in Phase 1.

## FTN / DVOA
Status: placeholder adapter.
Purpose: team-level offense, defense, and special teams efficiency ratings.
Access pattern: TODO after licensing and field availability review.
Notes: add only explicit supported fields in later phases.

## TeamRankings
Status: placeholder adapter.
Purpose: public special teams metrics and rankings.
Access pattern: TODO after source review.
Notes: likely auxiliary source rather than core grain source.

## PlayerProfiler
Status: placeholder adapter.
Purpose: fantasy usage metrics such as target share, snap share, and route participation.
Access pattern: TODO after source and licensing review.
Notes: should enrich, not redefine, canonical player keys.

## Future optional sources
- PFF: placeholder only, pending licensing
- betting odds APIs: placeholder only, pending selection and use-case definition
