# T-586 — Absent-Attribute Costing Study (NFL + MLB)

**Tier:** STANDARD · **Kind:** decision input, not a build · **Date:** 2026-09-28
**Base:** origin/main at 769d64d or later (T-581, 64c0313, confirmed landed).
**Scope fence honoured:** read-only over `src/`, `scripts/`, `deploy/`; public documentation only; nothing procured, registered for, or called on a paid API. `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` untouched (38.1 owns them). ADR-0066's verdict is not re-litigated.

## 0. What this study does and does not establish

**Establishes (factual):** what the code fetches and drops today, where each candidate could come from, the terms I found, and whether history exists to backtest it.

**Does NOT establish:** that any attribute carries edge. Nothing here is measured. The "informativeness" column is **judgement** (public research where cited, first principles otherwise). A priced, plausible, cheap attribute can still be worth nothing, as the EXP-027 EPA splits just were (ADR-0066: Brier delta -0.0007 [-0.0020, +0.0005], 1 of 6 seasons, neither model beats market close at n=48). Every item below still has to clear ADR-0042 D2 (pre-registered split, bootstrap delta CI excluding 0) before activation. This study recommends against no sport or market family.

**Unverified items are marked `[UNVERIFIED]`.**

## 1. Method note: independence from T-575

The absent list was re-derived from the code (what columns each ingestion module retains) and from the upstream dictionaries, not copied from T-575 Section 3. Where I agree with T-575 I say so from my own evidence. Attributes without an explainable mechanism were dropped (Section 5).

## 2. NFL

### 2.1 What the code holds
`nfl_ingestion.py` downloads full nflverse `games.csv` and `stats_team_week_{season}.csv` but keeps allowlisted columns only (11 schedule columns; 8 team-stat columns, from which `off_epa` = passing_epa + rushing_epa). The model consumes off_epa, def_epa_allowed, home_rest/away_rest (moneyline only).

Consequence: many "absent" attributes are already in bytes we download and discard. Their integration cost is an allowlist edit plus an accessor, not a new source.

### 2.2 Absent list, mechanisms, three-axis pricing

| # | Attribute | Mechanism (why it could matter) | (a) Source / terms | (b) Integration tier | (c) Backfill |
|---|---|---|---|---|---|
| N1 | Weather (temp, wind, roof, surface) | Wind/cold suppress passing and scoring; matters mostly for totals, weakly for sides | nflverse `games.csv` (temp, wind only for outdoor/open, roof, surface). Repo licence CC-BY-4.0 (code docstring says MIT: mismatch, see Section 6) | **Payload field** (already downloaded, dropped) | Deep, all seasons in one file; backtestable |
| N2 | Starting QB identity / QB change | QB is the largest single-player effect in football; team EPA lags a QB swap | `games.csv` away/home_qb_id/name | **Payload field** | Deep; backtestable |
| N3 | Head coach | Weak mechanism alone (proxy for scheme/4th-down aggression) | `games.csv` away/home_coach | **Payload field** | Deep |
| N4 | Referee tendency | Penalty/flag rates and pace vary by crew; small effect, mostly totals | `games.csv` referee; nflverse officials since 2015 | **Payload field** (name) / accessor for crew stats | 2015+ (officials); backtestable |
| N5 | Pace / pass rate over expectation | Plays per game and neutral pass rate change variance and totals; PROE has plausible predictive content | `stats_team_week` (attempts, carries, sacks); PROE proper needs pbp | **Payload field** for raw rates; **new accessor** for PROE (pbp, all seasons since 1999) | Deep |
| N6 | Pressure / sack rates, QB hits, penalties | Trench dominance drives EPA per play; sacks suffered / def_sacks / def_qb_hits are in the payload | `stats_team_week` (def_sacks, def_qb_hits, sacks_suffered, penalties) | **Payload field** | Same coverage as team-stats file `[coverage start to confirm]` |
| N7 | Rest/travel beyond rest-days | Timezone and distance shift; body-clock effects reported in the literature but small | Derivable from `games.csv` location/stadium/gametime; no travel field | **New accessor** (derivation, stadium coordinates table needed) | Deep |
| N8 | Injuries beyond existing flag | Availability of key players is real information the market prices fast | nflverse `injuries` (since 2009), `depth_charts`, `snap_counts` (since 2012) | **New accessor on new store** | Deep; but weekly Fri report timing means point-in-time discipline is needed |
| N9 | Scheme / personnel / formation / coverage (participation, ftn_charting) | Formation and coverage tendencies could explain matchup effects EPA hides | nflverse participation (2016+; 2023+ is FTN-sourced) and ftn_charting (2022+); **CC-BY-SA 4.0**, attribution "FTN Data via nflverse" (share-alike obligations `[UNVERIFIED for our use]`) | **New C1 module** | 2016+ backtestable, but 2023+ participation released only after the postseason: **not available in-season**; ftn_charting ~48h post-game |
| N10 | OL/DL matchup (NGS, PFR advstats) | Pass-block/rush win rates | nflverse nextgen_stats (2016+), pfr_advstats (2018+) | **New C1 module** | 2016+/2018+ |

