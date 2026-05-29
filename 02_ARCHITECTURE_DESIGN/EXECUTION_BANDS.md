# Execution Bands — Time-Horizon Strategy Framework

**Purpose:** Define the five execution time-horizon bands (T1–T5) and their model complexity, execution quality, and Kelly sizing requirements. The authoritative design document for multi-band trading strategy implementation.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-05-29 (initial build — Phase 6 idle period)
**Next review:** On any band activation; on Phase 8 real-time infrastructure scope
**Staleness triggers:** New band activated; Kelly fraction adjusted by ADR; execution SLA changed; new pipeline deployed
**Upstream links:** STRATEGY_OVERVIEW.md (strategy context); PIPELINES_JOBS.md (pipeline registry); METHODOLOGY.md (model classes)
**Downstream links:** execution_bands.py (implementation); PIPELINES_JOBS.md (PIPE-02/05/06/07/08); cron.conf (schedules)
**Decision references:** ADR-0001; ADR-0002; ADR-0004 (Kelly fraction)
**Confidence:** 9/10

---

## Design Principle

Derived from high-frequency trading theory (Jane Street, HRT, Virtu):

> **At the lowest latency, execution quality IS the edge. Model complexity is inversely proportional to time horizon because computation time eats into the edge window.**

Applied to prediction markets:
- **T1 (multi-day):** Full 78-feature ML pipeline — execution timing irrelevant; edge comes from superior probability estimation
- **T3 (pre-tip):** Minimal signal (momentum only) — edge window is minutes; fast execution matters more than model depth
- **T4/T5 (in-play):** No model — pure game-state arithmetic or Bayesian update; sub-second execution IS the edge

The same principle governs Kelly fraction: shorter horizons use simpler, less-calibrated signals, so position sizes are reduced to reflect lower model confidence.

---

## Band Definitions

### T1 — Multi-Day (ACTIVE — PIPE-02)

| Attribute | Value |
|-----------|-------|
| Horizon | 12–48h before game |
| Model | Full LR+Platt, 78 features (31 quant + 47 qual), QS-2026-05-28-002 |
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
| T1 | Multi-day | Full LR+78 feat | 0.25 | 30,000ms | 3600s | Cron | 6 ✅ |
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
| T2 | DS-04 injury data source registered (T-075); FEATURE_VERSION 1.3.0 |
| T3 | Phase 7 entry; no additional data sources required |
| T4 | Phase 8 + real-time infrastructure ADR + DS-02 websocket upgrade |
| T5 | Phase 8 + T4 infrastructure (T5 is an extension of T4 infra) |
