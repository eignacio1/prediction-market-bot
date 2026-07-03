# EXP-017 — EV Validation Against Actual Kalshi Market Prices

**Status:** PARTIAL — Part A complete 2026-06-01; Part B pending (Kalshi price data required)  
**Registered:** 2026-06-01  
**Hypothesis:** OQ-023 — does the model generate positive EV against actual Kalshi prices (not 0.50)?  
**Governance gap:** GG-004 — EV benchmark was never the commercial question  
**Known issue:** KI-017  
**Blocks gate:** G6 (live capital authorization requires this evidence)  
**Target window:** Dark period (2026-06-22 to 2026-10)

---

## What This Experiment Answers

Every prior EV figure in this project (`+$0.0958/bet`, `+$0.0855/bet`) was computed as:

```python
edge = model_p - 0.50   # mip = 0.50 (coin flip null)
```

This experiment computes:

```python
edge = model_p - kalshi_mid_price   # mip = actual Kalshi market price
```

These are different questions. The first asks: does the model beat random chance? The second asks: does the model beat professional market makers who have injury reports, advanced stats, and betting flow? This project exists to answer the second question.

---

## Design

### Data requirements

1. **Model test set:** Existing TEST rows from EXP-005 (2023-24 season, ~3,254 rows) — player, game_date, threshold, actual outcome, model_p, model_edge_vs_null
2. **Historical Kalshi prices:** Mid-prices for the same player/game/threshold combinations during the TEST period

### Historical price sourcing (TBD — operator action)

Options in priority order:

1. **Kalshi API historical endpoint:** `GET /trade-api/v2/markets` with date filters. Check if Kalshi provides historical mid-price data. If yes, pull for all TEST period tickers.
2. **Manual collection from existing paper portfolio logs:** If any TEST-period markets are still accessible in the API, pull current or recent prices as proxies.
3. **Inference from EXP-004 Part B:** Part B had live prices for 2 players. Expand this to the full TEST set if price data is available.

This data sourcing step is the primary blocker. Register as operator action before experiment can run.

### Methodology

```python
# For each row in TEST set where kalshi_mid_price is available:
edge_vs_market = model_p - kalshi_mid_price
ev_vs_market = edge_vs_market * kelly_fraction * bankroll_fraction

# Compute:
# 1. Distribution of edge_vs_market (vs. edge_vs_null)
# 2. Fraction of bets that still pass MIN_EDGE_TO_APPROVE = 0.02
# 3. Mean EV per bet vs market
# 4. Win rate on bets that pass the gate vs market
```

### Injury control

Per KI-011: bets where `kalshi_mid_price < 0.15` for a player with `pts_l10_mean > 15` are likely injury-priced. Run analysis both:
- Including these rows (raw result)
- Excluding rows where `|model_p - kalshi_mid_price| > 0.25` (injury filter)

The injury-filtered result is the more operationally relevant figure — it represents what the system would produce with the T2 injury overlay active.

---

## Success Criteria

| Metric | Pass | Fail |
|--------|------|------|
| Mean EV vs market | > 0 | ≤ 0 |
| % bets passing MIN_EDGE gate vs market | > 30% of bets that passed vs null | ≤ 30% |
| Injury-filtered EV vs market | > 0 | ≤ 0 |

**If FAIL:** G6 gate cannot be cleared on EV evidence alone. Paper P&L evidence becomes the primary (and only) argument for live capital. DS must decide whether to proceed, redesign model, or defer G6 indefinitely.

**If PASS:** Register as EXP-017 CONFIRMED. Update MODEL_CARD.md EV figure with market-benchmarked number. Proceed to G6 with full evidence base.

---

## Pre-Run Checklist

- [ ] Kalshi historical price data sourcing confirmed (operator action)
- [ ] TEST set rows matched to Kalshi ticker format
- [ ] Injury-flagged rows identified (mid_price < 0.15 for high-avg players)
- [ ] run_exp017.py created from EXP-TEMPLATE.md
- [ ] SNAP registered for historical price data before run

---

## Results

### Part A — Sensitivity Sweep (2026-06-01)

**Script:** `src/prediction_market_bot/run_exp017.py` (no args)  
**TEST set:** 2,692 rows | 47 players | 2025-26 Regular Season  
**Class balance:** 1,263 positive / 1,429 negative (47% positive)  
**VIG assumed:** 0.01 (measured 2026-05-28, 37 KXNBAPTS markets)  
**Results saved:** `exp_output/EXP-017/EXP-017_results.json`

