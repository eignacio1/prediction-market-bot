# Session Handoff — 2026-06-04T15:00Z

**Trigger:** Session 30 complete — implementation done, context nearing limit  
**Last commit:** `7596956` (main) — LOCAL ONLY; push pending

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 715/715 passing locally; VPS smoke test PASS
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; all SESSION 30 code deployed
- **Paper bets:** 0 resolved on new adj_λ model (clean slate reset; G2 is first game)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **Architecture finding: LR `p_est_lr` is logged-only; Poisson CDF drives all T1 bets** | LR model runs but output never read after being written to forecast_rec. All bet decisions use `p_threshold = 1 - Poisson_CDF(thresh-1, λ)`. Original T-072 design (add F-040 to LR, retrain) would have zero effect on trading behavior. | DECISION_LOG.md 2026-06-04 SESSION 30 entry 1 | DS |
| **T-072 redesign: adj_λ in Poisson CDF (not F-040 to LR)** | Root cause of EXP-017 DIRECTIONAL_NEGATIVE is Poisson λ having no opponent context. Correct fix targets the actual bet-generating mechanism. No retrain required. | DECISION_LOG.md 2026-06-04 SESSION 30 entry 2; ADR-0015 | DS |
| **ADR-0015 ACCEPTED: `adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30)`** | Directly corrects Fox 25+ root cause (λ=27.5 → 57% vs Kalshi 7.5% → actual 7pts; Finals Knicks defense not captured). LEAGUE_AVG_PTS_ALLOWED=113.0 (2025-26 season). | ADR-0015 artifact; DECISION_LOG.md 2026-06-04 SESSION 30 entry 3 | DS |
| **ADR-0016 ACCEPTED: `net_edge = gross_edge - 0.07×mid×(1-mid)`. GG-009 RESOLVED** | Kalshi taker fee was absent from edge gate. Option B selected (per-market subtraction). Fee-negative bets rejected. gross_edge + kalshi_fee logged to every position for G6 subgroup analysis. | ADR-0016 artifact; DECISION_LOG.md 2026-06-04 SESSION 30 entry 4; GOVERNANCE_GAP_LOG.md GG-009 RESOLVED | DS |
| **Paper portfolio reset to $1,000 before Finals Game 2** | G1 evidence tainted (pre-adj_λ architecture). Clean EXP-018 baseline requires post-ADR-0015 data from G2 onward. T4 pool auto-resets from PAPER_T4_POOL_USD=$500 on restart. | DECISION_LOG.md 2026-06-04 SESSION 30 entry 5; paper_portfolio_g1_archive.json | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Architecture finding (LR logged-only) | ✅ Traced full T1 bet-generation path; confirmed Poisson CDF is the only mechanism that generates bet direction and C4 gate decision |
| T-072: parse_ticker_opponent() | ✅ `KXNBAPTS-YYMMDDTMAM-TMAPLAYER##-##` → opponent team abbr; 8 test cases including malformed/edge cases |
| T-072: opp_adjusted_lambda() | ✅ adj_λ formula; fallback to raw λ when store/opponent unavailable; 8 test cases |
| T-072: TeamStatsStore cache (to/from_cache_dict) | ✅ PIPE-02→PIPE-03 handoff via `logs/team_stats_cache_{GAME_DATE}.json`; 4 test cases |
| T-072: run_pregame.py integration | ✅ Section 4a builds TeamStatsStore (30 teams ~18s), writes cache; inference loop uses adj_λ; gross_edge + kalshi_fee logged |
| T-072: run_paper_trade.py integration | ✅ Section 5a loads from cache (fallback: fresh build); adj_λ + fee gate active in inference loop |
| T-131: ADR-0016 fee gate | ✅ net_edge = gross_edge - kalshi_fee in both run_pregame.py and run_paper_trade.py; paper_trader.py backward compat |
| ADR-0015 artifact | ✅ `03_DECISIONS/ADR-0015_opponent-adjusted-poisson-lambda.md` created |
| ADR-0016 artifact | ✅ `03_DECISIONS/ADR-0016_fee-adjusted-edge-gate.md` created |
| EXP-018 registration | ✅ `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-018_opp-adjusted-lambda-ev-test.md` created |
| DECISION_LOG entries (5) | ✅ Architecture finding, T-072 redesign, ADR-0015, ADR-0016, portfolio reset |
| GG-009 resolved in GOVERNANCE_GAP_LOG | ✅ Status updated; added to Resolved Gaps table |
| ADR index updated (DECISION_LOG) | ✅ ADR-0015 and ADR-0016 added |
| Portfolio reset | ✅ paper_portfolio.json: bankroll=$1,000, all zeroed; G1 archive created |
| VPS deployment | ✅ 5 files deployed; smoke test: parse_ticker_opponent('KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20') = 'SAS' ✅ |
| Git commit | ✅ `7596956` — 13 files, 655 insertions, 15 deletions |
| MEMORY_BANK.md update | ✅ Current state snapshot, ADR count, test count, portfolio, risks |
| TODO_NEXT.md update | ✅ SESSION 30 COMPLETED block; SESSION 28 open items marked done |
| Wakeup scheduled | ✅ ScheduleWakeup clamped to 3600s max; will chain-reschedule until after PIPE-02 fires Jun 5 22:00 UTC |

