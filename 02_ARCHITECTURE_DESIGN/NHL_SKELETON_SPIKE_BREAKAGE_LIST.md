# NHL Skeleton Spike — Breakage List

**Session:** T-495 / EXP-024, 2026-08-25
**Deliverable this session:** an NHL skeleton mirroring T-474's NFL pattern exactly — cells + ticker grammar, no sizing, no C3. `kelly_fraction` stayed 0.0 throughout, no cell was promoted above `NOT_IMPLEMENTED`. Not a go/no-go verdict on NHL.

**What was built:** three NHL `MarketType` members (`NHL_MONEYLINE`, `NHL_PUCK_LINE`, `NHL_GAME_TOTAL`) in `market_type_registry.py`, with series tickers (`KXNHLGAME`, `KXNHLSPREAD`, `KXNHLTOTAL`) confirmed live against Kalshi's `/series` and `/events` endpoints on 2026-08-25 — measured against real 2026 Stanley Cup Finals events (e.g. `KXNHLGAME-26JUN14CARVGK`), not guessed from NFL/MLB's shape. A measured NHL ticker grammar (`_NHL_GRAMMAR`): date-tail shape `<YY><MON><DD><TEAMS>`, **no HHMM segment** — matches NBA/NFL's shape, not MLB's. All 15 `(family × band)` NHL cells seeded `NOT_IMPLEMENTED`. Full suite: 2930 passed, 28 skipped, zero regressions.

**Deviation from the literal task instruction, flagged per the task's own "measure, don't guess" discipline:** the task named four families (moneyline, puck line, game total, team total). Only three exist as real Kalshi series. See item 6 below (GG-217) — this is a genuine data-availability finding, not an oversight.

This file mirrors `NFL_SKELETON_SPIKE_BREAKAGE_LIST.md`'s structure and legend exactly; see that file for the full original probe methodology. Items 1-5 below restate that file's findings only insofar as they were re-confirmed to recur identically for NHL — full detail lives in the NFL file, not duplicated here.

---

## Legend

Same as `NFL_SKELETON_SPIKE_BREAKAGE_LIST.md`: PASS / SILENT GAP / STRUCTURAL GAP / Recurrence.

---

## 1. Ticker grammar / date derivation / cell lookup — PASS (shared, confirmed recurs)

`market_type_for_ticker`, `parse_ticker_date`/`derive_game_date`, and the per-cell kill-switch store all resolved NHL cells/tickers correctly with zero code change — `KXNHLGAME-26JUN14CARVGK-CAR` resolves to `MarketType.NHL_MONEYLINE`; `_NHL_GRAMMAR` (`has_hhmm=False`) correctly parses `26JUN14CARVGK` → `2026-06-14`. Same reason as NFL: the refusal-only per-series grammar registration (T-472/GG-191) is additive by design.

## 2. `venue_adapter.py`'s hardcoded `"tag": "nba"` — PASS (shared, confirmed recurs, pre-existing GG-174)

The `fetch_markets()` guard is on `market_type`, not a sport-specific string — an NHL `MarketType` calling this adapter gets the same clean `ok=False` no-op NFL got. No new gap; GG-174 not re-registered.

## 3. `run_power_calc.py` / `run_band_monitor.py` — STRUCTURAL GAP (shared, confirmed recurs, exactly as predicted in the NFL file)

MLB-hardcoded default file paths (`logs/.vps_portfolio_cache_mlb.json`, `logs/t4_mlb_resolved_ledger.jsonl`) and the hardcoded `"T4M-PROJ"` band-string literal in the T4 branch apply identically to NHL — no NHL-specific difference found. The NFL file's item 3 already named NHL as a predicted recurrence; this session confirms the prediction rather than discovering new shape.

## 4. `logic_epoch.py` — STRUCTURAL GAP (shared, confirmed recurs, ADR-0056 D3 still not implemented)

Single global `CURRENT_LOGIC_EPOCH` counter, no per-sport partition. NHL bands trivially get an epoch-1 floor for the same coincidental reason NFL does (no boundary has ever named them in `bands_affected`), not because a real per-sport counter exists. Identical to the NFL file's item 4 — no NHL-specific wrinkle found.

## 5. `semantic_contracts.py` — STRUCTURAL/SILENT GAP (shared, confirmed recurs)

`SemanticFloorGuard`'s `matched_players` vocabulary and the three MLB-named `BandInvariantChecker` methods have no NHL analog, for the same reason they have no NFL analog: these are game-level markets (moneyline/puck-line/total) with no player-matching step, and no NHL-band invariant checker exists or could yet be calibrated. Identical to the NFL file's item 5.

## 6. Missing NHL team-total series — NHL-SPECIFIC FINDING, registered as GG-217

| Check | Result |
|---|---|
| Full Kalshi `/series?category=Sports` listing (3512 series, fetched 2026-08-25) | No series matching NHL + team-total scope. |
| `KXNHLTOTAL` series detail | Scope = "Point Total" — game-level total, not team-scoped. |
| `KXNHLPTS` series detail | Scope = "Player Points" — player-scoped, not team-scoped. Ruled out as a false match. |

Unlike NFL (which had all four families confirmed live, including `KXNFLTEAMTOTAL`), NHL currently has only three of the four target families tradeable on Kalshi. `NHL_TEAM_TOTAL` was **not** added as a `MarketType` member this session — fabricating a ticker for it would (a) violate the project's measured-not-guessed discipline and (b) break `test_round_trips_for_every_market_type`, which requires every enum member to resolve to a real series ticker. Registered as **GG-217** (OPEN) rather than silently omitted. Re-check when Kalshi's NHL offering changes, or pending an operator decision on how to treat a family with no venue instrument.

**Recurrence:** NHL-specific as of this measurement date. Not predicted or found in the NFL spike (NFL had a full four-of-four match). Should be re-verified, not assumed, if this pattern is ever cited for a fifth sport.

---

## Summary table

| # | File / Finding | Result | Shared w/ NFL? | Close cost (next sport) |
|---|---|---|---|---|
| 1 | `market_type_registry.py` (grammar/lookup/kill-switch) | PASS | Yes, identical | None |
| 2 | `venue_adapter.py` (GG-174 `"tag":"nba"`) | PASS (pre-existing guard) | Yes, identical | None |
| 3 | `run_power_calc.py` / `run_band_monitor.py` | STRUCTURAL GAP | Yes, identical | ~0.5 day, needs real ledger data |
| 4 | `logic_epoch.py` (ADR-0056 D3) | STRUCTURAL GAP | Yes, identical | Medium, needs a real cross-sport fix to test against |
| 5 | `semantic_contracts.py` | STRUCTURAL/SILENT GAP | Yes, identical | Medium-large, design task not data task |
| 6 | Missing `KXNHLTEAMTOTAL` (GG-217) | NHL-SPECIFIC DATA GAP | No — NFL had 4/4 | Unknown — depends on Kalshi listing the series, or an operator call |

No cadence-analysis probe (GG-202's NFL-specific concern) was re-run for NHL this session — explicitly out of scope per the task's reduced-rigor authorization; NHL's own cadence question can wait.

---

## What this spike does *not* answer

Same as the NFL spike: not a go/no-go verdict on NHL, not an activation recommendation, not a claim that items 1-6 above are exhaustive. `kelly_fraction` was never set above `0.0`. No cell was promoted above `NOT_IMPLEMENTED`. No C1 module, C2 feature set, or C3 model was built. No efficiency-gradient probe was run.
