# Session Handoff — 2026-06-03T20:00Z

**Trigger:** Context window near limit — session-end protocol invoked
**Last commit:** `8321900` (main) — pushed to GitHub + VPS (SESSION 25; no new commit this session)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (no code changes this session)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-02 21:55 UTC, PIPE-03 22:00 UTC)
- **Paper bets:** 0 resolved post-G6-reset — G6 gate: accumulating (Finals G1 tonight)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

None — implementation-only session. No threshold changes, no ADR changes, no gate modifications.

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| `scripts/poll_and_resolve_g1.py` created | ✅ New automation script: polls ESPN scoreboard every 60–90s, triggers T-109 (run_resolve_local.py + fetch_kalshi_prices.py --portfolio) at STATUS_FINAL. Fallback at 07:30 UTC next day. Currently running PID 5865 + caffeinate PID 5867. |
| Fallback datetime bug fixed | ✅ Initial version used same-day time-of-day check — triggered at 19:15 UTC when 07:30 UTC already past. Fixed to `_compute_fallback_dt()`: always computes NEXT future 07:30 UTC. Restarted as PID 5478, then restarted again with caffeinate as PID 5865. |
| caffeinate -s added | ✅ nohup alone pauses on Mac lid close. Restarted script under `caffeinate -s` to prevent system sleep. |
| tmpfs ENOSPC diagnosed | ✅ Root cause: Claude Code internal task output pipe at `/private/tmp/claude-501/...UUID.../tasks/`. Not a real disk issue (82GB free). Workaround: `find | xargs grep`. Permanent fix pending: `export CLAUDE_CODE_TMPDIR="/Users/earlignacio/.claude/tmp"` in `~/.zshrc` (operator action). |
| Pre-game hygiene confirmed | ✅ VPS T4 PID 154947 STATUS_SCHEDULED; cron PIPE-02 21:55 / PIPE-03 22:00 UTC; portfolio $1,000.00 / 0 open; fee annotation live; pool_isolated live. |
| T-132 registered | ✅ CHANGE_CONTROL.md has `decisions_logged: false` — governance debt registered. Low priority; resolve before any session modifying that document. |

---

## ONE THING PENDING

**`scripts/poll_and_resolve_g1.py` is running (PID 5865 + caffeinate PID 5867) and will auto-trigger T-109 tonight when Finals Game 1 ends.** No operator action needed for resolution. Check `logs/auto_resolve_g1.log` after the game to confirm exit code 0. If exit code non-zero, run T-109 manually:
```
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio
```

---

## Current Paper Portfolio

- **Bankroll:** $1,000.00 (0% drawdown, 0 open bets)
- **Open:** None
- **Closed/Resolved:** 0 post-G6-reset | G6 gate: accumulating (Finals G1 tonight)
- **Note:** Portfolio was reset to $1,000 clean before Finals G1. Tonight's T1 cron (22:00 UTC) + T4 (PID 154947, auto-activates at tip-off ~00:30 UTC Jun 4) will open positions.

---

## Active Cron on VPS (157.230.91.33)

```
21:55 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, Finals tip-off window)
01:25 UTC  — PIPE-02 late
01:30 UTC  — PIPE-03 late
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py — VPS; will get 0 resolutions due to 403)
```
**Resolution runs locally via poll script** (PID 5865).

---

## Active Local Process

```
PID 5865 — python3 scripts/poll_and_resolve_g1.py  (polling ESPN, fallback 2026-06-04T07:30Z)
PID 5867 — caffeinate -s  (prevents Mac sleep)
Output:  logs/auto_resolve_g1.log
```

---

## Key Constraints to Remember

1. No live capital until G6 (APR-0017: ≥66 resolved bets + ≥5 game nights + EXP-017 confirmed + slope criteria)
2. T-131 (fee-adjusted edge ADR) is HIGH priority before G6 — GG-009 still OPEN
3. CHANGE_CONTROL.md has `decisions_logged: false` (T-132, LOW priority)

---

## ⚙️ DECISION AUDIT

**Governance scan result:** `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` — `decisions_logged: false` (unresolved, T-132 registered)

| Document | Decisions logged | DECISION_LOG entries | Status |
|----------|-----------------|----------------------|--------|
| scripts/poll_and_resolve_g1.py (new) | N/A — script, not canonical doc | None required (implementation, no threshold changes) | ✅ |
| CHANGE_CONTROL.md | false | Not this session (file not modified) | T-132 registered |

---

## Post-Game Next Session (after T-109 auto-run completes)

1. Check `logs/auto_resolve_g1.log` — confirm combined exit code 0
2. Run `run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` on VPS — T4 calibration
3. Review Finals G1 outcomes: bankroll, P&L, position breakdown
4. Evaluate portfolio reset before Finals G2 (Jun 5 PDT, cron 21:55 UTC)
5. Run Monte Carlo before Finals G2 cron: `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`
6. Draft T-131 ADR (fee-adjusted edge gate — GG-009)

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_2000.md. 
# Check logs/auto_resolve_g1.log to confirm T-109 ran successfully. 
# Then run post-game T4 calibration."
```