---

## ONE THING PENDING

**G2 MC verify (Priority 1):** Wakeup is actively chaining every hour until PIPE-02 fires at 22:00 UTC Jun 5. When it fires:

1. `scp root@157.230.91.33:/opt/prediction-market-bot/logs/pregame_20260605.json data/`
2. Verify `logs/team_stats_cache_2026-06-05.json` exists on VPS (confirms adj_λ TeamStatsStore ran in PIPE-02)
3. Run MC: `PYTHONPATH=src .venv/bin/python3 scripts/run_monte_carlo.py --date 2026-06-05`
4. Check: (a) opp_adj_factor < 1.0 for players facing Knicks defense; (b) gross_edge vs net_edge distribution; (c) total bets and stake vs G1

**T4 process status on VPS:** Verify T4 is running before G2 cron: `ssh root@157.230.91.33 "ps aux | grep t4_live"`. If dead, restart: `ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "set -a; source .env; set +a; source venv/bin/activate; PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" > /dev/null 2>&1 &'`

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (clean slate — reset 2026-06-04)
- Open: 0 positions
- Closed/Resolved: 0 (SESSION 30 clean slate) | G1 archive at `paper_portfolio_g1_archive.json`
- G6 evidence: 0 unique markets on adj_λ model; clean window starts Finals Game 2

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:55 UTC  — PIPE-02 inference (run_pregame.py) — NOW includes TeamStatsStore build + adj_λ
22:00 UTC  — PIPE-03 early (paper bets — adj_λ + fee gate ACTIVE)
01:30 UTC  — PIPE-03 late (paper bets)
06:00 UTC  — PIPE-03R resolve-only
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (APR-0017: ≥66 bets + ≥5 nights + EXP-017 Part B CONFIRMED)
3. **EXP-018 must resolve before EXP-017 re-run is meaningful** — adj_λ is the fix hypothesis; until EXP-018 confirms EV > 0, the commercial question (GG-004) remains OPEN
4. **LR model is logged-only** — do not design fixes that target the LR model expecting them to affect bet behavior
5. **adj_λ LEAGUE_AVG_PTS_ALLOWED = 113.0** — update at 2026-27 season rollover via DECISION_LOG entry (no new ADR required)

---

## ⚙️ DECISION AUDIT

Governance scan: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → **CLEAN** (0 matches)

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| ADR-0015 (new) | N/A (ADR, not design doc) | Entry 3 written | ✅ |
| ADR-0016 (new) | N/A (ADR, not design doc) | Entry 4 written | ✅ |
| EXP-018 (new) | N/A (experiment log) | Registered | ✅ |
| game_state_model.py | N/A (source code) | Entries 1+2+3 cover | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260604_1500.md.
# Priority: G2 MC verify — check if pregame_20260605.json exists on VPS (PIPE-02 fires 22:00 UTC Jun 5).
# If it does: scp + run MC. If not: verify VPS cron and T4 process status."
```
