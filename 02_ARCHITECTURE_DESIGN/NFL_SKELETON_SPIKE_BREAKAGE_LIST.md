# NFL Skeleton Spike — Breakage List

**Session:** T-474 / GG-202, 2026-08-21
**HEAD at time of writing:** `f3e1c6433a1b2615ecfa3a6285dd69aa67b9f052` (branch `session/20260821T190312Z-nfl-skeleton-spike`)
**Deliverable this session:** an NFL skeleton that resolves, groups, and epochs correctly, plus this list. **Not** the NFL trading arm — no C1 beyond a stub was built, no C2, no C3, `kelly_fraction` stayed 0.0 throughout, no cell was promoted above `NOT_IMPLEMENTED`. Not a go/no-go verdict on NFL.

**What was built:** four NFL `MarketType` members (`NFL_MONEYLINE`, `NFL_SPREAD`, `NFL_GAME_TOTAL`, `NFL_TEAM_TOTAL`) in `market_type_registry.py`, with series tickers (`KXNFLGAME`, `KXNFLSPREAD`, `KXNFLTOTAL`, `KXNFLTEAMTOTAL`) confirmed live against Kalshi's `/series` and `/events` endpoints on 2026-08-21 — not guessed from the MLB pattern. A `_SPORT_BY_MARKET_TYPE` map with fail-closed enforcement (ADR-0056 D1). A measured NFL ticker grammar (`_NFL_GRAMMAR`): date-tail shape `<YY><MON><DD><TEAMS>`, **no HHMM segment** — matches NBA's shape, not MLB's. All 20 `(family × band)` NFL cells seeded `NOT_IMPLEMENTED`. 40/40 existing registry regression tests plus 63/63 tests in the three other files importing the module pass with zero regressions.

Below is every place the shared machinery was exercised against the new NFL cells and what happened.

---

## Legend

- **PASS** — ran cleanly against an NFL cell/ticker with no code change needed.
- **SILENT GAP** — runs without error but produces no NFL-relevant output; the absence looks like "0 records" rather than a failure.
- **STRUCTURAL GAP** — the data shape or hardcoded assumption itself has no room for a second sport; adding NFL support requires a schema/architecture change, not just new data.
- **Recurrence** — will the same defect recur unchanged for NBA-normalization work and for NHL, or is it NFL-specific?

---

## 1. Ticker grammar / date derivation / cell lookup — PASS

| File:line | Result |
|---|---|
| `src/prediction_market_bot/c5_execution/market_type_registry.py:196` (`market_type_for_ticker`) | PASS — `KXNFLGAME-26AUG21NYJPIT-NYJ` resolves to `MarketType.NFL_MONEYLINE`. |
| `market_type_registry.py:328` (`parse_ticker_date`) / `:340` (`derive_game_date`) | PASS — `_NFL_GRAMMAR` (`has_hhmm=False`) correctly parses `26AUG21NYJPIT` → `2026-08-21` and `26FEB08SEANE` → `2026-02-08`. |
| `market_type_registry.py:737` (`resolve_kill_switch_state`) / `:747` (`halt_cell`) | PASS — the per-cell kill-switch store is keyed on `(MarketType, ExecutionBand)`, sport-agnostic by construction; `halt_cell(NFL_MONEYLINE, T1_MULTI_DAY, ...)` and its resolution both work with no change. |

**Recurrence:** N/A — these are now correctly generalized. The refusal-only grammar design (T-472/GG-191) is exactly what made this a PASS: a per-series grammar registration was already the pattern, so NFL was additive.

---

## 2. `venue_adapter.py`'s hardcoded `"tag": "nba"` — confirmed still present, still safely gated

| File:line | Result |
|---|---|
| `src/prediction_market_bot/c5_execution/venue_adapter.py:280-287` | PASS (defensive) — `fetch_markets()` guards with `if market_type is not MarketType.NBA_PLAYER_POINTS: return False, DS02Snapshot(...)` *before* reaching the hardcoded `"tag": "nba"` param. An NFL `MarketType` calling this adapter gets a clean `ok=False`, empty-snapshot no-op — not a crash, not a silent mis-tagged fetch. |

This is pre-existing **GG-174** (already registered — not re-registered here). Confirmed as of this session's HEAD that the guard still holds; no new gap.

**Recurrence:** Same pattern will hold for NHL — the guard is on `market_type`, not on any sport-specific string, so it generalizes to any non-NBA sport automatically. No action needed unless/until Polymarket NFL/NHL support is actually built (out of scope here).

---

## 3. `run_power_calc.py` / `run_band_monitor.py` — STRUCTURAL GAP, MLB-hardcoded at three levels

