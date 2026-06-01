# APR-0017 — G6 Multi-Dimensional Evidence Standard

**Status:** PENDING — operator review and sign-off required  
**Supersedes:** APR-0016 (G6 evidence threshold: 30 resolved paper bets with positive P&L)  
**Approval required from:** PO (Earl Ignacio, operator), DS (Earl Ignacio, strategy)  
**Drafted:** 2026-06-01  
**Effective when:** Signed by PO + DS; immediately supersedes APR-0016  
**Expiry:** Superseded by G6 gate closure (APR-0008/0009)  
**Why now:** GG-005 (registered 2026-05-31) established that APR-0016's count-based criterion is the wrong primary metric. ADR-0006 (2026-06-01) deleted the count gate from C4 for identical reasons — count is incoherent in a multi-band, 80-player execution system. Q7 (ARE WE COMPROMISED?) requires that every gate criterion pass the broken-system test. APR-0016 does not pass it.

---

## Why APR-0016 Fails the Broken-System Test

Q7 asks: what broken system could produce passing evidence?

| APR-0016 criterion | Broken system that passes |
|--------------------|--------------------------|
| 30 resolved bets | Accumulate 30 bets in one lucky Finals night at 17-40+/night throughput. One-night variance is not signal. |
| Positive P&L | 28 losses + 2 large wins. Net positive but negative trend. |
| (implicit) No calibration check | Miscalibrated model; bets sized by bad probabilities but lucky in test window. |
| (implicit) No commercial validation | EXP-017 Part B never run; bot prices against model_p − 0.50 null, not real Kalshi prices. |
| (implicit) No execution quality check | Duplicate-bet bug re-introduced; audit log gaps; no idempotency confirmation. |

**Verdict:** APR-0016 can be cleared by a lucky variance run on a miscalibrated, commercially unvalidated bot with execution bugs. It is not fit to gate live capital.

---

## APR-0017 Evidence Framework

**Structure:** Sequential tiers. Each tier is a prerequisite for the next. Failure in any tier halts G6 promotion regardless of bet count. Tier 0 must be satisfied before any G6 evidence counting begins.

---

### Tier 0 — Commercial Preconditions

*Must be true before the paper trading period counts as G6 evidence.*

| Criterion | Pass Condition | Status |
|-----------|---------------|--------|
| T0-A: EXP-017 Part B | Model achieves positive expected value against real Kalshi historical prices (not null baseline). Run: `python3 run_exp017.py --kalshi-prices kalshi_prices.csv`. GG-004 closes on CONFIRMED result. | PENDING (operator action required) |
| T0-B: Price discovery uses production API | All market price fetches hit `external-api.kalshi.com` regardless of BOT_ENV. Paper mode suppresses order submission only. | ✅ COMPLETE — T-114 (2026-06-01): `_price_discovery_url()` implemented; 3 invariant tests lock behavior. |

**Broken-system test for T0:**
- T0-A: Could run EXP-017 on a cherry-picked time window that excludes periods of model degradation. Mitigation: use full TEST period (2025-04-14 onward); require same model version as deployed.
- T0-B: Could re-introduce demo routing by changing BOT_ENV behavior. Mitigation: `test_unauthenticated_get_uses_production_url_in_paper_mode` (test_kalshi_client.py) will fail on any regression.

---

### Tier 1 — Execution Integrity

*The machine works reliably. Verified from C6 audit log + run logs.*

| Criterion | Pass Condition | Audit Source |
|-----------|---------------|--------------|
| T1-A: Pipeline stability | Pipeline fires correctly on ≥5 distinct game nights with no system errors and no missed cron windows | VPS cron logs + C6 PIPE-03 events |
| T1-B: Idempotency confirmed live | Zero duplicate bets detected across all cron windows in the paper period. (T-101 fixed the root cause; this confirms it holds live.) | C6 audit log: no duplicate `client_order_id` within any PIPE-03 session |
| T1-C: Resolution accuracy | ≥20 resolved positions confirmed correct outcome against nba_api final boxscores | paper_portfolio.json `closed_positions` with `resolution_source: "nba_api"` |
| T1-D: Audit log completeness | Every approved/rejected bet appears in C6 with full traceability chain. No PIPE-03 run produces approved bets without a corresponding C6 log event. | C6 JSONL: every `approve` or `reject` event traceable to a `PIPE-03` session_id |

**Broken-system test for T1:**
- T1-A: Count a night with a partial pipeline failure as "successful." Mitigation: "no system errors" is an explicit qualifier — any ERROR-severity C6 event during PIPE-03 disqualifies that night.
- T1-B: Idempotency check passes locally but VPS CWD path issue re-emerges. Mitigation: T-101 fix uses absolute `_SRC_ROOT / "logs"` path; verify portfolio file path in VPS run log.
- T1-C: Resolution uses stale boxscore data. Mitigation: `run_resolve_local.py` runs locally after nba_api updates (≥10:00 AM ET day after game); resolution timestamp recorded.
- T1-D: Logging fails silently. Mitigation: C6 has a fallback write failure path — if write fails, the error is re-raised, not swallowed.

---

### Tier 2 — Model Performance Trends

*The model works. Measured as trends over the paper period, not endpoints.*

