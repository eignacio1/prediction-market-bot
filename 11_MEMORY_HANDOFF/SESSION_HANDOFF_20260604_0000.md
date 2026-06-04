# Session Handoff — 2026-06-04T00:00Z

**Trigger:** Session end — Finals Game 1 resolved; operator-initiated handoff
**Last commit:** `d9cc855` (main) — SESSION 27 Bloomberg terminal

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing locally (VPS deploy pending)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; **DEPLOY PENDING** (paper_trader.py + run_t4_live.py not yet pushed)
- **Paper bets:** 32/66 unique markets resolved (G6 APR-0017 gate); 1/5 game nights — Finals Game 2 is next

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Finals G1 paper resolution: 1417 positions, bankroll $1,404.80, P&L −$95.20 (−6.3%), win rate 30.1% | First full game-day resolution on clean evidence window (post-ADR-0006 + all-threshold loop). Knicks won. 30.1% win rate depressed by Finals defensive intensity vs. historical norms model was trained on. | DECISION_LOG.md 2026-06-04 SESSION 28 | DS |
| EXP-017 Part B verdict: DIRECTIONAL_NEGATIVE (n=32, EV=−$0.162/bet, mean_edge_vs_market=+0.1366) | Model beats null (Part A +$0.054) but loses to actual Kalshi prices. Market correctly prices Finals defensive context that T1 model misses. GG-004 OPEN. Statistical power INSUFFICIENT (n=32 < ≥66 floor). | DECISION_LOG.md 2026-06-04 SESSION 28; exp_output/EXP-017/EXP-017_results.json | DS |
| T4_EXPECTED_TOTAL_EDGE calibrated 5.0 → 441.38 from G1 T4 audit log | 1446 evaluations, sum(edge)=441.38. Monitoring/planning constant only. T4_BAND_WEIGHT remains STUB (GG-011 registered — fractional-allocation incompatible with high-throughput T4). | DECISION_LOG.md 2026-06-04 SESSION 28; run_t4_live.py | DS |
| GG-011 registered: T4_BAND_WEIGHT architecture incompatible with ~1,434 approved bets/game | Uncapped Kelly G1 = $81,226 across 1434 bets — 87× any reasonable band budget. New ADR required before T4 ACTIVE. LOW severity now (paper bypasses). | GOVERNANCE_GAP_LOG.md GG-011 | DS |
| Same-day resolution bug fixed: `game_date < today` → `game_date <= today` in paper_trader.py | Local PDT date = game date = 2026-06-03; strict `<` excluded all same-day games. PlayerGameLog only returns final stats (safe). | paper_trader.py:resolve_pending() | DS |
| APR-0017 ≥66 statistical floor flagged for regression-based revision as strategy enhancements proceed | δ=15pp detection threshold set for baseline T1-only model. As model improves (opponent features, matchup modeling), δ changes and floor must be re-derived. Not frozen — re-derive at each major model version change before G6 EXP-017 re-run. | DECISION_LOG.md 2026-06-04 SESSION 28 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Finals G1 resolution via run_resolve_local.py | ✅ 1417 positions settled in ~37 min (Playoffs fallback: 2 API calls × 0.6s/position). Portfolio synced to VPS. |
| Same-day resolution bug fix | ✅ `paper_trader.py:resolve_pending()` line ~299: `game_date < today` → `game_date <= today` |
| T4_EXPECTED_TOTAL_EDGE calibration | ✅ `run_t4_live.py` updated 5.0 → 441.38. GG-011 registered for T4_BAND_WEIGHT. |
| EXP-017 Part B G1 run | ✅ DIRECTIONAL_NEGATIVE (n=32, EV=−$0.162/bet). Results in exp_output/EXP-017/EXP-017_results.json. |
| DECISION_LOG SESSION 28 entries (4 rows) | ✅ G1 resolution, EXP-017 Part B, G6 floor revision flag, T4 calibration |
| MEMORY_BANK.md updated | ✅ Current State Snapshot, Last reviewed, Last major milestone — all reflect G1 results |
| TODO_NEXT.md updated | ✅ SESSION 28 completed + open items table; VPS deploy + G2 MC verify as CRITICAL/HIGH |
| PLAN.md updated | ✅ Last reviewed header |

