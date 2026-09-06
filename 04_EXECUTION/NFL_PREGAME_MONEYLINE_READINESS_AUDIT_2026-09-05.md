# NFL Pregame-Moneyline Readiness Audit — 2026-09-05 (T-523)

**Tier:** STANDARD. **Deliverable:** this document — a measurement, not a build. No `src/` or `scripts/` file was touched to produce it. No `kelly_fraction` or `CellStatus` value was changed.

**Scope:** trace the single cheapest path — one NFL pregame moneyline bet, T1 band, end to end — through every pipeline stage, and report what exists, what is missing, and what it would take. This is not a survey of NFL readiness across all bands or all market types; it is the one path that would have to work first.

---

## Top-line answer

**No. A real NFL pregame moneyline bet cannot be placed by 2026-09-09 (four days from this audit).**

**Binding constraint:** the NFL-specific build gap is the primary blocker — four material components (GG-247 through GG-250 below) do not exist yet, none has been started, and one (GG-250, the run/resolve scripts) cannot even begin until the other three land, because it has nothing to call. This is not a four-day gap to close; §"Feasibility detail" below gives a rough floor.

**Compounding, independent blocker:** even if every NFL-specific gap were closed today, GG-203 — the account-wide, ticker-independent Kalshi demo-account order-write fault (`POST /portfolio/events/orders` fails universally) — was still unresolved as of the most recent evidence (T-515, 2026-09-03, two days before this audit). Its root cause is Kalshi-side; no in-repo fix applies, and there is no controllable ETA. A fully-built NFL pipeline could not place a real order through this same path today. This audit does not attempt to re-verify GG-203's current status — that is outside this audit's scope fence (it is not an NFL-specific gap) — but the operator should not read "NFL build finished" as "NFL bet placeable" without a fresh GG-203 check first.

**Earliest realistic date:** not 2026-09-09. The NFL-specific build alone (four sequenced components, one of them explicitly downstream of the other three, at least two independently sized MEDIUM-LARGE/LARGE) is a multi-week build, not a multi-day one — a defensible floor is **3-6 weeks of dedicated focus** (roughly mid-to-late October 2026), assuming no other priority displaces it. That estimate does not include however long GG-203 remains open, since that clock is not controllable from inside this repository.

---

## Seven-step trace

