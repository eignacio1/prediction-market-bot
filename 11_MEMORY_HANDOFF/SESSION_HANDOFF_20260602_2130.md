# Session Handoff — 2026-06-02T21:30Z

**Trigger:** Operator-initiated session end (context nearing limit)  
**Last commit:** `34b6fd9` (main) — pushed to GitHub. VPS deployment PENDING (required before Finals G1 tip-off 00:30 UTC Jun 4).

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (VPS state as of SESSION 19 commit `706264b`; no test files changed this session)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — screen `140907.t4_live` running commit `706264b`. Must pull `34b6fd9` before Finals G1.
- **Paper bets:** 11 open, 0 resolved — G6 gate requires ≥66 resolved (APR-0017)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|---------------------|-------|
| ADR-0013: T4 band budget architecture accepted | Standard Kelly on full bankroll ($618) → $6.18/bet × ~150 fires/game = capital exhaustion. Fix: Kelly operates on `t4_band_budget = bankroll × 0.60 × T4_BAND_WEIGHT`. Scales correctly at any capital ceiling. Two stubs (T4_BAND_WEIGHT=0.10, T4_EXPECTED_TOTAL_EDGE=5.0) pending G1 PAPER_T4_VIRTUAL calibration. | `03_DECISIONS/ADR-0013_t4-throughput-capital-budget.md`; DECISION_LOG SESSION 20 entry | DS |
| ~1000 bet evaluations per game is the design throughput floor | Bands are not pre-decided time-horizon thresholds. Model computation determines which decision-tree bucket a bet routes to. Architecture, sizing, and kill switches must all be designed to this scale. Any implementation that only makes sense at 10–20 bets/game night is architecturally wrong. | `CLAUDE.md` §Execution timing + Hard Rule 9 | DS |
| Decision tree mechanics expansion registered as pre-T4-ACTIVE requirement | Each quantitative computation (model inputs, probability estimates, Kelly variant) must be formally specified per bucket (T1–T5). Cannot activate T4 without this specification. Registered as T-130. | `04_EXECUTION/TODO_NEXT.md` T-130 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| KI-026 — T4 band budget architecture (ADR-0013) | ✅ `run_t4_live.py` updated: imports `RESERVE_MANDATE_PCT`, `T4_BAND_WEIGHT=0.10` stub, `T4_EXPECTED_TOTAL_EDGE=5.0` stub, `_compute_t4_band_budget()`, `_make_engines(t4_band_budget)`, `_run_cycle()` returns `t4_deployed_usd`. Two-tier kill switch. Syntax OK. Commit `a60b949`. |
| ADR-0013 written | ✅ `03_DECISIONS/ADR-0013_t4-throughput-capital-budget.md` — architecture, scaling table, two-tier kill switch, VIRTUAL vs ACTIVE, calibration procedure, 5 activation gates, rejected alternatives, operator sign-off table. |
| `scripts/run_t4_budget_sim.py` written and verified | ✅ Parametric (pre-G1) + empirical (`--from-log`, post-G1) modes. Verified at $618 bankroll: band_budget=$37.08, avg 37 minimum-bets ($1 floor), exhausts at cycle 125/200 (63% into game). Sensitivity table: band_weight=0.20 → only 6.6% exhaustion rate. |
| T1 Monte Carlo pre-G1 verification | ✅ `scripts/run_monte_carlo.py --label pre-G1-ADR-0013` clean — T1 unaffected. |
| DECISION_LOG ADR-0013 entry | ✅ ADR Index row added + Notable Judgment Calls entry with full derivation. |
| CLAUDE.md — design throughput framing | ✅ Execution timing section rewritten: bands are model-computation routing outputs, not pre-scheduled thresholds. Hard Rule 9 added: ~1000 evaluations/game is the design throughput floor. Commit `34b6fd9`. |
| TODO_NEXT.md, MEMORY_BANK.md | ✅ SESSION 20 completed/open sections written. VPS deployment and post-G1 calibration as top-priority open items. |

---

## ONE THING PENDING

**Deploy to VPS before Finals G1 tip-off (00:30 UTC Jun 4 = 8:30 PM EDT Jun 3).**

```bash
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && git pull'
# Screen 140907.t4_live picks up new code on next poll cycle
# Verify: tail -f /opt/prediction-market-bot/logs/t4_live.log
# Look for: "T4 band budget: $37.08  (T4_BAND_WEIGHT=0.20 × deployable)  [ADR-0013"
```

If screen has died: `screen -S t4_live -dm bash -c 'BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py'`

After G1 completes: `PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl --bankroll [current]` to calibrate T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE stubs before G2.

---

## Current Paper Portfolio

- Bankroll: $618.03 (38.2% drawdown from $1,000 start — deployed T1 bets, not realized losses)
- Open: 11 positions (Finals G1 pregame bets — resolve after game tonight Jun 3 PDT)
- Closed/Resolved: 0 | G6 gate: 0/66 resolved

---

## Active Cron on VPS (157.230.91.33)

```
55 21 UTC  — PIPE-02 early (run_pregame.py)
00 22 UTC  — PIPE-03 early (paper bets)
25 01 UTC  — PIPE-02 late
30 01 UTC  — PIPE-03 late
00 06 UTC  — PIPE-03R resolve-only (run_resolve.py)
```

T4 live: screen `140907.t4_live` (continuous; polls on STATUS_IN_PROGRESS; wakes at tip-off)

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (≥66 resolved paper bets + EXP-017 Part B confirmed + ≥5 game nights — APR-0017)
3. VPS must be running commit `34b6fd9` before Finals G1 tip-off tonight
4. T4_BAND_WEIGHT=0.10 and T4_EXPECTED_TOTAL_EDGE=5.0 are STUBS — do not activate T4 ACTIVE until calibrated from G1 data and operator signs ADR-0013 calibration block
5. EXP-017 Part B (n=2, floor=66) is the binding G6 constraint — commercial EV vs real Kalshi prices unproven

---

## ⚙️ DECISION AUDIT

Governance scan: **CLEAN** — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `ADR-0013_t4-throughput-capital-budget.md` | `true` (set at creation) | SESSION 20 entry in Notable Judgment Calls | ✅ |
| `CLAUDE.md` | N/A (not a decisions_logged artifact) | Hard Rule 9 + framing permanent in document | ✅ |
| `run_t4_live.py` | N/A (code file) | ADR-0013 decision entry covers all code decisions | ✅ |
| `scripts/run_t4_budget_sim.py` | N/A (code file) | No separate decisions — governed by ADR-0013 | ✅ |

---

## New Task Registered This Session

**T-130 — Decision tree mechanics specification per band (pre-T4-ACTIVE requirement)**  
Each T1–T5 bucket requires a formal specification: what model inputs are used, what probability estimate method applies, what Kelly variant governs sizing, what kill switch tier applies. The CLAUDE.md framing establishes *that* computation determines routing; T-130 is the task to specify *what* that computation is per bucket. Required before T4 ACTIVE. Longer time horizon = more complex decision tree — this gradient must be formally documented before Phase 8.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260602_2130.md.
# VPS needs git pull before Finals G1 tip-off (00:30 UTC Jun 4).
# After G1: run calibration sim, then T-130 decision tree mechanics spec."
```