| File:line | Result |
|---|---|
| `scripts/run_band_monitor.py:128-129` (`DEFAULT_PORTFOLIO`, `DEFAULT_T4_LEDGER`) | STRUCTURAL GAP — defaults are literally `logs/.vps_portfolio_cache_mlb.json` and `logs/t4_mlb_resolved_ledger.jsonl`. No `--sport` axis; no NFL-equivalent path exists or is discoverable by this script. |
| `scripts/run_power_calc.py:344-374` (`run_all_cells`) | STRUCTURAL GAP — the T4 branch (`run_power_calc.py:366-372`) hardcodes the literal band string `"T4M-PROJ"` for every T4 record it processes, regardless of what `market_type` the record actually resolves to. There is no dispatch on sport or on ADR-0056 D2's future `T4NFL-` prefix family. If NFL T4 records ever land in the same ledger file, they would either be mislabeled under the MLB band string or (more likely, given the MLB-only default path) never be read at all. |
| `scripts/run_band_monitor.py:126` (`BOOK_BANDS = ("T1","T2","T3")`) | Not itself sport-specific — the tuple only names generic band strings — but inherits the same MLB-only-portfolio-file problem as the row above, so in practice it never sees NFL T1/T2/T3 records either. |

**Net effect:** this is GG-004's own governing tool (sample-adequacy / `n*` power calc). As written, it cannot compute `clean_n`/`n*` for any NFL cell — not because the cell-key math is wrong (`_regroup_by_cell` at `run_power_calc.py:334` is correctly generic, keyed on `MarketType` via `market_type_for_ticker()`), but because the two loaders it depends on default to MLB-only files and the T4 path hardcodes an MLB band label. This is a **SILENT GAP layered on a STRUCTURAL one**: pointing `--portfolio`/`--t4-ledger` at hypothetical NFL files would fix the T1-T3 path, but the T4 path's hardcoded `"T4M-PROJ"` string is a code change, not a flag.

**Recurrence:** Will recur identically for NHL. Will also recur for any NBA-normalization work that tries to bring NBA's book onto this same script (NBA already has its own separate paper-trading path per `04_EXECUTION/TODO_NEXT.md`'s dark/frozen status, so this has been latent — not previously exercised — rather than newly introduced).

