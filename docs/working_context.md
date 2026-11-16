# Working Context

Running notes so any session working in this repository starts with the full NFL context: where the warehouse stands, known issues, and the owner's fantasy football league. Keep it current. When something here changes, edit this file in the same change.

Last updated: 2026-11-16.

## 1. Warehouse project (this repository)

### What it is

An NFL analytics warehouse built on nflverse data, pulled with `nflreadpy`, transformed with pandas, and loaded into PostgreSQL through SQLAlchemy and psycopg. The local database runs from `docker-compose.yml`. The project rules are in `AGENTS.md`.

CLI entry point: `nfl-data-platform`

| Command | Purpose |
|---|---|
| `check-db` | Verify the database connection |
| `init-db` | Create the warehouse tables from `sql/ddl/` |
| `run-phase1 --season <yyyy> --week <n>` | Weekly nflverse pipeline |
| `run-draft --season <yyyy>` | Separate draft pipeline. Run `run-phase1` first so `dim_team` is populated |

### Where it stands

- Phases 1 through 3 are complete. nflverse is the only implemented source.
- Tables loaded: `dim_team`, `dim_player`, `dim_game`, `dim_prospect`, `bridge_player_ids`, `fact_game_pbp`, `fact_draft_pick`, all six `fact_team_*` and `fact_player_*` tables, and `etl_run_log`.
- Implemented metrics: team EPA/play, success rate, explosive play rate, early down EPA, third down conversion rate, red zone TD rate, counting stats for special teams and player defense, and `fantasy_points_standard` (standard non-PPR scoring) on `fact_player_offense`.
- Deferred metrics: target share and air yards share (TODO in `transforms/player_offense.py`), CPOE, pressure rate, snap share, yards per route run, and DVOA.
- The NGS, PFR, FTN/DVOA, TeamRankings, PlayerProfiler, and PFF adapters are placeholders. Do not invent APIs for them (see `AGENTS.md`).

### History

- The repository was mostly built with OpenAI Codex on a Windows machine, then committed on 2026-04-25. That final commit also added `fantasy_points_standard`.
- `main` has 2 commits. No pull requests had been opened before 2026-11-16.
- Several docs link to absolute Windows paths (`/C:/Users/.../nfl_db/...`). Those links break on GitHub.

### Known issues (as of 2026-11-16)

- **CI fails on lint.** `.github/workflows/ci.yml` runs `ruff check .` before `pytest`, and ruff reports 89 errors: 80 `E501` line-too-long, 6 `I001` unsorted imports, 2 `F401` unused imports, and 1 `E712`. Every push will fail CI until these are fixed.
- **Possible flaky tests.** In a fresh container, the first full `pytest` run failed 2 tests in `tests/test_draft_pipeline.py`: `test_load_draft_tables_writes_rows_and_etl_log` and `test_run_draft_quality_checks_detects_missing_prospect_reference`. Every later run passed all 55 tests. The cause has not been investigated.
- **Docs gap.** `fantasy_points_standard` is missing from `docs/metric_definitions.md` and `docs/data_dictionary.md`.

## 2. Fantasy football: 2026 season league

Context from a live draft-assistant session on 2026-09-04.

### League format

- **All-flex skill positions.** The owner can start any mix of WR, RB, and TE ("I can have any amount of each"). Value is raw projected points; there is no positional replacement level.
- 1 QB, plus K and DEF slots.
- Snake draft from the **7th pick**: 7, 18, 31, 42, 55, 66, 79, 90, 103, 114, 127, 138, 151, 162, 175.
- **Assumed, never confirmed:** 12 teams and PPR scoring. ADP during the draft came from Fantasy Football Calculator's 12-team PPR data. Confirm scoring before relying on it, because the warehouse only has standard scoring.
- League platform: unknown.

### Drafted roster

| Rd | Pick | Player | Pos |
|---|---|---|---|
| 1 | 7 | Amon-Ra St. Brown | WR |
| 2 | 18 | Nico Collins | WR |
| 3 | 31 | Breece Hall | RB |
| 4 | 42 | Travis Etienne | RB |
| 5 | 55 | Bucky Irving | RB |
| 6 | 66 | Mike Evans | WR |
| 7 | 79 | Matthew Stafford | QB |
| 8 | 90 | Tony Pollard | RB |
| 9 | 103 | Jayden Reed | WR |
| 10 | 114 | Jordan Addison | WR |
| 11 | 127 | Rachaad White | RB |
| 12 | 138 | Rashid Shaheed | WR |
| 13 | 151 | Evan McPherson | K |
| 14 | 162 | Steelers | DEF |
| 15 | 175 | Najee Harris | RB |

That totals 6 WR, 6 RB, 1 QB, 1 K, 1 DEF, and 0 TE. This is the roster at draft time. Waiver moves and trades since then are unknown, so ask for the current roster before giving lineup advice.

### Strategy the owner agreed with

- Elite PPR WRs early; take an RB before each tier cliff.
- Never draft a TE. In all-flex scoring, TEs compete with WRs on raw points.
- Late-round QB; no backup QB (pick one up on waivers for a bye).
- K and DEF in the last rounds. Stream DEF week to week.

### Preferences and lessons

- **Verify current rosters, depth charts, and news before commenting on any player.** The owner rightly called out stale team knowledge during the draft. Free-agency moves the ADP table showed (as of Sep 2026) included Evans to SF, A.J. Brown to NE, Etienne to NO, Waddle to DEN, Kenneth Walker to KC, DJ Moore to BUF, and Kyler Murray to MIN. Treat memory as stale and check a live source.
- Answer decisively: give the pick first, then a short reason.
- The owner did not want Rashee Rice ("no more Rice").
- As of September 2026, Josh Jacobs was on the Commissioner Exempt list.

### Open threads

- During the draft session, the owner was offered a week-1 lineup and waiver watch list and didn't take it up. In-season lineup and waiver help needs current injuries, byes, and matchups.
- **Ways the warehouse could feed the league:**
  - load 2026 weeks with `run-phase1`
  - add `fantasy_points_ppr` (and half-PPR if needed) next to `fantasy_points_standard`, once scoring is confirmed
  - finish target share and air yards share, the most useful deferred metrics for WR/RB decisions