### 2.3 Not-in-the-list note
Market-derived fields in `games.csv` (moneyline, spread_line, total_line) are outputs of the market being benchmarked; using them as features would blur the "beats the market" question. Excluded deliberately.

## 3. MLB

### 3.1 What the code holds
`mlb_ingestion.py` retains batter and pitcher game logs, `fetch_game_starters` (SP ids/names, venue id/name), lineups, completed-game runs. Schedule hydrate is `probablePitcher,team`. A code grep across `src/prediction_market_bot` for handedness, weather, bullpen found **nothing** (only an unrelated schedule-validator docstring about weather-suspended games). `get_opp_runs_scored` exists in `mlb_team_stats_store.py` and is used only by `scripts/exp022_totals_backtest.py`, not by a live model.

**Park factor (36.1):** ADR-0064 is **PROPOSED, not accepted or activated**. The real defect was ~15.26% of rows silently neutral (not the ~100% T-575 hypothesised). The repair landed on a branch (`_VENUE_NAME_ALIASES`) but is dry-run only and must still clear ADR-0042 D2. So: repaired in code, **not closed** for modelling purposes. The 2022-2024 static table is also a fixed-vintage input.

### 3.2 Absent list, mechanisms, three-axis pricing

| # | Attribute | Mechanism | (a) Source / terms | (b) Integration tier | (c) Backfill |
|---|---|---|---|---|---|
| M1 | Pitcher handedness x batter side (platoon) | Platoon splits are large and well established; direct relevance to player-hit props (KXMLBHIT) | MLB Stats API `people` (pitchHand, batSide). Free, no auth. **Terms `[UNVERIFIED]`: mlb.com/legal/copyright returned HTTP 406 to my fetch; do not assume commercial-use rights** | **New accessor on an existing store** (same API client; batter side and pitcher hand are per-player static fields) | Deep; backtestable |
| M2 | Park factor (repaired) | Hit environment differs by park | Static table already in repo | **Already built** (ADR-0064 pending) | Backtestable now; gated by 0064 acceptance |
| M3 | Opposing pitcher quality beyond identity | Faced-pitcher strength is the main driver of a batter's hit probability | Pitcher game logs already ingested | **Accessor on existing store** (pitcher logs are fetched) | Deep |
| M4 | Bullpen state / usage | Late-game pitching quality for in-game and totals markets; relievers face batters after the starter exits | Derivable from pitcher game logs already fetched (`is_start`=False rows) | **New accessor on existing store** | Deep for aggregates; live availability (fatigue) is forward-accrual |
| M5 | Lineup-slot context | Slot drives PA count, so hit-prop probability | `fetch_lineups` already exists; T4M uses batting_slot live | **Payload / existing accessor** for pregame; historical lineups need game-feed backfill | Historical lineups `[UNVERIFIED depth]`; Retrosheet has lineups for history |
| M6 | Weather (temp, wind, humidity, roof) | Wind and heat move run and HR environment; totals and hit props marginally | MLB live feed has a weather field `[UNVERIFIED]`; alternative Open-Meteo: **free tier non-commercial only**, <10k calls/day, CC-BY 4.0; paid tier is commercial. Venue coordinates need a table | **New external dependency** (or payload field if the game feed carries it) | Open-Meteo historical archive `[start year not confirmed]`; backtestable if the venue table exists |
| M7 | Defensive alignment / fielders | Shifts and fielder quality alter hit probability | Statcast (Baseball Savant CSV) `[terms UNVERIFIED]` | **New C1 module** | Statcast era (2015+), heavy data, defence metrics are noisy |
| M8 | Umpire zone | Strike zone size shifts K/BB and totals | Public umpire game logs `[UNVERIFIED terms]`; Retrosheet has umpire assignments | **New C1 module** | Deep via Retrosheet |
| M9 | Retrosheet history as backfill source | Enables deep game-level backfill for M4/M5/M8 | Retrosheet: free for any use incl. commercial; prominent attribution notice required (verified) | **New C1 module** (bulk files) | 1900s to present |