| MIP  | YES bets | NO bets | Win%  | EV/bet    | Total P&L |
|------|----------|---------|-------|-----------|-----------|
| 0.40 | 2,226    | 211     | 50.5% | +0.0828   | +$201.81  |
| 0.43 | 1,948    | 359     | 52.9% | +0.0720   | +$166.19  |
| 0.45 | 1,717    | 466     | 53.5% | +0.0582   | +$127.13  |
| 0.47 | 1,527    | 648     | 54.9% | +0.0556   | +$120.99  |
| 0.49 | 1,306    | 865     | 56.1% | +0.0585   | +$127.05  |
| **0.50** | **1,200** | **975** | **55.9%** | **+0.0541** | **+$117.63** ◄ null baseline |
| 0.51 | 1,089    | 1,068   | 56.3% | +0.0577   | +$124.50  |
| 0.52 | 976      | 1,165   | 56.5% | +0.0619   | +$132.58  |
| 0.53 | 866      | 1,275   | 56.9% | +0.0696   | +$149.06  |
| 0.55 | 718      | 1,492   | 56.6% | +0.0786   | +$173.65  |
| 0.57 | 581      | 1,716   | 56.5% | +0.0942   | +$216.46  |
| 0.60 | 405      | 1,974   | 55.6% | +0.1171   | +$278.50  |

**Key findings:**
- EV is positive at ALL tested market price levels (0.40–0.60)
- EV *increases* as market prices move away from 0.50 in either direction — the model is exploiting systematic pricing deviations
- At MIP=0.60, NO bets dominate (1,974 of 2,379) because 47% actual positive rate means YES is overpriced at 0.60
- At MIP=0.40, YES bets dominate (2,226 of 2,437) because YES is underpriced at 0.40
- Interpretation: unless Kalshi prices are within ~0.02 of the model's estimates (highly efficient), the model finds positive EV

**GG-004 / OQ-023 status after Part A:**  
DIRECTIONAL EVIDENCE — edge is positive across the full realistic range of market prices. This does NOT close GG-004, because Part A uses uniform hypothetical prices, not actual Kalshi prices. Part B is still required for definitive confirmation.

### Part B — Historical Kalshi Price Validation

*Pending — requires operator to provide `exp_output/EXP-017/kalshi_prices.csv`.*

See Pre-Run Checklist for data collection instructions.

**Note (2026-07-03):** this Part B description is NBA-scoped and predates the MLB Part B (Live) results already logged directly in `GOVERNANCE_GAP_LOG.md` GG-004 (G2 Finals n=33 DIRECTIONAL_POSITIVE 2026-06-08; G4 n=96 DIRECTIONAL_NEGATIVE) — not reconciled into this file as part of this session's scope. See Part C below for the current, live commercial-validation track (MLB, T-184).

### Part C — MLB Real Portfolio Data (T-184, ADR-0024, run 2026-07-03)

**Script:** `scripts/run_exp017_mlb.py --portfolio <paper_portfolio_mlb.json>` (built SESSION 79, 2026-06-23; first run against real, non-empty MLB data 2026-07-03)
**Source:** real T1 MLB paper-trading portfolio (PIPE-05, `run_mlb_paper_trade.py`), 49 closed positions, all unique tickers, 0 duplicates
**Results saved:** `exp_output/EXP-017-MLB/EXP-017-MLB_results.json`

| Metric | Value |
|---|---|
| n (unique markets) | 49 |
| EV/bet | +$2.0408 |
| Win rate | 53.1% |
| Total P&L | +$100.00 |
| Direction split | YES n=2 (EV=-$0.807/bet, win=50.0%); NO n=47 (EV=+$2.162/bet, win=53.2%) |
| Threshold breakdown | k=1: n=26, EV=+$3.496/bet, win=42.3%; k=2: n=23, EV=+$0.396/bet, win=65.2% |
| ADR-0024 tier | Below Tier 1 (n≥150) and Tier 2 (n≥500 single-sport / n≥150 dual-sport, NBA n=0) |
| Edge Monotonicity (T-177/GG-037 guard) | INCONCLUSIVE — all 49 resolved positions carry edge>0 (the bot only fires above its edge threshold, so there's no natural edge≤0 comparison group in resolved data yet). Terciles all positive: T1 [+0.006,+0.045] win=56.2%; T2 [+0.046,+0.078] win=37.5%; T3 [+0.079,+0.169] win=64.7%. |
| **Verdict** | **DIRECTIONAL_POSITIVE** |

**Two loader bugs found and fixed during this run** (before the above numbers were trusted): (1) the loader read `p.get("threshold")` but the real producer emits `kalshi_threshold` — fixed with a fallback, 2 regression tests added; (2) the loader trusted a stored `fee_net_edge` field that `paper_trader.py` computes always YES-frame-signed, never flipped for NO-direction bets — corrupted the Edge Monotonicity check specifically (edge>0/edge≤0 exactly matched the YES/NO split before the fix). Fixed by always recomputing via `compute_fee_net_edge(direction, model_p, mip)` instead of trusting the stored value; 2 regression tests added. Full suite 102/102 passing post-fix. Neither bug affected the EV/win-rate/P&L/threshold-breakdown figures above (those read `pnl`/`outcome` directly). See GOVERNANCE_GAP_LOG.md GG-004 (updated) and GG-077 (new) for full derivation, and DECISION_LOG.md 2026-07-03 for the complete narrative.

**GG-004 status after Part C:** Still OPEN. Real MLB money produced a positive signal against actual Kalshi prices for the first time, but n=49 is well short of ADR-0024's adequacy floors. Continue accumulating T1 MLB volume; re-run this script periodically as the portfolio grows toward n=150 (Tier 1 diagnostic check) and n=500 (Tier 2 single-sport confirmation).
