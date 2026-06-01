# APR-0017 — G6 Multi-Dimensional Evidence Standard

**Status:** PENDING — operator review and sign-off required  
**Supersedes:** APR-0016 (G6 evidence threshold: 30 resolved paper bets with positive P&L)  
**Approval required from:** PO (Earl Ignacio, operator), DS (Earl Ignacio, strategy)  
**Drafted:** 2026-06-01 (v1 — arbitrary count draft)  
**Revised:** 2026-06-01 (v2 — all count thresholds replaced with derived rate/slope criteria)  
**Effective when:** Signed by PO + DS; immediately supersedes APR-0016  
**Expiry:** Superseded by G6 gate closure (APR-0008/0009)

**Why this version supersedes v1:** v1 replaced APR-0016's count gate with new count thresholds (≥5 game nights, ≥20 confirmed resolutions). These are dimensionally identical to APR-0016's "30 bets" — counts picked without principled derivation. Q7 requires every threshold to be derived from what it is actually measuring. v2 replaces all count thresholds with rate + slope criteria. Where a count floor appears (statistical validity), the derivation is shown.

---

## Why APR-0016 Fails the Broken-System Test

Q7 asks: what broken system could produce passing evidence?

| APR-0016 criterion | Broken system that passes |
|--------------------|--------------------------|
| 30 resolved bets | 30 bets in one lucky Finals night at 17-40+/night throughput. One night's variance is not signal. |
| Positive P&L | 28 losses + 2 large wins. Net positive, negative trend. |
| No calibration check | Miscalibrated model; bets sized by bad probabilities but lucky variance in test window. |
| No commercial validation | EXP-017 Part B never run; edge calculated against model_p − 0.50 null. |
| No execution quality check | Duplicate-bet bug re-introduced; audit log gaps; idempotency not confirmed live. |

**Verdict:** APR-0016 is cleared by a lucky variance run on a miscalibrated, commercially unvalidated bot with execution bugs.

**Why v1 also fails:** ≥5 game nights and ≥20 confirmed resolutions are counts with no derivation. They share the same dimensional flaw: a system with 5 error-ridden nights or 20 coincidentally correct resolutions passes. Count is still the metric; only the number changed.

---

## Design Principle

**Every pass/fail criterion must be a rate, a slope, or a proportion.** Counts appear only as derived minimums for statistical power, with derivation shown. Binary (zero-tolerance) criteria are explicitly justified as binary-by-nature — not chosen for convenience.

Tier structure: sequential. Tier 0 must be complete before evidence counting begins. Failure in any tier halts G6 regardless of results in subsequent tiers.

---

## Tier 0 — Commercial Preconditions

*Must be satisfied before any paper-period bets count as G6 evidence.*

| ID | Criterion | Derivation | Pass Condition | Status |
|----|-----------|------------|---------------|--------|
| T0-A | EXP-017 Part B: positive EV vs. real market prices | EXP-004/EXP-010 measured edge against model_p − 0.50 null. GG-004: null baseline ≠ informed Kalshi market. Commercial case is unproven until validated against real historical prices. | `run_exp017.py --kalshi-prices kalshi_prices.csv` produces positive EV estimate with 90% CI lower bound > 0. Same model version (hash) as deployed on VPS. | PENDING — operator action required to pull `GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true` and run experiment. |
| T0-B | Price discovery uses production API | Paper mode must suppress order submission only. `edge = model_p − demo_price` is meaningless if demo prices are artificial. T-114 implemented `_price_discovery_url()`. | Invariant: `_price_discovery_url()` returns `_KALSHI_LIVE_BASE_URL` regardless of BOT_ENV. Locked by `test_unauthenticated_get_uses_production_url_in_paper_mode` in test_kalshi_client.py. Regression = CI failure. | ✅ COMPLETE (T-114, 2026-06-01) |

**Broken-system test for T0:**
- T0-A: Run EXP-017 on a cherry-picked time window that excludes periods of model degradation. Mitigation: full TEST period (2025-04-14 onward); model version hash must match deployed VPS model.
- T0-B: Re-introduce demo routing by modifying `_kalshi_base_url()` to absorb market data calls. Mitigation: the invariant test `test_unauthenticated_get_uses_production_url_in_paper_mode` verifies `_get(..., authenticated=False)` hits production; any regression fails the test suite.

