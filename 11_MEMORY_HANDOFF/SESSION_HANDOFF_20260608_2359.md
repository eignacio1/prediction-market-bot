# Session Handoff — 2026-06-08T23:59Z

**Trigger:** Context window near limit — /session-end invoked by operator
**Last commit:** SESSION 40 (pending push) — main
**Session:** 40

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 783/783 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-07 T4 active for G3)
- **Paper bets:** 35 resolved (G2 only) — G6 gate: need ≥66 + ≥5 nights + GG-004 RESOLVED

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Remove `run_paper_trade.py:558` daily_loss accumulation | NO bets always have edge<0 by convention; line was silently accumulating all NO stake sizes as daily losses — not actual realized losses. Root source of truth is `portfolio.current_daily_loss` (set by `close_position()`). | DECISION_LOG.md SESSION 40 entry | DS |
| Post-game automation via `scripts/post_game_g3_resolve.sh` | Operator unavailable post-game; 5-step script (T1 resolve, T4 resolve, SCP portfolio, VPS git pull, EXP-017 Part B) scheduled via Mac crontab | scripts/post_game_g3_resolve.sh | EL |
| Design note: bets placed Jun 6 settling with losses on Jun 8 count toward Jun 8 kill switch | This is correct semantically (realized P&L date, not bet-placement date). But worth a formal DECISION_LOG note pre-G6 to ensure risk limits are calibrated to settlement semantics, not placement semantics. | DECISION_LOG.md SESSION 40 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-141: PIPE-03 false kill switch root cause + fix | ✅ `run_paper_trade.py:558` removed. All 783 tests pass. Root: NO bets have edge<0 by convention → all NO stakes were accumulated as daily losses → kill switch fired at $173.11 ($150 threshold). |
| T-142: live_terminal.py T4 log path | ✅ `t4_live.log` → `t4_live_cron.log` in both `_data_from_local()` and `_REMOTE_SCRIPT` |
| T-143: run_t4_live.py crash guard | ✅ try/except wrapper around main while loop body; kill switch remains outside guard |
| T-144: post_game_g3_resolve.sh | ✅ Created + scheduled via Mac crontab `0 23 8 6 *` (11 PM PDT Jun 8) |
| DECISION_LOG SESSION 40 entry | ✅ All three decisions written |

---

## ONE THING PENDING

**post_game_g3_resolve.sh fires tonight at 11 PM PDT.** If it runs cleanly: T1 positions resolved, T4 resolved, portfolio SCP'd, VPS pulls SESSION 40 fix, EXP-017 Part B rerun on n≥66. The next session opens to a clean resolved G3 portfolio and updated EXP-017 result.

If the crontab didn't fire (Mac was asleep or cron daemon not running): run manually:
```bash
bash "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets/scripts/post_game_g3_resolve.sh"
```

Then check:
1. `paper_portfolio.json` — resolved G3 positions listed
2. EXP-017 Part B output — is n≥66?
3. VPS: `git log --oneline -3` confirms SESSION 40 commits pulled

**G3 T1 bets: 0 placed** — kill switch blocked the 22:00 UTC window. The 01:30 UTC late window fired with the fix in place. Check if any late-window bets were placed.

---

## Current Paper Portfolio

- Bankroll: $915.97 (mid-G3, 21 open T4 positions)
- Open: 21 (T4: Anunoby, Bridges ×2, Towns + others from G3 game)
- Closed/Resolved: 35 (all G2) | Win: 28, Loss: 7, P&L: +$75.67 | Win rate: 80%
- G6 gate: 35/66 resolved bets (need ≥66 total + ≥5 game nights + GG-004 CONFIRMED)

---

## Active Cron on VPS (157.230.91.33)

```
21:25 UTC  — T-140 TSS cache check (run_t140_check.py)
21:55 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games) — FIXED (daily_loss bug)
01:25 UTC  — PIPE-02 late
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
20:30 UTC daily — GHA: TSS cache build + SCP to VPS
*/15 20-23 UTC — PIPE-06 T3 signal scan
*/15 0-3 UTC   — PIPE-06 T3 signal scan (midnight wrap)
23:00 UTC  — PIPE-07 T4 live paper trading (run_t4_live.py)
```

---

## Key Constraints to Remember

1. No live capital until G6 (≥66 resolved bets + ≥5 nights + GG-004 RESOLVED — APR-0017)
2. G3 T1 bets: 0 placed (22:00 UTC kill switch); 01:30 UTC late window had fix in place
3. `run_paper_trade.py` daily_loss fix: `edge < 0` stub REMOVED — do not re-add
4. T4 reads `t4_live_cron.log` — not `t4_live.log` (stale pre-cron file)
5. EXP-017 Part B (GG-004): directional positive at n=33; need n≥66 for APR-0017 floor

---

## ⚙️ DECISION AUDIT

**Step 1:** Governance scan ran this session: **CLEAN** — no `decisions_logged: false` documents.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| run_paper_trade.py (code) | N/A | SESSION 40 entry written | ✅ |
| live_terminal.py (code) | N/A | SESSION 40 entry written | ✅ |
| post_game_g3_resolve.sh (new script) | N/A | SESSION 40 entry written | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260608_2359.md.
#   Check if post_game_g3_resolve.sh ran. If yes: confirm G3 resolved, check EXP-017 Part B n≥66.
#   If not: run it manually. Tests: 783/783. Fix: daily_loss bug in run_paper_trade.py DEPLOYED."
```
