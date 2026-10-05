# W55.3 — MLB postseason shadow: games-cache source off statsapi (GG-470 / GG-453)

**Date:** 2026-10-05 · **Claim:** T-683..T-685, GG-480..GG-481 · **Status: BLOCKED at D2 (by design of the block)** — no code, no VPS write, no rows.

## D1 — fields the frozen model reads from the games cache
`MLBGameFeatureBuilder` (`mlb_game_pregame_features.py:47-61`): `status=="Final"`, `home_score`, `away_score`, `home`, `away` (via `canon`), `season`, `game_date`, `home_sp`, `away_sp` (int ids; keys a per-(season, pitcher) rolling runs-allowed history).
`MLBScheduleIndex`/`MLBForecaster` (`mlb_forecaster.py:85-125`): `start_utc`, `home`, `away`, `home_sp`, `away_sp` (starters passed into `builder.row`).

## D2 — ESPN scoreboard (VPS, HTTP 200) vs Stats API (Mac, HTTP 200), date 2026-10-03, 4 games
| Field | Result |
|---|---|
| game date / start_utc | match (17:00, 20:00, 22:30, 00:30Z) |
| status Final / home, away score | match (CLE 0-3 CWS, LAD 5-3 ATL, TB 1-0 NYY, MIL 3-2 SD) |
| team abbreviations | ESPN `CHW` vs Stats API `CWS`; `CANON` already maps CHW->CWS (no gap) |
| **home_sp / away_sp** | **DO NOT MATCH — different id namespace.** Stats API = MLBAM (e.g. 669373, 800048); ESPN scoreboard = ESPN athlete ids (e.g. 42409, 4619898). ESPN core athlete record carries no MLBAM id (`alternateIds.sdr`=4611966 is not MLBAM). |

Consequence: the builder's `_sp[(season, int(id))]` lookup is keyed on MLBAM history ids; ESPN ids would never match, so the starter feature would silently go null/degraded for every game — a changed model input, not a source swap. Frozen-model policy / EXP-037 pre-registration: **not substituted, not approximated.** D3 and D4 not attempted. ESPN would otherwise be a fine source for scores/status/schedule.

## Outcome
- GG-470: **stays OPEN** (no rows on disk). GG-453: stays OPEN. GG-472 untouched.
- No code, PR, VPS write, or t4-mlb change in this block.

## Operator decision (options, my read)
1. **Refresh locally, sync to VPS (cheapest, no model-input change).** Stats API range/date queries answer 200 from the Mac (confirmed today). Run `fetch_mlb_game_history.py --recent` here and scp `games_current.parquet` to the VPS before each T1 window (cron or manual). Identical fields to what the model was trained on. Needs a scheduled job on an always-on machine you control, or a hand-run daily.
2. **Hybrid: ESPN for results/status, Stats API per-date for starters only** — fewer 406-exposed calls but still depends on the throttled endpoint; weaker than 1.
3. **MLBAM<->ESPN crosswalk by name** — alters input provenance; needs your explicit sign-off as a pre-registration amendment before use. Not recommended.
4. Non-DO egress/proxy for statsapi (GG-470 option 3).
