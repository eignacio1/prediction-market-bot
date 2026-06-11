# Monte Carlo Pre-Game Assessment Protocol

**Status:** ACTIVE  
**Established:** 2026-06-02 SESSION 16  
**Decision:** Operator-mandated. See DECISION_LOG Session 16.  
**Script:** `scripts/run_monte_carlo.py`

---

## Purpose

Any time a strategy shift, architectural update, or decision drift affects C3/C4 behaviour, the impact on P/L and bot activity statistics must be quantified before the change is committed or the next cron fires. This protocol defines when to run it, how to run it, and what to look for.

---

## Trigger Conditions

Run the Monte Carlo whenever **any of the following are true**:

| Trigger | Category | When |
|---------|----------|------|
| ADR accepted that changes kelly fraction, min_edge, or max_exposure | C4 change | Before next PIPE-03 |
| Model retrain or model version bump (ADR required — frozen model policy) | C3 change | Before next PIPE-03 |
| Feature version update (C2 change that alters pts_l10_mean values) | C3 change | Before next PIPE-03 |
| New threshold types or market structure registered in market_mapper.py | C5/C2 | Before first affected PIPE-03 |
| Bankroll drops >20% from last assessment baseline | Risk event | Next available pregame |
| Kill switch fires or drawdown exceeds 10% | Risk event | Before resuming PIPE-03 |
| Session-start protocol surfaces a new governance gap (OPEN) | Governance | Same session |
| Operator request ("what would happen if...") | Ad hoc | On demand |

**Not a trigger:** game-to-game parameter drift, normal bankroll fluctuation, cron schedule changes.

---

## How to Run

### Standard run (after most triggers):

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
PYTHONPATH=src python3 scripts/run_monte_carlo.py
```

Auto-discovers the latest `pregame_YYYYMMDD.json`. Reads bankroll from `logs/paper_portfolio.json`.

### Before/after comparison (for ADR or parameter changes):

Run baseline first, then re-run with the proposed parameters:

```bash
# Step 1 — baseline (current parameters)
PYTHONPATH=src python3 scripts/run_monte_carlo.py \
  --label "before-ADR-XXXX" \
  --out logs/mc_before_adr_xxxx.txt

# Step 2 — apply the ADR change to the codebase

# Step 3 — re-run with same pregame to isolate the parameter effect
PYTHONPATH=src python3 scripts/run_monte_carlo.py \
  --kelly 0.12 \
  --label "after-ADR-XXXX" \
  --out logs/mc_after_adr_xxxx.txt