## 4. Ranking by expected informativeness per unit cost

**Informativeness is JUDGEMENT. Cost is factual.** Not measured edge. Where I cite general public research I give the finding, not a verified citation; the platoon-split and QB-value literature are well known, but I did not re-verify specific papers in this session `[UNVERIFIED citations]`. Otherwise reasoning from first principles.

### NFL
1. **N2 QB identity/change** — payload tier, deep backfill, largest plausible effect (first principles; QB effect is widely reported). Cheap AND backtestable.
2. **N1 weather** — payload tier, deep backfill. Plausible mainly for totals; low expected value for sides. Cheap AND backtestable.
3. **N6 pressure/sack/penalty rates** — payload tier. Overlaps with EPA, so incremental value doubtful (the same information-overlap concern that killed the EPA splits). Cheap AND backtestable.
4. **N5 pace/PROE** — raw rates payload tier; PROE needs pbp. Cheap AND backtestable.
5. **N8 injuries** — new store, deep backfill; market prices this fast, so edge doubtful.
6. **N7 travel** — derivation only; small effect.
7. **N4 referee, N3 coach** — weak mechanisms; cheap but low value.
8. **N9/N10 scheme, coverage, trench matchup** — highest cost (new module, share-alike licence, not in-season for 2023+ participation). Lowest priority.

### MLB
1. **M1 platoon (handedness)** — one new accessor on the existing API client; deep backfill; direct mechanism for the only live cell (player hits). Cheap AND backtestable, subject to terms `[UNVERIFIED]`.
2. **M3 opposing-pitcher quality** — data already fetched; tier is an accessor. Cheap AND backtestable.
3. **M2 park factor** — already built; the decision is ADR-0064 acceptance plus D2, not procurement.
4. **M5 lineup slot** — cheap live; history requires backfill work.
5. **M4 bullpen** — derivable from stored pitcher logs; moderately valuable for in-game/T4 and totals.
6. **M6 weather** — new external dependency and non-commercial free tier: a licensing question before an engineering one.
7. **M8 umpire, M7 defence** — new modules, noisy or unverified terms.

## 5. Not recommended for pursuit now (and why)

- **N9 scheme/personnel/coverage (participation, ftn_charting):** new module, CC-BY-SA share-alike terms unresolved for us, 2023+ participation not available in-season (cannot serve live forecasting), and its main mechanism overlaps EPA.
- **N10 NGS/PFR trench matchup:** new module, shorter history, high overlap with EPA.
- **N3 coach alone, N4 referee alone:** mechanism too weak to justify even payload-tier work by themselves; bundle only if N2 work is already open.
- **M7 defensive alignment:** noisy, heavy data, terms unverified.
- **M6 weather via Open-Meteo on the free tier:** the terms bar commercial use; do not build on it without a licensing decision.
- **Market-derived fields (lines, moneylines):** circular against the benchmark.

These are lower-priority, not recommendations against any sport or market family.

## 6. Findings for 38.1 to register (not written by this session)

1. **Licence docstring mismatch:** `nfl_ingestion.py` says "MIT license"; the nflverse-data repo is CC-BY-4.0, and FTN-sourced participation/ftn_charting are CC-BY-SA 4.0 with attribution "FTN Data via nflverse".
2. **Worktree-script race:** two concurrent `new_session_worktree.sh` runs failed with "could not lock config file .git/config: File exists" and left orphan branch `session/20260929T052119Z-absent-attribute-pricing` (no worktree, no commits; `git branch -d` refused, not force-deleted).
3. **Q7 vacuous in fresh worktrees:** ledger caches are absent, so the invariant check has nothing to read.

## 7. Operator decision input (ten-minute version)

- **Cheapest real experiments:** N2 (QB) + N1 (weather) on NFL; M1 (platoon) + M3 (opposing pitcher) on MLB. All are payload/accessor tier with deep history, so each can be built and run through ADR-0042 D2 without any procurement.
- **Gate before MLB M1:** resolve the MLB Stats API terms question (my fetch failed).
- **Decision for ADR-0064:** park factor's status is an acceptance decision, not a cost.
- **Prior to expect:** the EPA-splits result says re-cuts of correlated data tend to add nothing. N6 and N5 sit closest to that risk; N2 and M1 add information the current models do not see at all, which is why they rank first. This is judgement, not measurement.