| # | Step | What exists | What is missing | Rough size | Required for T1 pregame only, or also T4? |
|---|---|---|---|---|---|
| 1 | Market discovery | `kalshi_client`'s `series_ticker_for()` is registry-driven (since T-439) and correctly resolves all four NFL series tickers (`KXNFLGAME`/`KXNFLSPREAD`/`KXNFLTOTAL`/`KXNFLTEAMTOTAL`) — confirmed by testing it live, not reading it. The raw Kalshi API confirms all four open/tradeable as of this audit (ADR-0062 §2's 2026-09-01 snapshot is consistent; `KXNFLTEAMTOTAL`'s "unlisted" status noted there has since flipped to listed per T-521's independent live check the same day as this audit). | The parsed-market convenience wrapper that live pipelines actually consume assumes a player-prop payload shape (player name + stat threshold) and has no branch for a team-vs-team moneyline/spread/total shape. An NFL (or MLB game-market) response is silently dropped — no error, no log line — so a caller sees "no markets" indistinguishable from an empty slate. **Registered GG-248 (HIGH).** | MEDIUM (extend one wrapper with a game-market branch; benefits MLB's own 5 unbuilt T1 game-market cells too, not NFL-specific) | **T1 pregame** (also blocks T4 in-play discovery for any game market) |
| 2 | Model input | A generic `TeamStatsStore` exists (`c1_signal_ingestion/team_stats_store.py`, built for NBA, Phase 7/T-075) with temporal-integrity-safe rolling-stat accessors. MLB has its own separate, MLB-specific `mlb_team_stats_store.py`. | Neither is NFL-fit: the generic store's schema derives `pts_allowed = pts_scored - plus_minus`, a basketball-margin quantity NFL box scores don't need (they report points-allowed directly) — an adaptation, not a drop-in reuse. Zero NFL ingestion source exists at all — no script populates any store with NFL team/game data (rolling scoring, rest, home/away, injuries). **Registered GG-247 (HIGH).** | MEDIUM-LARGE (new C1 module + schema decision + historical backfill before any model can be fit) | **T1 pregame** (T4 would need a further, separate live-state ingestion layer on top of this) |
| 3 | Forecast | The C3 model class (LR + Platt scaling, ADR-0004) and the forecaster path around it are sport-agnostic in code — confirmed by reading `game_state_model.py` and the C3 call path earlier this session. HYP-011 (2026-09-03) pre-registers a moneyline LR hypothesis for MLB. | HYP-011 confirms no moneyline LR has been fit for **any** sport, including MLB — the most infrastructure-advanced sport the bot trades. ADR-0004's production model class exists for player-prop targets today, not team-win/moneyline targets, for any sport. NFL additionally has none of HYP-011's assumed feature inputs (an `MLBTeamStatsStore`-equivalent), per Step 2. | MEDIUM (model-fitting work, once Step 2's data exists — this is a research task, not primarily an engineering one, and MLB would go first since its data already exists) | **T1 pregame** |
| 4 | Risk gate | `risk.py::evaluate_forecast()`/`_evaluate_forecast_impl()` — confirmed via full read and grep this session: zero `MarketType`/`CellStatus`/sport-name coupling anywhere in the function. Gated only by the `BOT_C4_ACTIVE` env var, then purely numeric daily-loss (CHECK 1) and drawdown (CHECK 2) checks. | Nothing — this step is fully built and would evaluate an NFL forecast today exactly as it evaluates an MLB one. Not a blocker. | N/A — already done | N/A (already sport-agnostic for both bands) |
| 5 | Execution / stake sizing | `measurement_stake.py` (ADR-0059, T-497/GG-218, read in full this session) already includes all four NFL market types (`nfl_moneyline`, `nfl_spread`, `nfl_game_total`, `nfl_team_total`) in its `T1_GAME_MARKET_TYPES` frozenset, alongside MLB's five. The wrapper's logic (flat $1.00 stake, 10-contract cap, haircut gate) is complete and correct for NFL by design. | The module is wired into nothing. Grep confirms its only importer anywhere in `src`/`scripts` is `scripts/assert_ledger_invariants.py`, an audit tool — no live pipeline calls it, for any of its nine cells. This is a band-wide gap, not NFL-specific: MLB's own five T1 game-market cells are equally unwired. | MEDIUM (wire the wrapper into a live paper-trade caller — MLB first, since NFL has nothing yet to feed it) | **T1 pregame** |
| 6 | Resolution | MLB's resolve script (`run_resolve_mlb.py`, PIPE-05R, cron 06:30 UTC, 793 lines, read in full/grepped this session) uses the MLB Stats API primary + ESPN fallback. `paper_trader.py::settle_position()` implements a generic threshold-crossing settlement pattern. | Neither resolves a moneyline/game-winner outcome. `run_resolve_mlb.py`'s only fetch/resolve function is `fetch_actual_hits()` — a full-file grep for moneyline/game_winner/final_score/resolve functions returns nothing else. `settle_position()`'s pattern (`yes_won = actual_stat >= threshold`) is a threshold crossing, not a binary win/loss branch. A `src`-wide grep confirms zero moneyline-shaped resolution logic exists anywhere, for any sport. **Registered GG-249 (HIGH) — this is the single largest gap found in this audit, and it is not NFL-specific.** | MEDIUM (live final-score data source — ESPN plausibly covers both sports — + a new fetch-outcome function per sport + settle-path glue; MLB's version should be built first as the template) | **T1 pregame** (also required for T4 in-play moneyline settlement) |
| 7 | Scheduling | MLB's cron pipeline has ten distinct stages (PIPE-06/06pre/05/05.5/07[now systemd]/05R/08/05FX/05C + price archiver), fully enumerated this session. As of this audit's live re-check against `origin/main` post-rebase, the price archiver now has an NFL analogue — a concurrent session (T-521) added `KXNFLGAME`/`SPREAD`/`TOTAL`/`TEAMTOTAL` capture windows during this same audit window, registering **GG-245** (already OPEN, not re-registered here). | Every other stage has no NFL analogue: no NFL paper-trade run script (PIPE-05 equivalent), no NFL resolve script (PIPE-05R equivalent), no cron entries for either. This gap is downstream of, and cannot be closed independently of, GG-247/248/249 — a run script has nothing to call without C1 data, working market discovery, or a resolution path. **Registered GG-250 (HIGH).** | LARGE (two new run scripts + cron entries, but genuinely blocked on the three gaps above landing first) | **T1 pregame** (T4 in-play scheduling — sub-minute live polling — is a further, larger, separate build entirely out of this audit's minimum-viable-T1 scope) |

---

## T1-vs-T4 split

Every step above (1, 2, 3, 5, 6, 7) is required just to get a **T1 pregame** NFL moneyline bet placed and eventually resolved. Step 4 (risk gate) is the only step that needs nothing further — it already works for any sport.

**T4 in-play NFL would need everything above, plus, additionally:** a live game-state ingestion layer (score, clock, possession, down/distance — NFL's analogue of MLB's `game_state_model.py` live-batter-state feed), a live Bayesian update path comparable to MLB's T4 execution engine, and sub-minute-cadence scheduling (systemd, following MLB's PIPE-07 pattern, not cron). None of this was built or estimated in this audit — it is explicitly out of scope, since the task was to trace the *cheapest* path (T1 pregame), not the full band set. The operator should not read "T1 pregame NFL is buildable in N weeks" as implying T4 NFL is close behind it on the same timeline; T4 is strictly larger.

---

## Every GG registered this session

All four are newly registered (starting at GG-247, the first number free after re-verifying against `origin/main` immediately before writing — GG-245 and GG-246 were already reserved/in use by concurrent sessions T-521 and T-522 at claim-check time, see the Concurrency note below):

- **GG-247** (HIGH) — No NFL C1 ingestion module exists; generic `team_stats_store.py` is basketball-schema-shaped, not directly reusable.
- **GG-248** (HIGH) — `kalshi_client.py`'s parsed-market wrapper is player-prop-shaped; NFL (and other non-prop) market types are silently dropped despite registry resolving correctly.
- **GG-249** (HIGH) — No moneyline/game-winner resolution logic exists anywhere in `src/`, for any sport including MLB.
- **GG-250** (HIGH) — No NFL T1 paper-trade run script, resolution run script, or cron entries exist (distinct from GG-245's price-archiver-only fix).

Not re-registered (already tracked, cited for context only):
- **GG-245** (OPEN) — NFL price-archiver gap; found missing at this audit's Step 7 trace time, independently and concurrently fixed by T-521 during this same audit window. See Concurrency note below.
- **GG-226** (OPEN) — no namespace-valid `ExecutionBand` member for NFL/NHL T4 sub-bands; a concurrent session (T-522) has claimed this exact scaffolding work as of this audit but had not yet reported a merge/closure at the time of this trace. Relevant to T4 NFL only, not this audit's T1 scope.
- **GG-203** (PARTIALLY RESOLVED as of last check, T-515/2026-09-03) — the account-wide Kalshi order-write fault cited as the compounding blocker above. Not re-verified in this audit (out of scope — not NFL-specific); the operator should re-check its live status before treating any NFL-specific fix as sufficient on its own.

---

## Concurrency note

Three commits landed on `origin/main` from other sessions during this audit's investigation window: `9a95a24`/`aeb29b8`/`31dd9fc` (T-521, GG-245, NFL price-archiver fix) and a claim row for T-522/GG-246 (ADR-0062 §17.1 ExecutionBand scaffolding, ADR-0056/GG-226-adjacent, claimed but not yet merged as of this audit). This audit's branch was rebased onto the resulting `origin/main` before this document was finalized, so Step 7's table row reflects the corrected, current state (NFL price capture now exists) rather than the stale "zero NFL cron lines" finding this audit's own trace produced before the rebase. New GG numbers in this document were claimed only after a final live re-check against `origin/main` confirmed GG-245/GG-246 were already spoken for.

---

## What this audit did not do

Per the task's explicit constraints: no code was built, scaffolded, or wired; no `kelly_fraction` or `CellStatus` value was touched; no recommendation against NFL as a sport is made or implied — this is a readiness measurement, not a go/no-go on the sport itself. Operator doctrine on NFL expansion stands unchanged by this document.