---

## PDTP REVIEW STACK — G1 Raw Numbers + Assessment

*Princeton Deep Thinking Protocol: structured 4-pass analysis for handoff to next session.*

### Pass 1 — Deconstruction: What actually happened?

**Raw numbers:**

| Metric | Value |
|--------|-------|
| Positions resolved | 1417 |
| Open positions remaining | 0 |
| Starting bankroll (T1+T4 combined) | $1,500 |
| Final bankroll | $1,404.80 |
| Realized P&L | −$95.20 |
| P&L % | −6.3% |
| Win rate | 30.1% (426/1417) |
| Realized drawdown | 9.5% of initial |
| Game nights completed | 1 of ≥5 |
| Unique markets (EXP-017 n) | 32 |
| EXP-017 Part B EV/bet | −$0.162 |
| EXP-017 Part B win rate | 21.9% |
| Mean edge vs. Kalshi market | +0.1366 |
| Mean edge vs. null | −0.0003 |
| EXP-017 Part A EV (null baseline) | +$0.054/bet |
| T4 evaluations (G1) | 1446 |
| T4 sum(edge) | 441.38 |
| T4 approved bets | ~1,434 |
| T4 uncapped Kelly deployment | $81,226 (87× band budget) |

**Note on T1 vs T4 P&L split:** The 1417 positions = 3 T1 + 1414 T4 (flat 1-contract, pool_isolated). The −$95.20 P&L is primarily from T1 positions (not T4 flat-sizing, which tracks against PAPER_T4_POOL_USD separately). T4 resolution appears in the portfolio but pool_isolated=True means T4 does not deduct from T1 bankroll.

---

### Pass 2 — Sequential Processing: What does each data point mean?

**30.1% win rate:**
T1 model predicts ~54-60% probability on its approved bets (MIN_EDGE gate + Poisson CDF path). Observed 30.1% means outcomes ran below model estimates. Two explanations: (a) Finals defensive intensity suppresses scorer totals vs. regular season norms the model was trained on — Fox 25+ case is the exemplar (model 57%, market 7.5%, actual 7 pts); (b) T4 flat-sizing included players where Poisson threshold estimate was above market but market was right.

**Mean edge vs. Kalshi market = +0.1366:**
The model sees itself as 13.7pp above the market price on average. The model LOST (win rate 21.9% vs. implied ~57%). This is not a small calibration error — the model is systematically overestimating win probability vs. market by a large margin in this sample. The market was right. The model was wrong.

**EXP-017 Part A (+$0.054) vs Part B (−$0.162):**
Part A tests model against a flat 50% coin flip. Part B tests model against actual Kalshi prices. The model beats the coin flip but loses to the market. This is the diagnostic that distinguishes "model works" from "model beats an informed counterparty." The gap is large: +$0.054 vs −$0.162 = $0.216/bet difference. The market is incorporating Finals-specific information the T1 model does not have.

**n=32 vs ≥66 floor:**
32 unique markets is one Finals game (5 players matched × ~6-7 thresholds each). INSUFFICIENT statistical power for G6. But the DIRECTIONAL_NEGATIVE verdict at n=32 is informative even before the floor: the model is losing by $0.162/bet, not hovering near zero. This is not noise — it is likely systematic.

**GG-011 ($81,226 uncapped Kelly):**
This is the most alarming G1 data point architecturally. At Kelly=0.20 and ~1,434 approved bets, the system would have deployed $81,226 if not paper-only. At any realistic bankroll ($683–$1,500), this is a capital destruction event. The T4_BAND_WEIGHT fractional-allocation formula (bankroll × RESERVE × BAND_WEIGHT) cannot contain this. New ADR is mandatory before T4 ACTIVE.

