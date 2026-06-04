# EXP-018 — Opponent-Adjusted λ: EV Test Against Kalshi Prices

**Status:** PENDING — awaiting paper trading data on adj_λ model  
**Registered:** 2026-06-04 SESSION 30  
**Hypothesis:** Opponent-adjusted Poisson λ (`adj_λ = pts_l10_mean × opp_def_l10 / 113.0`) will produce positive net-of-fee EV against actual Kalshi market prices, correcting the DIRECTIONAL_NEGATIVE result from EXP-017 Part B.  
**Governance gap:** GG-004 (remains OPEN until this experiment confirms positive EV)  
**ADR:** ADR-0015  
**Blocks gate:** G6 (positive EV vs. Kalshi prices required)  
**Parent experiment:** EXP-017 (Part B: DIRECTIONAL_NEGATIVE, n=32, EV=−$0.162/bet)

---

## Why This Experiment Exists

EXP-017 Part B Finals G1 result: DIRECTIONAL_NEGATIVE. The root cause was identified as the Fox 25+ mechanism:
- Model: λ = pts_l10_mean = 27.5 → p(25+) = 57%
- Kalshi: priced at 7.5%
- Actual: 7 pts — market was correct

The model had no opponent context. Knicks defense (top-3 in the league, 2026 Finals) suppressed Fox to 7 pts. The Poisson λ used regular-season average ignoring the Finals defensive matchup.

**Architecture finding (SESSION 30):** The LR model (`p_est_lr`) is logged but NOT used for bet decisions. The Poisson CDF alone drives the bet direction and C4 gate. Adding F-040 to the LR model (original T-072 design) would have zero effect on trading behavior. The correct fix is `adj_λ` in the Poisson CDF. This ADR-0015 change is the minimal targeted fix to the actual bet-generating mechanism.

---

## Experimental Design

### Measurement

After ADR-0015 deployment (2026-06-04 SESSION 30), all paper bets use:
```python
adj_λ = pts_l10_mean × clip(opp_def_l10 / 113.0, 0.70, 1.30)
p_threshold = 1.0 - Poisson.CDF(threshold - 1, adj_λ)
net_edge = p_threshold - kalshi_mid - half_spread - 0.07 × mid × (1-mid)
```

### Metrics

| Metric | Definition | Acceptance threshold |
|--------|-----------|---------------------|
| EV/bet (Part B) | `(win_rate × payout) - (1-win_rate) × stake` per unique market | > 0 |
| Net-of-fee EV | EV after Kalshi taker fee = `0.07 × P × (1-P)` | > 0 |
| n | Unique markets (≠ positions — multiple thresholds per player per game) | ≥ 30 |
| Win rate | Resolved YES bets that settled YES + NO bets that settled NO | TBD |
| Mean opp_adj_factor | `adj_λ / pts_l10_mean` across all approved bets | Expected < 1.0 in Finals (Finals D > league avg) |

### Falsification

If EV/bet ≤ 0 after ≥ 30 unique markets, Hypothesis C from PDTP_FINALS_G1 is promoted:
> Poisson model class is too simple — pace, foul rate, minute restrictions, and within-game variance not captured by pts_l10_mean regardless of opponent adjustment.

At that point, model class change (superseding ADR-0014 §T1 + ADR-0004) is required.

---

## Comparison to EXP-017 Part B

| Metric | EXP-017 (raw λ) | EXP-018 (adj_λ) |
|--------|----------------|-----------------|
| Model | `p = Poisson.CDF(thr-1, pts_l10_mean)` | `p = Poisson.CDF(thr-1, adj_λ)` |
| Fee gate | Not applied | Fee-adjusted edge (ADR-0016) |
| EV/bet | −$0.162 (DIRECTIONAL_NEGATIVE) | TBD |
| n | 32 (Finals G1 only) | Target ≥ 30 |

---

## Status Log

| Date | Event |
|------|-------|
| 2026-06-04 | Registered (SESSION 30) |
| TBD | First paper night on adj_λ model (Finals G2) |
| TBD | ≥30 unique markets accumulated |
| TBD | EXP-018 verdict + GG-004 resolution |
