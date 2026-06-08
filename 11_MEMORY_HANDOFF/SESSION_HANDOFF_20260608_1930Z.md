# Session Handoff — 2026-06-08T19:30Z

**Trigger:** Operator-initiated (session wrap before G3 tip-off)
**Last commit:** `da793e0` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 745/745 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (all PIPE-02/03/06/07 active)
- **Paper bets:** 35/30 resolved — G6 30-bet threshold MET; full gate requires ≥66 bets + ≥5 nights + EXP-017 CONFIRMED (APR-0017)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T-140 automated via `scripts/run_t140_check.py` at 21:25 UTC cron | GHA timing ambiguity makes manual pre-upload unreliable; script rebuilds from ESPN if cache < 1000 bytes; manual T-140 check retired | DECISION_LOG.md [SESSION 38 PART 2] | DS |
| CLAUDE.md kill switch threshold corrected: 20%/~$192 → 15%/~$144 | `MAX_DAILY_LOSS_PCT = 0.15` in `risk.py:90` and `run_monte_carlo.py:48`; CLAUDE.md had stale value from prior bankroll update | CLAUDE.md:167; DECISION_LOG.md [SESSION 38 PART 2] | DS |
| Poisson CDF confirmed as primary model; LR+Platt (47 PRF features) is shadow only | `run_pregame.py:370` uses `gross_edge = p_threshold - mid` where `p_threshold` is Poisson CDF; `p_estimate_lr` stored but not in decision path; 10x gap (LR=0.4629 vs Poisson=0.0485 for Wembanyama ≥35) indicates LR miscalibration at extreme thresholds; EXP-017 Part B is the validation gate for LR promotion | DECISION_LOG.md [SESSION 38 PART 2]; `run_pregame.py:366,385,389` | DS |
| SAC label corrected to SAS — De'Aaron Fox on Spurs (traded from Sacramento) | No code change; data was correct; team label in session commentary was wrong | Non-binding; no document change | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| G3 Monte Carlo assessment | ✅ 34 markets → 29 bets, EV=+$138.47, P(profit)=95.1%, kill switch risk 0.19%. Stale 9-player pregame (adj_λ not applied); tonight's 21:55 PIPE-02 will have ~20-25 players + adj_λ active. MC uses raw λ (gap noted). |
| T-140 automated | ✅ `scripts/run_t140_check.py` + cron.conf entry `25 21 * * *` + VPS deploy. Dry run: TSS cache OK 18,854 bytes. |
| CLAUDE.md kill switch correction | ✅ 20%/~$192 → 15%/~$144 at CLAUDE.md:167 |
| PAM/LR shadow model deep-dive | ✅ Confirmed `p_estimate` = Poisson CDF (primary), `p_estimate_lr` = LR+Platt shadow. DECISION_LOG entry written. |
| DECISION_LOG entry (SESSION 38 PART 2) | ✅ All three decisions above captured. |
| MEMORY_BANK, TODO_NEXT, PLAN updated | ✅ VPS HEAD da793e0; T-140 automated status; session header updated. |

---

## ONE THING PENDING

**Post-G3 resolution sequence** (run after ~06:00 UTC Jun 9 when game resolves):

1. `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py` — T1 resolution
2. `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` — T4 resolution (~1,000 positions)
3. `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git pull"` — deploy idempotency fix (safe after resolution clears open_positions)
4. Rerun EXP-017 Part B — target n≥66 (APR-0017 floor)
5. EXP-018: adj_λ + T3 signal analysis (first live adj_λ test)

---

## Current Paper Portfolio

- Bankroll: $958.99
- Open: 20 (2 resting + 18 `failed: HTTP 503` pre-fix)
- Closed/Resolved: 35 | G6 gate: 35/30 threshold MET (full gate: 66 + EXP-017 CONFIRMED)
- T4 pool: isolated in `paper_portfolio_t4.json` — running tonight

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check (deploy/healthcheck.sh)
21:25 UTC  — T-140 TSS cache check (scripts/run_t140_check.py) ← NEW
21:55 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
*/15 20-23 — PIPE-06 T3 momentum scan
*/15 0-3   — PIPE-06 T3 momentum scan (midnight crossing)
01:25 UTC  — PIPE-02 late inference
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
23:00 UTC  — PIPE-07 T4 in-play (6h timeout; paper_portfolio_t4.json)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints to Remember

1. **Idempotency fix NOT yet on VPS** — commit `341ab97` local only; deploy post-G3 resolution (step 3 above)
2. **18 open tickers blocked** tonight — failed HTTP 503 positions from 01:25 UTC run; ~18 fewer bets than MC predicts
3. **MC uses raw λ, not adj_λ** — `run_monte_carlo.py` maps `lam` to `pts_l10_mean`; EV is a lower bound when adj_λ > raw λ
4. **No live capital until G6** — APR-0017 gates: EXP-017 Part B CONFIRMED (n≥66) + ≥5 game nights + DS sign-off
5. **`deploy/cron.conf` is canonical** — any manual VPS crontab edit must be committed immediately

---

## ⚙️ DECISION AUDIT

**Governance scan:** ENOSPC on tmp filesystem (recurring harness issue — main disk 77GB free). No new `decisions_logged: false` documents created or modified this session.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `scripts/run_t140_check.py` | N/A (new script, not governance doc) | SESSION 38 PART 2 entry | ✅ |
| `deploy/cron.conf` | N/A (config file, not governance doc) | SESSION 38 PART 2 entry | ✅ |
| `CLAUDE.md` | N/A (session rules, not governance doc) | SESSION 38 PART 2 entry | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260608_1930Z.md, confirm 745 tests"
# Post-G3 first action: run run_resolve_local.py, then run_t4_resolve_local.py, then deploy idempotency fix (git pull on VPS)
```