---

### Pass 3 — Synthesis + Rivals: What's the competing hypothesis?

**Hypothesis A (adopted):** Model systematically overestimates win probability in Finals context because the feature set lacks opponent quality (opp_def_rating_l10_mean, F-040) and Finals/Playoffs adjustment factors. Market prices these correctly. Root cause: TeamStatsStore F-040 is built but FALSIFIED by EXP-012 at current N. The model needs a new experiment validating opponent features before re-enabling.

**Hypothesis B (rival):** Small sample variance. n=32, one game night. The 30.1% win rate could be a bad night for above-threshold scorers regardless of opponent. Counter: the Fox 25+ example is not variance — market priced 7.5% correctly vs. model's 57%. The magnitude of mean_edge_vs_market=+0.1366 is too large for pure variance.

**Hypothesis C (structural):** Poisson CDF with pts_l10_mean as λ is too simple. It doesn't account for minutes restriction, injury status, game pace, or opponent quality. Even vs. null (Part A), EV is only +$0.054 — not large. Against an informed market, this thin edge evaporates.

**Synthesis:** Hypotheses A and C are compatible and probably both true. The model's feature set is missing opponent context (H-A) AND the Poisson model class itself may be too simple to beat a Finals market (H-C). Both corrections point to the same dark period build: (1) add opponent defensive rating (F-040) to C2 and retrain per T-072; (2) validate with EXP-017 re-run in regular season.

**PDTP Contradiction check:** The DECISION_LOG says EXP-017 Part A EV is positive and "strong directional evidence." If Part B shows DIRECTIONAL_NEGATIVE with a large magnitude, Part A's optimism needs qualification: Part A is only valid if the market prices near the null (0.50). In Finals markets, the market prices far from 0.50 for specific thresholds (Fox 25+: market 7.5%, not 50%). Part A never tested the model against a market pricing at 7.5%. This is the core limitation of Part A as a commercial validation tool.

---

### Pass 4 — Finalization: What must tomorrow's session do?

**BINDING G6 constraint:** EXP-017 Part B DIRECTIONAL_NEGATIVE. This means the commercial EV question is answered — negatively — at n=32. The path to G6 is not "accumulate 66 more bets." The path is: (1) fix the feature gap (add opponent features, retrain), (2) validate fix with new EXP-017 run, (3) confirm positive EV vs. actual Kalshi prices, (4) accumulate ≥66 markets + ≥5 nights on the FIXED model. Continuing to accumulate evidence on the CURRENT broken model does not advance G6.

**Confidence gradient (PDTP P4.4):**
- HIGH confidence: model beats null (Part A) — 2692 test rows, multiple MIP levels
- HIGH confidence: model loses to Finals market (Part B n=32) — large effect, specific mechanism identified
- MEDIUM confidence: opponent features are the fix — mechanism is plausible, needs EXP validation
- LOW confidence: fix will be sufficient — other factors (game pace, Finals-specific rest effects) may persist

**Blind spot check:** Is there any case where DIRECTIONAL_NEGATIVE is a VPS/data artifact rather than a real signal? VPS delivered prices correctly (production Kalshi API, T-114 confirmed). Portfolio prices are T1 cron prices (22:00 UTC), not execution prices. The mismatch from pre-ADR-0006 sessions is eliminated in clean evidence. No data integrity concern identified.

---

## G6 Gate Floor Revision (Per Earl's Request)

**Current floor:** ≥66 resolved markets (derived: calibration power formula, α=0.10, power=0.80, δ=15pp)

**Earl's instruction:** Revise via regression analysis as strategy enhancements proceed.

**What "revision" means operationally:**
The ≥66 floor was derived from: `n = (z_α/2 + z_β)² × p̂q̂ / δ²` where δ=15pp was set for the baseline T1-only model. As strategy enhancements are added:
- If model ECE improves → δ may be set tighter (smaller detectable difference) → n increases
- If model win rate variance decreases → p̂q̂ decreases → n decreases  
- If α/β are tightened (more conservative) → n increases

