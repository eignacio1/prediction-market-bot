# Handoff W125.3 — H-EDGE-5 favourite-longshot + pot of gold per leaf

Last reviewed: 2026-11-24. Session: W125.3 (Sonnet 5.5). Branch `session/20261124T011322Z-w125-3-flb`.

## Result
- **H-EDGE-5: NOT SUPPORTED.** Pre-registered first (commits 42e706b, e7c0278), then run on 2025-26 regular season. 7 testable
  family x bucket cells, 0 SUPPORTED, BH q 0.10 rejects none. Hypothesis closed (EXP-H-EDGE-5, parked for R&D); reopen trigger in RESULT.md.
  Modal outcome (~65% none SUPPORTED) held. NHL ML [.50,.75) net -0.0432 [-0.0658,-0.0205], n 1,296 (population read earlier by W117.2).
  NBA ML [.90,.98) is a LEAD (+0.0496 [+0.0237,+0.0755]) but n 63 < 100: UNDERPOWERED, not routed; judge forward on 2026-27.
  NFL TT UNDERPOWERED; NHL TT no history (NO POPULATION). No leaf map changed.
- **Pot of gold per leaf: 0 of 18 judged leaves EARNED** (288 leaves, 80 pools, 10,430 settled forward rows). 15 judged leaves routed
  away (those leaves only); 3 NBA favourite-YES leaves continue with zero in the interval. FLB bucket is now a field on every leaf.
- **Parlays:** Kalshi lists combo markets (KXMVE* collections, public API, 11-23). Registered NOT_IMPLEMENTED: 4 MarketTypes x T1/T2/T3 + seat cells. Not built.

## Files
`12_EXPLORATORY/edge_location/h5_flb/{PREREG,RESULT,tables}.md, run_h5.py, fetch_h5.py, results.json`;
`12_EXPLORATORY/pot_of_gold/{score_w125.py,RESULT_W125.md,out/w125/}`; `tests/test_w125_3_flb.py` (9);
registry + `SEATS/{nba,nfl}.toml` + rendered seats; `HYPOTHESIS_DOCTRINE.md` II.1 (H-EDGE-5) and II.5 rows; CLAUDE.md Right-now regenerated.

## Caveats for the next window
- Part C joins settlements only through 11-20 (W122.2 fetch); later games unjoined. Re-run `score_w125.py` after a settlement refresh.
- Pool tau is a lower bound (tiers of one game share games).
- Fee schedule is today's, applied to 2025-26 history. Close is an hourly candle (0-60 min stale).
- Candle data under `h5_flb/data/` is gitignored; re-fetch with `fetch_h5.py` (24 workers, resumable; Kalshi caps ~4 req/s per IP).
- **B-024 conflict, needs operator/window ruling:** backlog "why" line should read "an arm of the same tree now, not a later phase"
  (DOCTRINE §6), but the block says not to edit ROLLING_BACKLOG.json. Not edited.

## Measures
- vision_pillar: PROOF (P2 +2 verdicts: H-EDGE-5 NOT SUPPORTED; pot-of-gold per-leaf IN_SAMPLE/routed) ; BREADTH B4 (combo families registered, NOT logging)
- gap_measure: P2 verdicts issued; B4 props/parlay families registered. gap_delta: P2 +2; B4 registered +4 (logging +0, stated).
- pattern_sweep: swept `src/ scripts/ tests/ 02_ARCHITECTURE_DESIGN/` for registry-count assumptions on MarketType and `_SPORT_BY_MARKET_TYPE`; 156 registry/seat/claude_md tests pass.
- surface_delta: 0 runtime components (no cron/service/workflow); +4 MarketType members (NOT_IMPLEMENTED), +2 analysis scripts (offline).
- Next look: re-score on settlement refresh; 17 pre-registered cells 2026-12-10.
