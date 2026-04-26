# Source Catalog

## nflverse
Status: fully implemented source for the current Phase 3 pipeline.
Purpose: primary source for schedules, rosters, play-by-play, weekly player stats, weekly team stats, and draft picks.
Access pattern: Python package integration through `nflreadpy`.
Notes: authoritative baseline source for the current end-to-end pipeline. Empty required extracts are treated as failures for the requested run window. Draft data is loaded through `nflreadpy.load_draft_picks` in a separate draft pipeline.

## Next Gen Stats
Status: placeholder adapter.
Purpose: CPOE, separation, time to throw, and related tracking metrics.
Access pattern: TODO after confirming legal/public access path.
Notes: do not implement undocumented or restricted APIs.

## Pro-Football-Reference
Status: placeholder adapter.
Purpose: snap counts, advanced stats, and roster context support.
Access pattern: TODO after legality and scraping review.
Notes: retain the adapter boundary only; this source is not implemented yet.

## FTN / DVOA
Status: placeholder adapter.
Purpose: team-level offense, defense, and special teams efficiency ratings.
Access pattern: TODO after licensing and field availability review.
Notes: add only explicit supported fields in later phases.

## TeamRankings
Status: placeholder adapter with documented enrichment intent.
Purpose: public special teams metrics and rankings.
Access pattern: TODO after source review.
Notes: treated as an auxiliary enrichment source for team special teams ratings, not as the core grain source.

## PlayerProfiler
Status: placeholder adapter.
Purpose: fantasy usage metrics such as target share, snap share, and route participation.
Access pattern: TODO after source and licensing review.
Notes: should enrich, not redefine, canonical player keys.

## Future optional sources
- PFF: placeholder only, pending licensing
- betting odds APIs: placeholder only, pending selection and use-case definition