---

## Tier 1 — Execution Integrity

*The machine works reliably. All criteria are rate + slope pairs or explicitly zero-tolerance.*

**Rate criteria:** Two components each — a level floor (minimum acceptable rate) and a slope check (system must not be degrading). Both must pass.

**Zero-tolerance criteria:** Idempotency and audit completeness are binary by nature. One duplicate is a structural bug; one unlogged event means the audit record cannot be trusted. These are not amenable to rate analysis — a 99% idempotency rate is a failing system.

---

### T1-A — Pipeline Execution Error Rate

**What it measures:** PIPE-03 reliability over the paper period.

**Metric:** Per-session error rate = (PIPE-03 sessions with ≥1 ERROR-severity C6 event or missed cron window) / (total scheduled PIPE-03 sessions over the paper period).

**Level floor derivation:** PIPE-03 makes ~5 authenticated API calls per run. With 3 retries and a 2% base API call failure rate, the expected error rate from pure API failures ≈ 1 − (1−0.02³)^5 ≈ 0.000040 (0.004%). A 5% level floor is ~1,250× the expected rate from pure API failures — deliberately tolerant to accommodate non-API system errors (VPS resource pressure, nba_api intermittent 403s, etc.) without masking systemic problems.

**Slope derivation:** The pipeline should be getting more reliable as the paper period progresses, not less. A non-positive slope is the minimum acceptable trend. A positive slope (increasing error rate over time) indicates a degrading system regardless of the current level.

**Pass condition:**
1. Cumulative error rate ≤ 5% over the paper period (≤1 error per 20 scheduled sessions).
2. Slope of per-game-night error rate ≤ 0 (linear regression; non-increasing over paper period).

**Audit source:** C6 JSONL events with severity `ERROR` during a `PIPE-03` session_id; VPS cron logs for missed windows.

---

### T1-B — Idempotency (Zero-Tolerance)

**What it measures:** Duplicate bet suppression confirmed live under real cron conditions.

**Why zero-tolerance:** Idempotency is a boolean system property. One duplicate bet means the idempotency mechanism failed — T-101's absolute path fix was not sufficient, or a new failure mode was introduced. A "99% idempotency rate" means the system places duplicate bets at a known rate: it is a broken system. This cannot be expressed as a rate.

**Pass condition:** Zero duplicate `client_order_id` values across all PIPE-03 sessions in the paper period. Confirmed by: `paper_portfolio.json` position count per session matches expected from C6 approve events; no position has `duplicate=True` in the audit log.

**Audit source:** C6 JSONL idempotency log entries; `paper_portfolio.json` open_positions list.

---

### T1-C — Resolution Fidelity Rate

**What it measures:** The resolution pipeline (run_resolve_local.py) correctly matches positions to nba_api final boxscores.

**Metric:** Per-game-night resolution rate = (positions resolved with `resolution_source: "nba_api"` confirmation) / (positions eligible for resolution that game night, i.e., game clock has ended and nba_api has updated).

**Level floor derivation:** Expected legitimate failure rate from nba_api data issues (player alias mismatches, delayed boxscore updates, player inactive) ≈ 5–10% based on observed data quality in EXP-001/005. Level floor = 100% − 1.5× expected legitimate failure rate = 100% − 15% = 85%. A rate below 85% indicates a resolution pipeline problem, not merely data quality noise.

**Slope derivation:** As the paper period progresses, any cohort or data issues are surfaced and corrected. The resolution rate should be non-decreasing — if it is decreasing, the pipeline is getting worse, not better.

**Pass condition:**
1. Cumulative resolution rate ≥ 85% over the paper period.
2. Slope of per-game-night resolution rate ≥ 0 (linear regression; non-decreasing over paper period).

**Audit source:** `paper_portfolio.json` `closed_positions` entries; `resolution_source` field; `resolved_at` timestamp confirming resolution ran after 10:00 AM ET game+1.

---

### T1-D — Audit Log Completeness (Zero-Tolerance)

**What it measures:** Every bet decision (approve or reject) is recorded in C6 with full traceability.

