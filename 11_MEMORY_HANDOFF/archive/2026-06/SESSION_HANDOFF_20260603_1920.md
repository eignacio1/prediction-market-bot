# Session Handoff — 2026-06-03T19:20Z

**Trigger:** Operator-initiated — session end
**Last commit:** `8049acd` (main) — SESSION 26 handoff; SESSION 27 changes uncommitted (scripts/ only)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (no src/ changes this session)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; T4 PID 154947 active (LIVE during Finals G1)
- **Paper bets:** 0 resolved (G6 gate: ≥66 resolved bets + ≥5 game nights — APR-0017)
- **Game 1 status:** LIVE (tip-off ~00:30 UTC Jun 4); 1416 T4 positions open, $499.95 deployed

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

None — implementation-only session. All work was tooling (`scripts/live_terminal.py`). No src/ changes, no threshold changes, no governance decisions.

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Bloomberg terminal rewrite | ✅ `scripts/live_terminal.py` — complete rewrite as multi-panel Bloomberg-style TUI. 8 independent panels with individual curses pads and scroll state. 2-column layout (56%/44% split). Tab/Shift+Tab focus cycling; focused panel highlighted cyan with `↕NN%` scroll indicator. Arrow/PgUp/PgDn/Home/End scroll within focused panel. Layout adapts to terminal size dynamically. Atomic render via `curses.doupdate()`. |
| Curses ordering bug fix | ✅ Critical fix: `draw_panel()` was calling `ps.pad.noutrefresh()` before `stdscr.noutrefresh()`. Since stdscr ran last, its blank content areas overwrote the pad content in the virtual screen buffer, causing all panels to appear empty despite data flowing correctly. Fix: separated `refresh_pad()` into its own pass called AFTER `stdscr.noutrefresh()`. Borders on stdscr, content on pads, pads always win. |
| Data fetch verified | ✅ Confirmed `--once` debug mode shows 1416 T4 live positions from VPS. Portfolio: $1,000 bankroll, 3 T1 bets today, data flowing correctly via ControlMaster SSH. |

---

## ONE THING PENDING

**Game 1 is LIVE right now.** `scripts/poll_and_resolve_g1.py` (PID 5865, caffeinate) is running and will auto-trigger T-109 (resolve + price sync) when ESPN reports STATUS_FINAL. Expected game end ~02:30 UTC Jun 4. Fallback at 2026-06-04T07:30Z.

After resolution fires:
1. Check VPS: `ssh root@157.230.91.33 "tail -30 /opt/prediction-market-bot/logs/paper_late_cron.log"`
2. Run T4 calibration: `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && BOT_ENV=paper PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl"` — to replace stubs in `run_t4_live.py`
3. Portfolio reset decision (see TODO_NEXT.md)
4. Finals Game 2 MC verify before 2:55 PM PDT Jun 5

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (0% drawdown)
- Open: 1416 T4 positions ($499.95 deployed) + 3 T1 positions
- Closed/Resolved: 0
- G6 gate progress: 0/66 resolved bets (0/5 game nights) — APR-0017

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

**Running outside cron:** `scripts/poll_and_resolve_g1.py` (PID 5865) — auto-resolve at STATUS_FINAL; fallback 2026-06-04T07:30Z.

**T4 process:** nohup PID 154947 — watching Finals G1, PAPER_T4_FLAT_SIZING=true, PAPER_T4_VIRTUAL=false, pool=$500.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. G6 gate = APR-0017: ≥66 resolved bets + ≥5 game nights + EXP-017 Part B confirmed. Bet count is NOT the binding constraint. GG-004 (EXP-017) is the binding constraint.
3. T-131 ADR required before G6 EXP-017 re-run — taker fee not in MIN_EDGE gate (GG-009 OPEN)
4. T4 stubs not yet replaced — calibrate from G1 audit_t4.jsonl after game ends

---

## ⚙️ DECISION AUDIT

Governance scan: clean — no `decisions_logged: false` documents created or modified this session. All changes were to `scripts/live_terminal.py` (new file, no decisions_logged header required for scripts).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `scripts/live_terminal.py` | N/A (script, not governance doc) | None needed | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_1920.md.
# Game 1 just ended / is pending resolve. Run post-G1 protocol:
# 1) Check poll_and_resolve_g1.py triggered; 2) T4 calibration; 3) portfolio reset decision."
```

---

## NEXT SESSION PRIMER

Game 1 resolve should have auto-triggered via `scripts/poll_and_resolve_g1.py` (PID 5865). Start by checking `/opt/prediction-market-bot/logs/paper_late_cron.log` for resolve confirmation and reviewing the portfolio P&L. Then run T4 calibration (`run_t4_budget_sim.py --from-log logs/audit_t4.jsonl`) to replace the two stubs in `run_t4_live.py` and redeploy before Finals Game 2. Read `04_EXECUTION/TODO_NEXT.md` — the open items table for SESSION 22/23 has the precise commands.