| Criterion | Pass Condition | Notes |
|-----------|---------------|-------|
| T2-A: Calibration holds live | Realized win rate within ±15% of mean predicted probability across all resolved bets | Expected if model is properly calibrated (ECE 0.0247 on TEST set) |
| T2-B: Positive realized EV | Realized EV (net P&L / total amount wagered) positive across the statistical floor sample | Requires ≥50 resolved bets (see floor below) to have statistical power |
| T2-C: Brier within L1 threshold | Paper Brier score on resolved bets ≤ 0.265 (L1 drift threshold from MONITORING_DRIFT_PLAN.md) | Confirms model is not degraded during live paper period |
| T2-D: P&L trend positive | Median game-night P&L positive across all qualifying game nights — not just net positive at sample end | Eliminates: "27 losing nights + 3 big winning nights = net positive but broken" |

**Broken-system test for T2:**
- T2-A: Win rate is within range by chance on small N. Mitigation: statistical floor (see below) ensures sample size provides meaningful power.
- T2-B: Large bet on a lucky high-edge market dominates total EV. Mitigation: compute per-bet EV, not just total P&L.
- T2-C: Brier evaluated on unresolved bets (model assigns probability to outcomes not yet known). Mitigation: Brier computed only on `resolution_source: "nba_api"` confirmed positions.
- T2-D: Two large wins on game nights 1 and 2 inflate median. Mitigation: ≥5 game nights required ensures median is computed over meaningful sample.

---

### Tier 3 — Risk Control Validation

*The guardrails work. Verified from paper_portfolio.json + C6 log.*

| Criterion | Pass Condition | Notes |
|-----------|---------------|-------|
| T3-A: Per-bet cap respected | No resolved bet's `approved_size_usd` exceeded $500.00 in any PIPE-03 run | Kelly + $500 cap in C4; this confirms C4 is operative in production |
| T3-B: Drawdown within bound | Peak realized drawdown during paper period never exceeded 15% of starting bankroll | Kill switch at 20%; 15% paper threshold confirms headroom |
| T3-C: C4 selectivity confirmed | C4 rejection rate 20–80% across the paper period | Below 20%: risk engine is a rubber stamp. Above 80%: something is wrong with edge calculation or market access. |

**Broken-system test for T3:**
- T3-A: A Kelly explosion on a miscalibrated edge generates a $600 bet; C4 cap clips it; the $600 figure isn't recorded. Mitigation: audit log records `approved_size_usd` before Kelly cap is applied; verify clipping is logged, not hidden.
- T3-B: Drawdown never reaches 15% because bet sizes are tiny (model finding no edge). Mitigation: T3-C rejection rate check ensures the system is actually placing bets.
- T3-C: C4 rejects because MIN_EDGE threshold is misconfigured rather than because markets are priced fairly. Mitigation: sample a selection of rejected bets and verify the edge was correctly computed as < 0.02.

---

## Statistical Validity Floor

**These are validity thresholds, not gate criteria.** Meeting the floor is necessary but not sufficient.

| Floor | Value | Rationale |
|-------|-------|-----------|
| Resolved bets | ≥50 | At win rate ~60%, SE = √(0.6×0.4/50) ≈ 0.069; 10pp edge is ~1.4 SE from null. Provides meaningful but not conclusive power. |
| Distinct game nights | ≥5 | Ensures trends are not one-night variance. A T2-D median requires ≥5 data points. |

**Floor + tier relationship:**
- Reaching floor while failing any Tier 2 criterion = automatic gate failure
- Reaching floor while all Tier 1–3 pass = eligible for G6 promotion
- Below floor = defer regardless of tier status (insufficient statistical power to adjudicate)

---

## Gate Dependencies and Critical Path

```
EXP-017 Part B (T0-A)          ← BLOCKING — operator action required
    ↓
Tier 0 complete
    ↓
Paper period begins (Finals G1, Jun 3 — already running on VPS)
    ↓
Tier 1 criteria accumulate over ≥5 game nights
    ↓
Statistical floor met (≥50 resolved bets, ≥5 game nights)
    ↓
Tier 2 + Tier 3 evaluated
    ↓
G6 promotion (APR-0008/0009)
```

**T0-B is already complete** (T-114, 2026-06-01). T0-A is the only Tier 0 blocker.

**EXP-017 Part B is operator-action:** requires pulling Kalshi historical prices via:
```bash
GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true
```
Save as `exp_output/EXP-017/kalshi_prices.csv`, then run `run_exp017.py --kalshi-prices`.

---

## What This Does NOT Change

- Bankroll remains $683.41 actual / $1,000 demo paper balance
- All risk limits unchanged (C4 `_HARD_LIMITS`, MIN_EDGE_TO_APPROVE, DEFAULT_KELLY_FRACTION)
- VPS cron schedule unchanged
- G6 approval still requires APR-0008 (PO/RCO sign-off on final validation report) and APR-0009
- No live capital until APR-0008 and APR-0009 are signed

---

## Operator Approval

**Review checklist:**
- [ ] Tier 0 criteria are the correct commercial preconditions
- [ ] Tier 1 criteria correctly verify execution reliability
- [ ] Tier 2 criteria correctly measure model performance trend (not just endpoint)
- [ ] Tier 3 criteria correctly verify risk controls are operative
- [ ] Statistical floor (≥50 bets, ≥5 game nights) is acceptable
- [ ] Broken-system test responses are adequate

**Sign-off:** ________________________________ Date: ___________  
**Role:** PO / DS (Earl Ignacio)

*Upon signing, APR-0016 is superseded. G6 evidence counting rules change immediately.*