# Step 4 — compare
diff logs/mc_before_adr_xxxx.txt logs/mc_after_adr_xxxx.txt
```

To test a parameter change without committing it:

```bash
PYTHONPATH=src python3 scripts/run_monte_carlo.py --kelly 0.15 --min-edge 0.03
```

### On VPS (after PIPE-02 runs, if manual check needed):

```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33
cd /opt/prediction-market-bot
/opt/prediction-market-bot/venv/bin/python3 scripts/run_monte_carlo.py
```

---

## Output Sections and What to Review

### BOT STATISTICS
- **Bets PLACED**: total approved. For a standard Finals game expect 15–30 bets.
- **Bets exp. to WIN**: high win rates (>85%) are expected; bot bets on high-probability outcomes with market mispricing. Healthy.
- **Bets REJECTED/PASS**: review rejection reasons. `min_bet_floor` rejections after sequential bankroll depletion are expected at paper scale — they indicate high-edge bets that arrive late in the market iteration and get cut off by Kelly producing sub-$10 stakes. Flag if high-edge (>0.10) bets are being killed this way — it's a batch ordering issue, not a model issue.
- **Reserve (T4/T5)**: should be ≥$400 (40% of $1,000 bankroll, RESERVE_MANDATE_PCT=0.40). If below, flag it. Batch-level enforcement is a dark-period fix.

### EXPECTED VALUE
- **Analytical EV** is the pre-game estimate; actual P/L may differ due to game outcomes.
- **ROI on deployed** > 10% is the target signal for positive expected value.
- **GG-004 caveat applies**: EV is vs. Poisson model, not vs. adversarial market. EXP-017 Part B is the real test.

### MONTE CARLO P/L DISTRIBUTION
- **Kill switch risk** should be near 0% at paper scale. If > 1%, investigate parameter changes.
- **p5** should ideally be > -$50 (5th percentile; rare tail). If worse, review max_exposure sizing.
- **Std deviation** relative to total_stake indicates concentration risk. High std / total_stake ratio means few bets are driving P/L.

### What should change after a parameter update

| Change | Expected effect |
|--------|----------------|
| kelly ↑ | Stakes ↑, total_stake ↑, std ↑, EV ↑ |
| kelly ↓ | Stakes ↓, total_stake ↓, std ↓, EV ↓ |
| min_edge ↑ | Fewer bets, PASS count ↑, EV/bet ↑, total_stake ↓ |
| min_edge ↓ | More bets, EV/bet ↓, total_stake ↑ |
| max_exposure ↑ | Stakes can be larger; mainly affects high f* bets |
| Model change | p_model values change → direction flips possible → recount YES/NO |

If the actual changes don't match this table, investigate before committing the ADR.

---

## Decision Log Requirement

Per CLAUDE.md rule #7: every strategic decision that triggers this assessment **must have a DECISION_LOG entry** before the next PIPE-03 fires. The entry should include:

1. What changed (ADR reference)
2. Baseline MC output summary (EV, bets placed, kill switch risk)
3. Post-change MC output summary
4. Decision: proceed, revert, or modify

---

## Known Limitations (read before interpreting results)

1. **GG-004 (OPEN):** All EV figures compare the Poisson model vs market mid — not adversarial Kalshi pricing. EXP-017 Part B (≥66 resolved bets) is the binding commercial validation. Until it clears, high EV in this sim does not confirm commercial viability.

2. **Independence assumption:** Player scores modeled as independent Poisson(pts_l10_mean). In reality, game pace correlates all players simultaneously. High-pace games inflate all YES outcomes and deflate NO outcomes. True P/L variance is higher than reported. Treat P5/P95 as conservative bounds.

3. **pts_l10_mean freshness:** The lambda values come from the most recent pregame JSON. If the last game was a significant outlier (injury substitution, blowout, garbage time), pts_l10_mean may not reflect current form. Check the pregame date against game recency.

4. **Sequential bankroll depletion:** Stakes are computed sequentially in market iteration order. High-edge bets that arrive late in the iteration may be rejected at `min_bet_floor` because earlier bets have already deployed most of the bankroll. This is a known gap (batch-level capital allocation deferred to dark period). It does NOT mean those markets have no edge — it means the current architecture can't size them at paper scale.

5. **No T4/T5 bets in this sim:** This script models T1 pre-game bets only. T4/T5 fire during the game and use whatever capital remains after T1 batch. The reserve figure in BOT STATISTICS is the T4/T5 budget.

---

## MC Track Record (T1 predictions vs. realized T1 P&L)

| Game | Predicted EV | Realized P&L | Miss | P(profit) | P(kill switch) | Notes |
|------|-------------|-------------|------|-----------|----------------|-------|
| G3 (2026-06-08) | +$138.47 | -$198.84 | -$337 | >95% | ~1% | Independence assumption failed: Brunson 42 pts → Castle/Hart underperformed vs pre-game λ |
| G4 (2026-06-10) | +$152.08 | -$119.58 | -$272 | 95.3% | 1.07% | Same failure mode: Brunson 36 pts dominated → Wemby 24 pts, correlated defensive effort. 2 of 35 bets were late-cron mid-game (ineligible per APR-0019). |

**Pattern (2 games):** Both G3 and G4 were >95% confidence positives that produced realized losses. The independence assumption (player scores modeled as independent Poisson) fails when a single player (Brunson) has an outsized game that suppresses teammates and opponents via pace/defensive load effects. True P/L variance is materially higher than reported — treat MC P(profit) as overstated until cross-player correlation is modeled.

**Standing instruction:** Do not cite MC P(profit) >95% as evidence of safety when placing new pre-game bets. It is a model consistency check, not a calibrated probability of realized profit. Realized drawdown as of G4: 24.3% (above 20% kill-switch threshold — DS reset decision required before G5).
