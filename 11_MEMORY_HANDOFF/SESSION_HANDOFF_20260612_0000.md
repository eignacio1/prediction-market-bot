# Session Handoff — 2026-06-12T00:00Z

**Trigger:** Operator-initiated (session wrap)
**Last commit:** `91058ed` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live
- **Tests:** 843/843 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running
- **Paper bets:** 117 resolved (post-G4 resolve) + 29 open (G5) — G6 gate: 117/30 count ✓, GG-004 OPEN (EV unvalidated vs Kalshi prices), GG-014 BREACHED (31% order failure rate)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-014 G6 gate status changed to BREACHED | G5 data: 9/29 = 31% demo order failures. T-138 (exponential backoff) was ineffective at 29-order burst. Pattern: first ~20 succeed (resting), last ~9 fail persistently. G6 live capital gate requires ≤5%. | GOVERNANCE_GAP_LOG.md — GG-014 resolution fields | DS |
| T-164 registered as HIGH PRE-G6 blocking task | Root cause of 31% failure rate unknown; throttled inter-order submission required before live capital deployment. T-138's 2s/4s/8s backoff is insufficient — need per-order sleep or batch-size cap. | TODO_NEXT.md — item 0c | EL |
| G5 YES-only gate confirmed not implemented | DS ruling required YES-only diagnostic mode for G5. Gate was not implemented before G5 cron fired. G5 placed 20 NO + 9 YES. Data still analyzable post-hoc YES/NO. | TODO_NEXT.md — item 0b | DS |
| G4 resolved via run_resolve_local.py (local nba_api) | VPS blocked by Akamai WAF for nba_api calls. Local Mac is not blocked. SCP pull→resolve→push workflow is the canonical G-resolve path until VPS WAF issue addressed. | Decision logged SESSION 48 entry, DECISION_LOG.md | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| G4 resolve (3 positions) | ✅ run_resolve_local.py — SCP pull from VPS, resolved locally, pushed back. VPS synced. |
| G5 Monte Carlo | ✅ 29 bets, $848.73 deployed, EV +$209.70 (+24.71% ROI), P(profit)=97.5%, kill switch risk 0.10% |
| GG-014 data update | ✅ G4: 0% failure (3/3), G5: 31% failure (9/29). T-164 registered. |
| Documentation sweep | ✅ DECISION_LOG.md, GOVERNANCE_GAP_LOG.md, TODO_NEXT.md, MEMORY_BANK.md, PLAN.md all updated to SESSION 48 state |

---

## ONE THING PENDING

**T-164 throttled order submission** is the blocking G6 task. 9/29 = 31% G5 order failures (GG-014 BREACHED, ≤5% required for G6). T-138 exponential backoff (2s/4s/8s) is proven ineffective at burst size. Root cause needs characterization (429 vs 503, rate limit window size), then implement per-order inter-submission sleep or batch cap in `run_paper_trade.py`.

**Before that:** After G5 game resolves on **June 13**, run:
```bash
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```
This pulls VPS portfolio, resolves 29 G5 positions using local nba_api, pushes back. Then proceed to T-164.

---

## Current Paper Portfolio

- Bankroll: $285.27 (71.5% drawdown from initial $1,000 — all deployed in G5 bets)
- Open: 29 G5 positions (game_date=2026-06-13, NBA Finals G5)
- Closed/Resolved: 117 | G6 gate: 117/30 count ✓ — blocked by GG-004 (EV unvalidated) and GG-014 (order failure rate)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
23:00 UTC  — PIPE-07 T4 in-play (run_t4_live.py)
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016) — additionally blocked by GG-004 (EV) and GG-014 (order failure rate)
3. nba_api blocked on VPS by Akamai WAF — all resolve operations must run locally via run_resolve_local.py
4. G5 game resolves June 13 — run resolve script before G6 planning begins

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found (only match is CHANGE_CONTROL.md definition line, not an actual document).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md | N/A (operational log, not a design doc) | SESSION 48 findings (GG-014, T-164) | ✅ |
| DECISION_LOG.md | N/A (the log itself) | SESSION 48 entry added | ✅ |
| TODO_NEXT.md | N/A (task list) | SESSION 48 COMPLETE block + T-164 | ✅ |
| MEMORY_BANK.md | N/A (state snapshot) | SESSION 48 update | ✅ |
| PLAN.md | N/A (plan doc) | SESSION 48 header update | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260612_0000.md, confirm 843 tests"
# After Jun 13 game: run G5 resolve first
# Then investigate T-164 (throttled order submission)
```
