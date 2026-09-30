# Execution Bands — Time-Horizon Strategy Framework

**Purpose:** Define the five execution time-horizon bands (T1–T5) and their model complexity, execution quality, and Kelly sizing requirements. The authoritative design document for multi-band trading strategy implementation.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-07-19 (CLAUDE.md lean-up pass — added the "Live Registry" section below as this document's own current band-status inventory, moved verbatim from CLAUDE.md § "Execution timing (T1–T5 bands)". Prior to this pass, that section told readers to go check CLAUDE.md for the live registry — CLAUDE.md had, over many sessions, become the de facto live registry by default, which is exactly why it had ballooned with decaying state. This document is the correct permanent home for band status; CLAUDE.md now points here instead of the reverse.)
**Last reviewed (prior):** 2026-05-31 (T-106: T2 activation gate corrected — FEATURE_VERSION 1.3.0 removed; gate now requires DS-04 operational + EXP validation. EXP-012 falsified injury signal at current N.)
**Next review:** On any band activation; on Phase 8 real-time infrastructure scope; monthly grounding-docs staleness review (TODO_NEXT.md Standing Items)
**Staleness triggers:** New band activated; Kelly fraction adjusted by ADR; execution SLA changed; new pipeline deployed
**Upstream links:** STRATEGY_OVERVIEW.md (strategy context); PIPELINES_JOBS.md (pipeline registry); METHODOLOGY.md (model classes)
**Downstream links:** execution_bands.py (implementation); PIPELINES_JOBS.md (PIPE-02/05/06/07/08); cron.conf (schedules)
**Decision references:** ADR-0001; ADR-0002; ADR-0004 (Kelly fraction)
**Confidence:** 9/10
**Decisions logged:** true — T1–T5 framework, Kelly fractions per band, and multi-band interaction rules captured in DECISION_LOG.md (2026-05-29 retroactive batch, entries 5/6/7)

---

## ⚠️ Implementation Reality Update (2026-07-02 documentation-remediation pass)

This document is marked CANONICAL and its band definitions/design principle below are left unedited by this pass — they remain the reference for how the system *thinks about* time horizons. But two things the original document could not have anticipated have since happened, and a reader relying on the tables below without this note will draw wrong conclusions:

1. **T4 was actually built as a cron/systemd polling loop (45–90s cycle), not the real-time/websocket architecture this document specifies as T4's infrastructure requirement.** The "Blocked by" row for T4 below (`Real-time C5 rebuild; live game data feed (DS-02 upgrade); kill switch SLA reduction 60s → <5s`) describes a more ambitious build than what shipped. What's actually live: **NBA T4** — `run_t4_live.py`/`t4_live_runner.py`, PIPE-07, deployed and cron-scheduled (dark now only because NBA work is tabled per operator directive, not because it's unbuilt). **MLB T4M-PROJ** — `run_t4_mlb_live.py`, ADR-0023, ACTIVE, systemd-managed (`t4-mlb`). Neither required the websocket upgrade, the sub-5s kill switch, or the "full C5 rebuild" this document lists as blockers — the 45-90s poll interval turned out to be an acceptable substitute for true real-time infrastructure, at least for the current edge thesis. This is worth a governance note (not added here) on whether the original T4 design principle's "sub-second execution IS the edge" framing still describes what was actually built, since a 45-90s poll is not sub-second.
2. **MLB introduced an entirely new T4 sub-band layer this document has no knowledge of.** ADR-0029 (NBA T4 sub-bands, `t4_execution_engine.py`, 10 sub-bands, Phase 8-gated) and ADR-0039 (MLB-native T4 sub-bands — T4M-PROJ/ARITH/FLOW/BOUNDARY/EVENT/LINEUP/PITCHER/STAGED/CORR/EXIT, `t4_mlb_execution_engine.py`) both post-date this document and are not reconcilable with the single flat "T4 — In-Play Bayesian Update" band described below without reading those ADRs directly. Treat the T4 row in every table below as describing the *original design intent*, not the current registry of what's built, active, or blocked — see the **Live Registry** section immediately below for the current inventory.

T1/T2/T3/T5 status below is still substantively accurate (T5 in particular remains genuinely unbuilt for both sports, as originally scoped).

---

## Live Registry — Current Band Status (moved from CLAUDE.md, 2026-07-19)

**This is the authoritative, current inventory of which sub-bands are ACTIVE / BLOCKED / dark, per sport.** It supersedes the band-status table implications elsewhere in this document (those describe original design intent, per the note above). Update this section — not CLAUDE.md — when a band's status changes; CLAUDE.md carries only a one-line pointer here so this doesn't happen twice.

**The bands are not pre-decided time-horizon thresholds. The model computation determines which decision-tree bucket a bet routes to** — see CLAUDE.md § "Execution timing (T1–T5 bands)" for the full architectural framing (this section is state only, not the design philosophy).

NBA and MLB now have separate, non-interchangeable T4 implementations — do not assume one sport's band status describes the other's.

**NBA bands (dark/frozen — tabled per operator directive, not actively worked):**
- **T1:** Night-before baseline — the primary band while NBA was active. 158/30 resolved paper bets, frozen at a negative baseline (GG-034/GG-037-adjudicated).
- **T2:** Same-day with injury overlay — skeleton; requires DS-04 qualitative source.
- **T3:** Pre-tip momentum scan — skeleton.
- **T4 (NBA, PIPE-07):** Built, deployed, cron-scheduled (23:00 UTC daily). Polls ESPN NBA scoreboard + NBA pregame context, ~1,000 bet evaluations per game via 45-second loop. Currently dark (NBA off-season — 0 active games, and tabled per operator directive independent of season). Code: `run_t4_live.py`, `t4_live_runner.py`, `t4_price_cache.py`.
- **T4 sub-bands (ADR-0029 Tier A — NBA-native architecture):** Built (`t4_execution_engine.py`, 10 sub-bands) but Phase 8-gated; NBA work is tabled, so this stays dark regardless of gate status. Do not confuse this file with the MLB T4 engine below — they are architecturally separate modules (GG-061 — an earlier session conflated them and had to be corrected via ADR-0037).

**MLB bands (ACTIVE — the live G6 pool):**
- **T1:** Night-before baseline — ACTIVE, cron-scheduled, the primary source of MLB's resolved paper bets (see MEMORY_BANK.md Current State Snapshot for the live count).
- **T2:** Same-day with injury overlay — cron-active (`run_t2_mlb_sameday.py`).
- **T3:** Pre-game signal scan — cron-active.
- **T4M-PROJ (`run_t4_mlb_live.py`, ADR-0023):** ACTIVE. The flat, single-evaluator MLB T4 engine — polls ESPN MLB scoreboard on a 45s loop, live and cron/systemd-managed on the VPS (`t4-mlb` service).
- **T4M-ARITH / T4M-FLOW (ADR-0039, MLB-native T4 sub-band architecture):** Built and unit-tested (`t4_mlb_execution_engine.py`), registry status `BLOCKED` — each requires its own experiment (EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01) to confirm edge before activation. Code authorization (DS sign-off, Session 109) is not capital authorization — both stay dark until their EXP clears and a Phase 8 Activation Gate + APR is granted. T4M-FLOW additionally has a live-wiring gap (`score_diff` never populated from a live poll) that must be closed before it can evaluate real cycles at all.
- **T4M-BOUNDARY / T4M-EVENT / T4M-LINEUP / T4M-PITCHER / T4M-STAGED / T4M-CORR / T4M-EXIT (ADR-0039 Tier B roster):** Scoping-only. Not authorized for implementation — do not build without a fresh, explicit DS sign-off scoped to the specific sub-band.
- **T5:** Not built, either sport. Future; requires real-time infrastructure.

Before touching any T4 code, confirm in `GOVERNANCE_GAP_LOG.md`/`TODO_NEXT.md` which sport and which specific sub-band you're in — NBA's `t4_execution_engine.py` and MLB's `t4_mlb_execution_engine.py` are separate files with separate registries, separate ADRs, and separate activation status. Conflating them is a recurring, logged failure mode (GG-061).

**High per-game evaluation volume in T4 is a structural consequence of the latency-edge thesis, not a target.** Measured MLB T4 throughput (GG-080/T-235, 2026-07-04, n=2 game-days — re-derive as more days accumulate): 2026-07-02 = 924 rows/game-day, 5.75 bets/game (0.62% fire rate); 2026-07-03 = 464 rows/game-day, 3.67 bets/game (0.79% fire rate). This runs well below the old ~8,600 slots/game theoretical ceiling (superseded — see GG-080), but the architectural point survives: bet sizing, kill switches, and decision routing must be designed per-cycle/per-bet, continuously evaluated, not as a small pre-scheduled batch. See CLAUDE.md Hard Rule 9 and DECISION_LOG.md 2026-07-04.

---

## Design Principle

Derived from high-frequency trading theory (Jane Street, HRT, Virtu):

> **At the lowest latency, execution quality IS the edge. Model complexity is inversely proportional to time horizon because computation time eats into the edge window.**

Applied to prediction markets:
- **T1 (multi-day):** Deepest tree of the bands (LR+Platt; MLB player-prop model measured at 18 features, 0 qualitative — see T-597 D4; the earlier "78-feature" figure was an NBA-era design number) — execution timing irrelevant; edge comes from superior probability estimation
- **T3 (pre-tip):** Minimal signal (momentum only) — edge window is minutes; fast execution matters more than model depth
- **T4/T5 (in-play):** No model — pure game-state arithmetic or Bayesian update; sub-second execution IS the edge

The same principle governs Kelly fraction: shorter horizons use simpler, less-calibrated signals, so position sizes are reduced to reflect lower model confidence.

### Amendment — 2026-09-30 (operator restatement; canonical text in ADR-0068)

The principle above is correct and is retained. Three clauses were missing, and their absence let a
misfiled cell run for an entire MLB season without contradiction.

**A. Shallowness must be paid for in measured speed.** The text above licenses a stripped tree wherever
"sub-second execution IS the edge" — but never required that the sub-second execution be *demonstrated*.
The T4 pipeline has never been sub-second: it polls on a ~60s cycle, and P3 of
`BAND_ASSIGNMENT_FRAMEWORK.md` already records the T5 kill-switch SLA as 60s, "12x too slow." The tree was
stripped on a latency premise the architecture did not satisfy. **T-569 tested that premise directly and
returned NOT SUPPORTED (current feature set).**

> **The rule, stated as a test: a band's decision-tree depth must be justified by its decision horizon and
> paid for by a measured execution advantage. A cell that is shallow without being fast is misfiled, not
> optimized.**

The corollary matters as much as the rule: the remedy for a misfiled cell is **not more speed**. At a 60s
cadence there is ample time to condition on pitcher, park, lineup, score state and leverage. T4's headroom
is in **structure**, and the stripping there was inherited rather than chosen.

**B. Horizon is not throughput.** Evaluation rate is how often the system looks; horizon is how fast the
underlying information changes. T4S11 fires thousands of evaluations per game, but the markets it prices
move on discrete events (at-bats) that arrive minutes apart. High poll rate, long horizon. **Band membership
keys on decision horizon, never on evaluation count.**

**C. Build sequencing — widest horizon first.** The matchup/sport/player/team/external/qualitative feature
architecture is piped in at pre-game, where it exists, is stable, and has a context window wide enough to
evaluate. Pre-game also accrues evidence at a countable rate: markets resolve once per game and are roughly
independent across games, where in-play rows are serially correlated within a game and inflate n without
inflating information (this is why the T4 A/B harness built in T-583 clusters by game). Establish the deep
tree at the widest horizon, then carry that granularity inward toward the shorter bands. The north star is
that granularity at **every** arm.

---

## Band Definitions

### T1 — Multi-Day (ACTIVE — PIPE-02)

| Attribute | Value |
|-----------|-------|
| Horizon | 12–48h before game |
| Model | LR+Platt. **MLB (measured 2026-09-30): 18 features, 0 qualitative** (`models/mlb_v1_model_meta.json`, `feature_count: 18`). The NBA-era design figure was 78 (31 quant + 47 qual, QS-2026-05-28-002) — not true of the MLB T1 model |
| Signal | Season-trend mispricing; qualitative role classification |
| Kelly fraction | 0.25 (quarter-Kelly, ADR-0004) |
| Execution SLA | 3600s (1h) — execution timing irrelevant |
| Max compute | 30,000ms — full pipeline; batched |
| Pipeline | PIPE-02 — cron 21:30 UTC daily |
| Phase | Phase 6 ACTIVE |
| Confidence | 7/10 (backtested; paper trading in progress) |

T1 is the primary revenue strategy (Strategy A). All other bands are supplements or enhancements.

---

### T2 — Same-Day Injury/Lineup Overlay (SKELETON — PIPE-05)

| Attribute | Value |
|-----------|-------|
| Horizon | 4–8h before tip-off |
| Model | T1 output + injury/lineup adjustment overlay (DS-04 required — T-075) |
| Signal | Confirmed absences → usage share redistribution; load management confirmations |
| Kelly fraction | 0.20 (reduced: injury data adds uncertainty to T1 estimates) |
| Execution SLA | 1800s (30 min) — relaxed; 4h before tip |
| Max compute | 5,000ms — fast overlay on cached T1 |
| Pipeline | PIPE-05 — cron 17:00 UTC on game days |
| Phase | Phase 7 (requires injury data source T-075) |
| Status | Skeleton operational — injury overlay stub (TODO: DS-04) |

**Injury adjustment logic (target):**
```
teammate_out_flag = True → usage_boost = +0.04 (4% scoring probability increase)
player_questionable    → kelly_fraction = 0.05 (minimal sizing)
player_out             → remove from T2 forecasts entirely
```

---

### T3 — Pre-Tip Momentum Scan (ACTIVE SKELETON — PIPE-06)

| Attribute | Value |
|-----------|-------|
| Horizon | 15–60 min before tip-off |
| Model | No historical data — reads cached T1 output + live price comparison only |
| Signal | Price drift vs. T1 forecast-time price: CONFIRM / FADE / NEUTRAL |
| Kelly fraction | 0.10 (half of T1 — thinner signal, confirmation only) |
| Execution SLA | 300s (5 min) — window closes at tip-off |
| Max compute | 500ms — reads JSON + live API only |
| Pipeline | PIPE-06 — cron `*/15 21-23 * * *` |
| Phase | Phase 7 (runs on current infrastructure — no new data sources required) |

**Momentum signal logic:**
```
price_drift = current_mid - t1_forecast_mid

CONFIRM:  drift ≥ +0.025 in model's direction → edge × 1.15
FADE:     drift ≥ +0.025 against model        → edge × 0.75
NEUTRAL:  |drift| < 0.025                      → edge unchanged
```

T3 does not require real-time infrastructure. It reads the T1 report file and fetches current Kalshi prices via VenueRouter — both are available on the current VPS cron setup.

---

### T4 — In-Play Bayesian Update (BLOCKED — PIPE-07)

| Attribute | Value |
|-----------|-------|
| Horizon | Seconds to minutes during live game |
| Model | Bayesian update: P(X≥threshold \| current_pts, time_remaining, pace) |
| Signal | Live game-state: score progression, time remaining, pace of play |
| Kelly fraction | 0.05 (minimal — no historical calibration on live model) |
| Execution SLA | 5s — in-play window is seconds |
| Max compute | 50ms — must be faster than market update latency |
| Pipeline | PIPE-07 — event-driven (not cron) |
| Phase | Phase 8+ |
| Blocked by | Real-time C5 rebuild; live game data feed (DS-02 upgrade); kill switch SLA reduction 60s → <5s |

**Bayesian game-state model (design):**
```
λ_remaining = expected_pts_remaining(pace, time_remaining, pts_so_far)
P(X≥threshold | game_state) = 1 - CDF_Poisson(threshold - 1 - pts_so_far, λ_remaining)
```

---

### T5 — Late-Game Arithmetic (BLOCKED — PIPE-08)

| Attribute | Value |
|-----------|-------|
| Horizon | Final 2–5 minutes of game |
| Model | Arithmetic certainty: pts_needed, pace, time_remaining |
| Signal | Player at 23 pts with 3 min left on a ≥25 line — near-certain outcome |
| Kelly fraction | 0.15 (higher than T4 — near-certainty justifies larger size) |
| Execution SLA | 1s — final minutes; sub-second preferred |
| Max compute | 5ms — pure arithmetic; no model inference |
| Pipeline | PIPE-08 — event-driven |
| Phase | Phase 8+ |
| Blocked by | Same as T4; requires T4 infrastructure first |

T5 Kelly fraction (0.15) is intentionally higher than T4 (0.05) — when arithmetic certainty is high, the simplified model is more reliable, not less.

---

## Band Comparison Matrix

| Band | Horizon | Model | Kelly | Compute | Exec SLA | Infra | Phase |
|------|---------|-------|-------|---------|----------|-------|-------|
| T1 | Multi-day | LR+Platt, 18 feat (MLB, measured) | 0.25 | 30,000ms | 3600s | Cron | 6 ✅ |
| T2 | Same-day | Injury overlay | 0.20 | 5,000ms | 1800s | Cron | 7 (T-075) |
| T3 | Pre-tip | Momentum signal | 0.10 | 500ms | 300s | Cron | 7 ✅ |
| T4 | In-play | Bayesian | 0.05 | 50ms | 5s | Real-time | 8 |
| T5 | Late-game | Arithmetic | 0.15 | 5ms | 1s | Real-time | 8 |

---

## Cron Schedule (T1–T3 only)

```
# T1 — PIPE-02 (pre-game inference)
30 21 * * * cd $PROJ && ... $PYTHON run_pregame.py >> logs/pregame_cron.log 2>&1

# T1 late games — PIPE-02 second run
30 1  * * * cd $PROJ && ... $PYTHON run_paper_trade.py >> logs/paper_cron.log 2>&1

# T2 — PIPE-05 (same-day injury overlay) — activate when DS-04 ready (T-075)
# 0 17 * * * cd $PROJ && ... $PYTHON run_t2_sameday.py >> logs/t2_cron.log 2>&1

# T3 — PIPE-06 (pre-tip momentum scan)
# */15 21-23 * * * cd $PROJ && ... $PYTHON run_t3_pretip.py >> logs/t3_cron.log 2>&1
```

T2 and T3 cron lines are commented out until Phase 7 activation. Add to VPS cron.conf at activation.

---

## Infrastructure Requirements by Band

| Band | Data feed | C5 capability | Kill switch SLA | Additional |
|------|-----------|--------------|-----------------|-----------|
| T1 | nba_api (batch) | Read-only | 60s current | None |
| T2 | nba_api + DS-04 injury | Read-only | 60s | Injury data source (T-075) |
| T3 | VenueRouter (live prices) | Read-only | 60s | None — uses current infra |
| T4 | Real-time game feed | Write + sub-5s | <5s | Full C5 rebuild required |
| T5 | Real-time game feed | Write + sub-1s | <5s | Same as T4 |

---

## Activation Gates

| Band | Gate condition |
|------|---------------|
| T1 | ✅ G6 (ADR-0005) for live capital; paper already running |
| T2 | DS-04 operational (T-075 + commissioning); dedicated EXP confirming injury overlay Brier improvement ≥ 0.001 at N ≥ 100 (EXP-012 falsified this signal at current N — scale constraint applies) |
| T3 | Phase 7 entry; no additional data sources required |
| T4 | Phase 8 + real-time infrastructure ADR + DS-02 websocket upgrade |
| T5 | Phase 8 + T4 infrastructure (T5 is an extension of T4 infra) |

---

## Arbitrage Strategies by Band

Arb strategies (C, D, E) map differently to execution bands than model-edge strategies. The governing principle remains identical — shorter horizon = shorter decision tree — but arb has a critical structural distinction: **detection band ≠ execution band.**

The expensive computation (market scan, OU estimation, venue comparison) happens at T1/T2. Execution at T3/T4 is pure lookup + fire. Without T1/T2 pre-computation, arb strategies cannot meet T3/T4 SLAs.

Full decision tree specification: `02_ARCHITECTURE_DESIGN/ARB_FRAMEWORK.md`

### Arb Strategy Band Matrix

| Band | Strategy C (Complement Lock) | Strategy D (Stat Arb) | Strategy E (Line Shopping) |
|------|------------------------------|----------------------|---------------------------|
| T1 | **Detection:** Full market scan → build lock opportunity table | **Detection:** Full OU estimation → rank correlated pairs | **Cache:** Full venue comparison → build routing table |
| T2 | **Refresh:** Re-validate top-N candidates; update ask prices | **Update:** Fetch live prices → recompute z-scores (no OU re-est.) | **Refresh:** Re-query venues + injury adjustment → update routing table |
| T3 | **Execute:** Verify lock holds (1 API call) → submit both legs | **Execute:** Check z-score in entry zone → submit if valid | **Route:** Query all venues live → normalize → route to best price |
| T4 | **Execute:** Lookup pre-staged flag → fire pre-built order pair | Not applicable (OU reversion > game window) | **Route:** Lookup pre-cached routing_table[market_id] |
| T5 | Not applicable (near-deterministic settlement) | Not applicable | Lookup pre-cached routing_table[market_id] |

### Decision Tree Depth — Arb vs. Strategy A

```
                T1          T2          T3          T4          T5
Strategy A:   [FULL]     [overlay]  [momentum]  [Bayesian]  [arithmetic]
               18 feat (MLB) cached+    1 signal    1 update    2 ops

Strategy C:  [SCAN]     [REFRESH]  [VERIFY+FIRE] [LOOKUP]    N/A
              all mkt     top-N      1 API+1 op    1 op

Strategy D:  [ESTIMATE]  [UPDATE]  [CHECK+FIRE]   N/A        N/A
              OU params    z-score   cached+1 op

Strategy E:  [COMPARE]  [REFRESH]  [LIVE ROUTE]  [CACHED]  [CACHED]
              all venues  inj adj    N API calls   1 lookup   1 lookup
```

The arb strategies share the band infrastructure (pipelines, VPS cron, C5) with Strategy A but require additional modules: `ComplementLockScanner`, `StatArbScanner`, `LineShoppingRouter`, and `ArbOpportunityLog`. These are Phase 7 builds, post-G6.

### Arb Activation Gates by Band

| Strategy | Band | Phase | Primary blocker |
|----------|------|-------|----------------|
| E | T1/T2/T3 | 7 | Polymarket API (T-077); VenueRouter multi-venue |
| E | T4 | 8 | Real-time C5 rebuild |
| C | T1/T2 scan | 7 | APR-0010 (DS decision) |
| C | T3/T4 execute | 7/8 | Write-capable C5 (ACC-0002 upgrade); APR-0010 |
| D | T1/T2 | 8 | DS-02 price history (≥2 seasons per pair); new ADR |
| D | T3 | 8 | DS-02 live feed |

---

## Band Assignment Protocol

**Full specification:** `02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md`

**Registry:** `src/prediction_market_bot/execution_bands.py` — `BAND_REGISTRY` singleton. All strategies A–K must be registered in `BAND_REGISTRY` before deployment. Unregistered strategies cannot be activated.

### Five-Criterion Test (C1–C5)

Before assigning a strategy to a band, all five criteria must pass:

| Criterion | Test | Fail condition |
|-----------|------|---------------|
| **C1 — Compute fit** | Can the strategy's full decision tree complete within the band's `max_compute_ms`? | Strategy computation exceeds band budget at P90 latency |
| **C2 — SLA achievable** | Can a bet be submitted before the execution SLA expires, given venue API latency? | `venue_api_p90_ms + compute_ms > sla_ms` for target band |
| **C3 — Signal exists** | Does the strategy have a validated signal for this band's time horizon? | No signal or signal is untested at this horizon |
| **C4 — Evidence validated** | Has the band assignment been confirmed by a registered experiment (EXP-NNN)? | No EXP result; hypothesis unvalidated |
| **C5 — Depth justified by horizon** (ADR-0068) | Is the decision-tree depth consistent with the band's decision horizon, and — where the tree is stripped — is the execution advantage that licenses the stripping **measured**, not assumed? | Tree is shallow relative to the horizon with no measured latency advantage. The cell is misfiled. |

A strategy passes C1–C2 (feasibility) before C3–C4 (evidence). A strategy may be SKELETON if it passes C1–C2 but is pending C3–C4 evidence.

### Band Status Semantics

| Status | Meaning | Execution behavior |
|--------|---------|-------------------|
| **ACTIVE** | C1–C5 all pass (C5 per ADR-0068, PROPOSED); validated by EXP | Eligible to drive bet sizing |
| **SKELETON** | C1–C2 pass; C3–C4 pending evidence | Signals logged; bet sizing blocked |
| **BLOCKED** | C1–C2 fail OR gate condition unmet | No execution; no signals |

`band_status` is machine-enforced, not a documentation label. `BandRegistry.validate()` runs at bot startup and logs violations as WARNINGS.

### Adding a New Strategy

1. Create a `StrategyBandSpec` dataclass instance with all 11 required fields.
2. Register it via `BAND_REGISTRY.register(spec)`.
3. Assign `band_status = "SKELETON"` initially (C3–C4 evidence pending).
4. Run the 4-criterion test; document in BAND_ASSIGNMENT_FRAMEWORK.md.
5. Write a DECISION_LOG entry for the assignment decision.
6. Promote to `ACTIVE` only after a registered EXP confirms signal quality.
7. Promotion from SKELETON→ACTIVE requires a DECISION_LOG entry + CHANGE_CONTROL Class A review.

### Band Change Governance

| Change | Documentation required |
|--------|----------------------|
| New strategy registered (any status) | DECISION_LOG entry |
| SKELETON → ACTIVE promotion | DECISION_LOG entry + DS sign-off (CHANGE_CONTROL Class A) |
| SKELETON → BLOCKED demotion | DECISION_LOG entry + DS sign-off |
| Band reassignment (e.g., T1 → T2) | DECISION_LOG entry + DS sign-off + may require new ADR |
| ACTIVE → BLOCKED (evidence invalidated) | DECISION_LOG entry + DS sign-off + ADR if strategy was live capital |

See `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` — Band Assignment Changes section.