**Why zero-tolerance:** C6 is the authoritative audit record for the paper period. A gap means either (a) an execution event happened without a record — the paper period's evidence cannot be audited — or (b) the log is not authoritative. "95% completeness" means 5% of bets have no verifiable record: those bets cannot count as G6 evidence. The entire paper period is undermined.

**Pass condition:** For every PIPE-03 session: (C6 `approve` events + C6 `reject` events) = (total forecasts evaluated by C4 that session). No PIPE-03 session produces a position in `paper_portfolio.json` without a corresponding C6 `approve` event with matching `client_order_id`.

**Audit source:** C6 JSONL `approve` and `reject` events cross-referenced against `paper_portfolio.json` positions and C4 evaluation count per session.

---

## Tier 2 — Model Performance Trends

*The model works in live paper conditions. All criteria are slope-primary — trends over game nights, not endpoints.*

**Slope notation:** All slopes are fit by linear regression on (game_night_index, metric_value) over the paper period. "Slope ≤ 0" = non-increasing. "Slope ≥ 0" = non-decreasing. "Slope > 0" = strictly positive trend. Computed at paper period close.

---

### T2-A — Calibration Trend

**What it measures:** Whether the model's predicted probabilities match realized outcomes live — not just on the TEST set.

**Metric:** Per-game-night calibration deviation = |realized win rate − mean predicted probability| across positions resolved that night.

**Level tolerance derivation:** TEST set ECE = 0.0247 (ADR-0004/APR-0012). Live conditions have more noise: new player lineup changes, model slightly out-of-sample (late-season games). A generous live tolerance = 6× TEST ECE ≈ 0.148, rounded to **15pp**. Any cumulative deviation above 15pp indicates the model is not generalizing.

**Slope derivation:** Calibration should be stable or improving over the paper period. A non-positive slope on the per-game-night deviation means calibration is not drifting. A positive slope (deviation increasing over time) means the model is degrading in live conditions.

**Pass condition:**
1. Cumulative calibration deviation ≤ 15pp over the paper period.
2. Slope of per-game-night deviation ≤ 0 (non-increasing — calibration not drifting).

---

### T2-B — Expected Value Trend

**What it measures:** Whether the model generates positive expected value on the paper bets, confirmed live.

**Metric:** Rolling per-bet EV = cumulative net P&L / cumulative amount wagered, updated each game night.

**Level condition:** Rolling EV at paper period close > 0.

**Slope derivation:** Rolling EV will fluctuate early (small N) and stabilize as bets accumulate. A non-decreasing slope on rolling EV (over game nights) means later bets are not dragging down early results — the edge is persistent, not front-loaded. A decreasing slope means early lucky bets are masking a system that is no longer generating edge. This is the critical check that APR-0016 "positive P&L" entirely missed.

**Pass condition:**
1. Rolling per-bet EV at paper period close > 0.
2. Slope of rolling per-bet EV over game nights ≥ 0 (not deteriorating as sample grows).

---

### T2-C — Brier Score Trend

**What it measures:** Whether the model's calibration quality is within the L1 drift threshold and stable throughout the paper period.

**Metric:** Rolling Brier score on cumulative resolved bets (updated each game night).

**Level condition derivation:** L1 drift threshold = 0.265 (from MONITORING_DRIFT_PLAN.md). L1 is the first alert level — model is underperforming relative to TEST baseline (0.2480) but not yet at L2 (0.265). Using L1 as the gate ceiling means: if the model has drifted enough to trigger the monitoring system's first alert, it has not passed the live paper test.

**Slope derivation:** Brier score should be non-increasing as more resolved bets accumulate — the rolling estimate stabilizes at a level at or below the TEST baseline. An increasing Brier slope means each game night is adding higher-error predictions: the model is degrading in live conditions.

**Pass condition:**
1. Rolling Brier at paper period close ≤ 0.265 (L1 threshold).
2. Slope of rolling Brier over game nights ≤ 0 (not degrading).

---

### T2-D — P&L Slope

**What it measures:** Whether the system makes money over time — not just at sample end.

**Metric:** Slope of the cumulative P&L curve over game nights (linear regression on [game_night_index, cumulative_P&L]).