**Action required:** At each major model version (retrain with opponent features per T-072), re-run the formula with updated δ estimate. δ = expected improvement vs. market at the new calibration level. Document derivation in DECISION_LOG before each EXP-017 re-run. Do not apply the current ≥66 to a significantly different model — re-derive.

**Current floor status:** ≥66 OPERATIVE for Finals paper window on current T1 model (v1-28483b21). Revision pending T-072 model refresh.

---

## ONE THING PENDING

**VPS deploy is blocking Finals Game 2 evidence quality.** The same-day resolution bug fix (`paper_trader.py`) and T4_EXPECTED_TOTAL_EDGE=441.38 (`run_t4_live.py`) are local-only. Without deploy before Jun 5 2:55 PM PDT:
1. Finals G2 T1 bets resolve correctly on local machine only; VPS `run_resolve.py` still has the bug (though T-109 runs locally anyway)
2. T4 on VPS still reports stale T4_EXPECTED_TOTAL_EDGE=5.0 in logs

Deploy command (run locally before G2 cron):
```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
git push
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && git pull && source venv/bin/activate && python -m pytest tests/ -q --tb=no 2>&1 | tail -5'
```

---

## Current Paper Portfolio

- **T1 Bankroll:** ~$404.80 (post-G1 T1 P&L; started $1,000 T1 reset)
- **T4 Pool:** pool_isolated — tracks separately against PAPER_T4_POOL_USD=$500
- **Total system bankroll:** $1,404.80 (combined as tracked in portfolio)
- **Open positions:** 0
- **Resolved:** 1417 (32 unique markets for EXP-017)
- **G6 gate progress:** 32/66 unique markets | 1/5 game nights | P&L NEGATIVE (GG-004 OPEN)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py — 403-blocked on VPS; T-109 local procedure covers this)
14:00 UTC Mon — Model freshness check
```

**Finals Game 2:** Jun 5 PDT — T1 cron fires at 22:00 UTC Jun 5 (2:55 PM PDT). MC verify before that.

---

## Key Constraints to Remember

1. **stats.nba.com 403 blocks VPS** — resolution must always run locally via `run_resolve_local.py`
2. **No live capital until G6** — APR-0017 four-tier gate; GG-004 OPEN (DIRECTIONAL_NEGATIVE)
3. **EXP-017 verdict is DIRECTIONAL_NEGATIVE** — path to G6 requires model fix (opponent features), not just accumulation
4. **VPS deploy pending** — push before Finals Game 2 (Jun 5 2:55 PM PDT)
5. **T4_BAND_WEIGHT is STUB** — GG-011 blocks T4 ACTIVE; new ADR required before live T4

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents in modified paths.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| paper_trader.py (bug fix) | N/A — code only | Same-day resolve fix logged | ✅ |
| run_t4_live.py (calibration) | N/A — code only | T4_EXPECTED_TOTAL_EDGE + GG-011 logged | ✅ |
| DECISION_LOG.md | ACTIVE (no decisions_logged field) | 4 new SESSION 28 rows | ✅ |
| MEMORY_BANK.md | ACTIVE (no decisions_logged field) | Updated Current State Snapshot | ✅ |
| TODO_NEXT.md | ACTIVE | SESSION 28 completed + open items | ✅ |
| GOVERNANCE_GAP_LOG.md (GG-011) | ACTIVE | Added GG-011 this session | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260604_0000.md.
# Priority 1: git push and VPS deploy (paper_trader.py + run_t4_live.py) before Jun 5 2:55 PM PDT.
# Priority 2: Run MC verify for Finals Game 2: BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2
# Priority 3: Portfolio reset decision (current T1 bankroll ~$404.80; evaluate reset to $1,000 before G2).
# GG-004 path: add opponent features (F-040 opp_def_rating_l10_mean) to C2, retrain per T-072, re-run EXP-017."
```