**Closing cost estimate (next sport):** Small-to-medium. Needs (a) a `--sport` flag threading through `load_pool_by_band`/`load_t4_ledger` to select the right default file, and (b) replacing the hardcoded `"T4M-PROJ"` literal with a lookup keyed on the record's resolved `MarketType` → sport → that sport's T4 band-label convention (which itself depends on item 4 below, D2's `T4NFL-`/`T4NHL-` registries actually being built). Roughly a half-day task once a second sport has real ledger data to test against — cannot be meaningfully built or verified against zero live NFL records.

---

## 4. `logic_epoch.py` — STRUCTURAL GAP, ADR-0056 D3 is not yet implemented in code

| File:line | Result |
|---|---|
| `src/prediction_market_bot/logic_epoch.py:102-111` (`LogicEpochBoundary` `NamedTuple`) | STRUCTURAL GAP — no `sport` field. Fields are `epoch, resolving_gap, commit_sha, commit_utc, description, bands_affected`. |
| `logic_epoch.py:117` (`_BOUNDARIES`) | STRUCTURAL GAP — a single flat, global tuple. All 12 recorded boundaries are MLB-authored fixes; there is no per-sport partition. |
| `logic_epoch.py:530` (`CURRENT_LOGIC_EPOCH`) | STRUCTURAL GAP — a single global `int`, derived as `_BOUNDARIES[-1].epoch`. There is no second counter for NBA, NFL, or NHL. |
| `logic_epoch.py:560` (`clean_epoch_floor_for_band`) / `:576` (`is_clean_for_band`) | Currently correct *for the single-timeline model* — they filter `_BOUNDARIES` by `band in boundary.bands_affected`, giving each *band* its own effective floor within the one global timeline. This is a real, working mechanism, but it is band-scoped, not sport-scoped — it was never designed to answer "does NFL's timeline start at epoch 1." |

**What this means concretely:** ADR-0056 D3 was accepted this session (§4: "every sport's epoch counter is independent, starting fresh at epoch 1... four independent counters total"). The code that exists today implements zero of that — it implements one global counter that happens to only ever have been touched by MLB fixes, with NBA/NFL/NHL bands trivially getting a floor of `1` (the pre-history default) only because no boundary has ever named them in `bands_affected`. That is coincidentally the *same visible behavior* D3 wants for a brand-new sport's epoch-1 start, but for the wrong reason — it is an accident of "nothing ever touched this band" rather than a designed per-sport counter, and it silently breaks the moment any *shared* infrastructure fix (an `ALL_BANDS`-scoped boundary) gets recorded, since `ALL_BANDS` boundaries currently bump every band's floor globally, MLB and NFL alike, with no way to scope a genuinely-MLB-only shared-path fix away from NFL's still-fresh timeline.

**Recurrence:** Identical for NHL. Also retroactively relevant to NBA — NBA's own epoch floor has been riding the same "never named, so floor=1" default, not a real second counter; formalizing D3 will need to decide whether NBA's dark/frozen history should be reframed as "epoch 1, never bumped" or left exactly as-is.

**Closing cost estimate (next sport):** Medium. Requires adding a `sport: str` field to `LogicEpochBoundary` (or splitting `_BOUNDARIES` into a `dict[str, tuple[LogicEpochBoundary, ...]]`), updating `clean_epoch_floor_for_band`/`is_clean_for_band`/`epoch_for_timestamp` to take or infer a sport argument, and deciding what an `ALL_BANDS`-equivalent sentinel means across sports (does an MLB-only shared-path fix bump NFL's counter too, or not — this is exactly the kind of question ADR-0056 D3 answers in principle but the implementing session will have to encode explicitly). Not safely doable without at least one real cross-sport shared-path fix to test against — building it purely speculatively risks guessing the wrong sentinel semantics, the same failure class GG-124 already found once for the single-sport case.

---

## 5. `semantic_contracts.py` — vocabulary and checks are player-shaped and MLB-band-named; no game-level contract exists

| File:line | Result |
|---|---|
| `src/prediction_market_bot/c7_monitoring/semantic_contracts.py:290-403` (`SemanticFloorGuard`, `assert_floor`) | SILENT GAP — the floor invariant is `games_fetched > 0 ⟹ matched_players > 0`. Mechanically this executes fine with any two ints; semantically, "matched_players" describes nothing for `NFL_MONEYLINE`/`NFL_SPREAD`/`NFL_GAME_TOTAL`/`NFL_TEAM_TOTAL` — these are game-level markets with no player-matching step in their pipeline at all. If an NFL C1 stub were ever wired to call this guard, someone would have to decide what "matched_players" even means for a moneyline market (the natural analog is "matched_events"/"matched_markets", a different pipeline shape entirely) — the current guard cannot express that distinction, it can only be mis-used or bypassed. |
| `semantic_contracts.py:450` (`check_mlb_ba_range`) | STRUCTURAL GAP (by name) — MLB-specific batting-average range check, no NFL analog exists or would make sense (no equivalent "range" concept was designed for a moneyline/spread market). |
| `semantic_contracts.py:733` (`check_t1_mlb_threshold`), `:768` (`check_t4_proj_lambda`), `:806` (`check_t4_flow_score_diff`) | STRUCTURAL GAP — all three `BandInvariantChecker` methods are named for and scoped to specific MLB bands (`T1` MLB threshold, `T4M-PROJ` lambda decay, `T4M-FLOW` score-diff). There is no NFL-band invariant checker of any kind. **This means: if an NFL band ever goes live and drifts in some analogous way to what these three checks catch for MLB, nothing will catch it.** This is not a crash risk — it is a coverage gap that fails silently by design (absence of a check, not a check returning a false negative). |

**Recurrence:** Will recur identically for NHL, and is not NBA-specific either — NBA never had its own `BandInvariantChecker` methods written (it predates this pattern, per the file's own history), so NBA has ridden without this class of protection the whole time it's been dark. Formalizing a sport-agnostic (or per-sport-pluggable) contract shape is a real design task, not a data-seeding one.

**Closing cost estimate (next sport):** Medium-to-large — this is the least mechanical of the five gaps. It requires actually deciding what a game-level (non-player) semantic floor looks like (a genuine design question, not a rename), then writing NFL-specific `BandInvariantChecker` methods once there is real NFL band behavior to calibrate them against (impossible to do meaningfully before any NFL band is live — GG-001's own lesson, a stub-shaped check is worse than an honestly-absent one).

---

## Summary table

| # | File | Result | Recurs for NBA-normalization? | Recurs for NHL? | Close cost (next sport) |
|---|---|---|---|---|---|
| 1 | `market_type_registry.py` (grammar/lookup/kill-switch) | PASS | — | — | None |
| 2 | `venue_adapter.py` (GG-174 `"tag":"nba"`) | PASS (pre-existing guard) | — | — | None (unless Polymarket NFL/NHL is built) |
| 3 | `run_power_calc.py` / `run_band_monitor.py` | STRUCTURAL GAP | Yes (latent) | Yes | ~0.5 day, needs real ledger data |
| 4 | `logic_epoch.py` (ADR-0056 D3) | STRUCTURAL GAP | Yes (retroactive question) | Yes | Medium, needs a real cross-sport fix to test against |
| 5 | `semantic_contracts.py` | STRUCTURAL/SILENT GAP | Yes | Yes | Medium-large, design task not data task |

Plus **GG-202** (registered this session, not in the table above since it's a probe finding rather than a shared-machinery breakage): T4's `POLL_INTERVAL_S = 45` cadence assumption is unvalidated for NFL's drive-level, dead-period-clustered structure, and NFL game markets sit at the efficient end of this project's own market-efficiency gradient — a compounding, not merely additive, concern for the T4 latency thesis specifically.

---

## What this spike does *not* answer

Per the session's explicit scope: this is not a go/no-go verdict on NFL, not an activation recommendation, and not a claim that any of the five gaps above are the *only* ones — only that these are the ones the assigned Step 2/3 probe surfaced. `kelly_fraction` was never set above `0.0`. No cell was promoted above `NOT_IMPLEMENTED`. No C1 module, C2 feature set, or C3 model was built.