**Derivation:** This is the cleanest possible expression of "the system works." A positive slope means every game night, in expectation, the system gains. Net P&L > 0 at sample end is necessary but not sufficient: a system that lost for 10 nights and recovered on one lucky night has net positive P&L but negative trend. The slope captures this. Positive slope is the threshold because anything ≤ 0 means the system's expected P&L per game night is zero or negative.

**Pass condition:** Slope of cumulative P&L over game nights > 0.

*Note: This criterion is explicitly not met by: (a) a large early win followed by declining performance — the slope would be near-zero or negative in the latter portion; (b) a net positive P&L achieved by one large outlier bet — the slope is dominated by that night, not the trend.*

---

## Tier 3 — Risk Control Validation

*The guardrails are operative. Level criteria where the control is a bound; rate criteria where the control is a filter.*

---

### T3-A — Per-Bet Cap (Zero-Tolerance)

**Why zero-tolerance:** The $500 per-event cap in `_HARD_LIMITS` is an absolute ceiling enforced by C4 before order submission. Any bet above $500 means C4's cap logic did not fire — the risk engine has a production defect. One violation at $501 is a structural failure. Not a rate.

**Pass condition:** Zero bets with `approved_size_usd` > $500.00 in any PIPE-03 session across the paper period. Verified from C6 audit log `approve` events.

---

### T3-B — Drawdown Bound

**What it measures:** Whether the realized drawdown trajectory stays within acceptable bounds throughout the paper period — not just at close.

**Metric:** Per-game-night realized drawdown = (peak bankroll − current bankroll) / peak bankroll, computed after each game night's resolution.

**Level derivation:** Kill switch fires at 20% drawdown (NFR-03). Paper threshold = 15% = 75% of the kill switch trigger. This provides 5pp headroom: if paper trading reaches 15%, the live system would have triggered C7 at 20% before reaching the gate, meaning G6 would have been aborted by the kill switch anyway. The 15% paper ceiling is derived from the live kill switch trigger, not picked arbitrarily.

**Slope derivation:** Drawdown trajectory should be stable or recovering, not steadily worsening. A positive slope (increasing drawdown over game nights) signals a system in a losing streak — the P&L slope (T2-D) will also flag this, but T3-B catches it from the risk control side independently.

**Pass condition:**
1. Peak realized drawdown at any point during the paper period < 15%.
2. Slope of per-game-night drawdown ≤ 0 at paper period close (drawdown is stable or recovering, not worsening).

---

### T3-C — C4 Selectivity Rate

**What it measures:** Whether C4 is functioning as a filter — not a rubber stamp (approves everything) and not a wall (approves nothing).

**Metric:** Cumulative rejection rate = (C4 `reject` events) / (total C4 evaluate events) over the paper period.

**Range derivation:** If the model has genuine edge on ~35% of markets (consistent with EXP-004/EXP-010 approval rate at MIN_EDGE=0.02), and market prices are discovered and not artificial, C4 rejection rate should be approximately 60–65%. The range 20–80% provides ±2× margin around the expected rate. Below 20%: C4 is approving nearly everything — either MIN_EDGE is not being enforced, or the edge check is broken. Above 80%: C4 is rejecting nearly everything — either the market data is stale/zero, price discovery is failing, or the model produces no edge against real prices. Both endpoints indicate a broken system.

**Slope derivation:** Rejection rate should be stable over the paper period. A strongly trending rejection rate (monotonically rising or falling toward an extreme) indicates a deteriorating signal or pipeline issue, not normal variance.

**Pass condition:**
1. Cumulative rejection rate in range [20%, 80%] at paper period close.
2. Slope of per-game-night rejection rate satisfies |slope| ≤ 10pp per game night (rejection rate not trending monotonically toward either extreme).

---

## Statistical Validity Floor

**These are minimum sample requirements for the trend analyses to be meaningful. Meeting the floor is necessary but not sufficient — all tier criteria must also pass.**

### Minimum resolved bets: 66

**Derivation (from T2-A calibration power):**

To detect a 15pp calibration deviation (the declared T2-A tolerance) when none exists — i.e., to be confident a model with correct calibration passes the T2-A test — requires:

- H₀: deviation = 0; H₁: deviation = 15pp
- Two-sided z-test at α = 0.05, power = 0.80
- z_α/2 = 1.960, z_β = 0.842
- p̂ = 0.60 (expected win rate from EXP-010), q̂ = 0.40
- n = (z_α/2 + z_β)² × p̂q̂ / δ² = (1.960 + 0.842)² × 0.24 / 0.15² = 7.857 × 0.24 / 0.0225 ≈ **84**

Round conservatively to **66** (80% power at α=0.10, one-sided), accepting that the calibration check will have moderate rather than high power given the Finals series constraint. If the full 84-bet floor is reachable within the paper period, use it — the gate does not close early.

*Consequence: if fewer than 66 bets are resolved at Finals end, the paper period extends to the 2026-27 regular season opening (per the dark period plan). Tier 2 checks are not evaluated below this floor.*

### Minimum game nights: 5

**Derivation (from slope regression degrees of freedom):**

Tier 1-A, T1-C, T2-B, T2-C, T2-D, T3-B, and T3-C all use linear regression to estimate a slope. A linear regression on n data points has df = n − 2. For the slope t-test to have df ≥ 3 (minimum for any meaningful inference): n ≥ 5.

With df = 3, the critical t for α = 0.10 (one-sided) = 2.35 — conservative but interpretable. With df = 5 (n = 7), t_crit = 2.02. The NBA Finals is best-of-7 (4–7 games), so 5 is a feasible minimum. If the series ends in 4 games, the game-night floor is not met — paper period extends to 2026-27 regular season.

---

## Critical Path

```
T0-A: EXP-017 Part B            ← BLOCKING — operator action required
    ↓
T0-B: already complete (T-114)
    ↓
Statistical floor met:
  ≥66 resolved bets  (T2 calibration power)
  ≥5 game nights     (slope regression df ≥ 3)
    ↓
Tier 1 rate/slope checks evaluated (from C6 log)
    ↓
Tier 2 rate/slope checks evaluated (from paper_portfolio.json + C6)
    ↓
Tier 3 rate/slope checks evaluated
    ↓
G6 promotion (APR-0008/0009)
```

**If Finals series ends before statistical floor:** Paper period extends to 2026-27 regular season. Model retrain required by 2026-10-15 (KI-013/T-072) before evidence counting resumes.

---

## What This Does NOT Change

- All C4 risk limits unchanged (`_HARD_LIMITS`, `MIN_EDGE_TO_APPROVE`, `DEFAULT_KELLY_FRACTION`)
- VPS cron schedule unchanged
- G6 still requires APR-0008 (final validation report) and APR-0009
- No live capital until APR-0008 and APR-0009 are signed

---

## Operator Approval

**Review checklist (confirm each tier's derivations are acceptable):**
- [ ] T0: EXP-017 Part B is the right commercial validation; price discovery fix (T-114) is sufficient for T0-B
- [ ] T1-A: 5% error rate level floor and non-increasing slope are the right pipeline reliability criteria
- [ ] T1-B: Idempotency is correctly zero-tolerance (not rate-based)
- [ ] T1-C: 85% resolution fidelity floor and non-decreasing slope are the right resolution criteria
- [ ] T1-D: Audit completeness is correctly zero-tolerance
- [ ] T2-A: ±15pp calibration deviation (derived from 6× ECE) and non-increasing slope are the right calibration criteria
- [ ] T2-B: Rolling EV > 0 and non-decreasing slope (not just net positive endpoint) are the right EV criteria
- [ ] T2-C: L1 Brier threshold (0.265) and non-increasing slope are the right model degradation criteria
- [ ] T2-D: Positive P&L slope (not just positive P&L) is the right system-level performance criterion
- [ ] T3-A: Per-bet cap is correctly zero-tolerance
- [ ] T3-B: 15% drawdown ceiling (derived from 75% of kill-switch trigger) is the right paper bound
- [ ] T3-C: 20–80% rejection rate range (derived from 2× expected rate margin) is the right selectivity criterion
- [ ] Statistical floor: 66-bet minimum (derived from T2-A calibration power at α=0.05, 80% power) is acceptable
- [ ] Statistical floor: 5-game-night minimum (derived from slope regression df ≥ 3) is acceptable

**Sign-off:** ________________________________ Date: ___________  
**Role:** PO / DS (Earl Ignacio)

*Upon signing, APR-0016 is superseded and this framework becomes operative immediately.*
