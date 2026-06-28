# Session Handoff — 2026-06-28T07:55Z (SESSION 96)

**Trigger:** Context window near limit (auto-continuation from S95 context compaction)
**Last commit:** `586c9ca` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live
- **Tests:** 2110/2110 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — all MLB + NBA crons running
- **Paper bets:** MLB T4: 523 resolved / 143 open | T1 MLB: 0 (first run pending June 28 11:00 UTC) | NBA: dark period (0 active)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Kalshi KXMLBHIT tickers use market creation date (`DD` = game_date − 1 day) — NOT the game date | First validated against VPS T4 portfolio which correctly recorded game_date=2026-06-27 for same tickers that PIPE-05 parsed as June 26 | DECISION_LOG 2026-06-28 [SESSION 96 / T-205] | EL |
| GG-047 RESOLVED / GG-048 OPEN (MLB Stats API 406 errors need retry path) | June 27 morning PIPE-05R returned 406 for all players; June 28 recovered; pattern may recur | GOVERNANCE_GAP_LOG.md GG-047/GG-048 | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **ARE WE COMPROMISED? Q1–Q6** | ✅ COMPLETE — governance scan clean; GG-048 registered for Q6 concern |
| **T-205: T1 MLB ticker off-by-one** | ✅ COMPLETE — `+timedelta(days=1)` fix in `_ticker_to_game_date`; 3 test files updated; 2110/2110; commit `586c9ca`; VPS deployed before June 28 11:00 UTC |
| **GG-047 + GG-048 registered** | ✅ COMPLETE — GG-047 RESOLVED (ticker fix), GG-048 OPEN LOW (API 406 retry) |
| **DECISION_LOG entry for T-205** | ✅ COMPLETE — Kalshi convention + fix methodology logged |
| **TODO_NEXT.md updated** | ✅ COMPLETE — T-205 marked complete, T-206 escalated to HIGH (condition met: 523 resolved T4 bets), T-207 registered |
| **MEMORY_BANK.md updated** | ✅ COMPLETE — S96 delta added, last reviewed updated |

---

## ONE THING PENDING

**Monitor the June 28 11:00 UTC PIPE-05 run (first T1 MLB bets).**

The T-205 fix deployed at 07:48 UTC on June 28. PIPE-05 fires at 11:00 UTC (3h13m from session close). Check `logs/paper_mlb_cron.log` on VPS:
- If `"> 0 players in live MLB markets"` and bets placed → T-205 fix confirmed working
- If still `"0 players"` → another matching failure exists; examine the exact player name format in the log

Also: **T4 has 143 still-open positions** (June 27 game players within 48h grace as of 06:30 UTC run). PIPE-05R at 06:30 UTC June 29 will resolve them. Total T4 P&L will become known then.

---

## Current Paper Portfolio

**NBA (dark period):**
- Bankroll: $958.99 | Drawdown: −$248.90 / −20.6% from peak
- Open: 0 | Closed: 158 | G6 gate: NOT CLEARED (NBA, negative P&L)

**MLB T1/T2 pool:**
- Bankroll: $1,000.00 | 0 open | 0 closed (T-205 prevented all bets until today)
- First T1 bets: June 28 11:00 UTC (pending)

**MLB T4 pool:**
- Bankroll: $1,000.00 (gross, before paper P&L)
- T4 paper P&L: **+$87.91** | Win rate: **53.7%** (523 W=281/L=242)
- Open: 143 (June 27 game players — resolving June 29 morning)
- Total positions: 666

---

## Active Cron on VPS (157.230.91.33)

```
NBA (dark period — no bets):
  Inactive until Oct 2026 (NBA 26-27 season)

MLB:
  00:30 UTC daily  — PIPE-05FX feature refresh (run_mlb_feature_refresh.py)
  06:30 UTC daily  — PIPE-05R resolution (run_resolve_mlb.py)
  11:00 UTC daily  — PIPE-05 T1 betting (run_mlb_paper_trade.py)
  16:30 UTC daily  — PIPE-06pre pregame context (run_mlb_pregame.py)
  19:30 UTC daily  — PIPE-05.5 T2 lineup overlay (run_t2_mlb_sameday.py)
  */15 20-23 UTC   — PIPE-06 T3 momentum scan (run_t3_mlb_pretip.py)
  */15 0-3 UTC     — PIPE-06 T3 momentum scan (run_t3_mlb_pretip.py)
  systemd 24/7     — T4 MLB live (t4-mlb.service, Restart=on-failure)
```

---

## Key Constraints to Remember

1. G6 gate: 30 resolved paper bets with positive P&L — APR-0016. NBA: NOT cleared (negative P&L). MLB: counting from today.
2. GG-004 (EXP-017 MLB commercial validation) — still OPEN. Model vs historical rates is not the same as model vs Kalshi market prices.
3. The T4 53.7% win rate is early signal (paper, 523 bets, mip≈0.21 break-even). Not a commercial validation claim.
4. MLB T1 bets fire today (June 28 11:00 UTC) for the first time. Monitor.

---

## ⚙️ DECISION AUDIT

**Step 1 scan result:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_mlb_paper_trade.py` (modified) | N/A (source file, not decision doc) | SESSION 96 T-205 entry written | ✅ |
| `GOVERNANCE_GAP_LOG.md` (modified) | N/A | GG-047 + GG-048 added | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_S96_CLOSE.md, then check logs/paper_mlb_cron.log on VPS for the June 28 11:00 UTC T1 run result. T-206 (EXP-T4-01) is the next active task."
```

---

## Next Session Primer

Check VPS `logs/paper_mlb_cron.log` first — confirms T-205 fix worked (should show >0 players matched). If confirmed, move to T-206: run EXP-T4-01 on the 523 resolved T4 bets (win rate by mip bucket, edge monotonicity, net EV after 7% fee). T-207 (API 406 retry) is LOW priority — only escalate if PIPE-05R shows another full-406 run.
