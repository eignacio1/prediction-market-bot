# Session Handoff — 2026-06-27T17:22Z

**Trigger:** Operator-initiated (session-end after context compaction close-out)
**Last commit:** `35e868b` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE — MLB paper trading arm LIVE (MLB-G1 gate CLOSED)
- **Tests:** 2044/2044 passing (7 skipped)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — 6 MLB crons + NBA crons running
- **Paper bets:** 158/30 resolved (NBA; G6 gate cleared on count, NOT on P&L — EXP-017 GG-004 open)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

*S90 was the substantive session; this terminal window was documentation close-out after context compaction.*

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| MLB-G1 gate CLOSED — 6 MLB crons enabled; T4 MLB + calib monitor explicitly deferred | All 8 institutional tasks (T-192–T-199) complete. T4 deferred per GG-007 (uncalibrated constants). Calib monitor deferred per GG-044 (no closed positions + wrong baselines). | ADR-0032 (`03_DECISIONS/ADR-0032_mlb-g1-gate-close.md`) | DS |
| `mark_aged_open()` in-place tagging — positions stay in `open_positions`, NOT moved | Moving a position out of `open_positions` would credit capital back to free cash; bankroll invariant broken. `_ledger_bankroll()` derives `open_cost` by summing `open_positions[*]["size_usd"]`. | DECISION_LOG SESSION 90 T-194 entry | DS |
| Permissive-with-logging pattern for silent exception handlers | `_is_mlb_game_in_progress()` and `_fetch_live_game_pks()` are contamination guards — false positives (thinking a game is in progress when API fails) are SAFE. Raising on API failure would be wrong. Optional logger parameter means existing callers without a logger are unchanged. | DECISION_LOG SESSION 90 T-195 entry | DS |
| GG-043 deferred to pre-MLB-G6 | MLB Kelly fraction 0.10 inherited from NBA without MLB derivation. LOW risk while paper only. Revisit after ≥30 MLB resolved bets. | GG-043 in GOVERNANCE_GAP_LOG.md | DS |
| GG-044 deferred to post-first-MLB-resolutions | C7 drift baselines (Brier=0.2416, ECE=0.0247) are NBA G4 test set values — wrong sport. Monitor not enabled. Revisit when first MLB bets resolve. | GG-044 in GOVERNANCE_GAP_LOG.md | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-194 — Resolution age-out | ✅ `PaperTrader.mark_aged_open()` + `run_resolve_mlb.py` 48h detection; 15 tests |
| T-195 — Silent fallback audit | ✅ Optional-logger C6 WARNING in `_is_mlb_game_in_progress()` + `_fetch_live_game_pks()`; 17 tests |
| T-196 — Cron timing comment fix | ✅ `run_mlb_paper_trade.py` docstring + inline comment corrected 03:00→11:00 UTC |
| T-197 — MLB kill switch drill | ✅ APR-0023 written; halt_time_ms=0.116ms; SLA PASS (NFR-03 ≤60,000ms) |
| T-198 — Governance gaps | ✅ GG-043 + GG-044 registered in GOVERNANCE_GAP_LOG.md |
| T-199 — Gate close + VPS deploy | ✅ 2044 tests; 6 MLB crons enabled; VPS deployed; ADR-0032 ACCEPTED |
| MEMORY_BANK.md S90 close-out | ✅ `Last reviewed` updated to S90 CLOSE with full MLB-G1 description |
| DECISION_LOG.md S90 close-out | ✅ S90 header + ADR-0032 in ADR Index + 3 judgment call entries |
| TODO_NEXT.md S90 close-out | ✅ MLB-G1 gate CLOSED; all 8 tasks marked COMPLETE |
| PLAN.md S90 close-out | ✅ `Last reviewed` updated to S90 CLOSE |
| Commit + VPS deploy | ✅ `35e868b` pushed; VPS fast-forwarded clean |

---

## ONE THING PENDING

**Monitor first MLB paper bets.** PIPE-05 T1 runs at 11:00 UTC daily (`run_mlb_paper_trade.py`). The MLB arm has been live since cron re-enable at S90 close but has placed 0 bets (MLB bankroll $1,000, 0 open, 0 closed). Check VPS logs at next session:

```bash
ssh prediction-market-vps "tail -50 /opt/prediction-market-bot/logs/audit_mlb.jsonl | python3 -c \"import sys,json; [print(json.loads(l)['event_type'], json.loads(l).get('ticker','')) for l in sys.stdin if l.strip()]\""
```

If bets are being placed, first resolution comes via PIPE-05R at 06:30 UTC (typically 24–48h after bet). GG-043/GG-044 resolution timeline starts after first resolved bets.

---

## Current Paper Portfolio

**NBA (halted — drawdown kill switch):**
- Bankroll: $751.10 | P&L: −$248.90 (24.9% drawdown > 20% kill switch threshold)
- Open: 0 | Resolved: 158 | Kill switch: ACTIVE
- G6 gate: count CLEARED (158 ≥ 30); P&L gate FAILING (EXP-017 GG-004 open)

**MLB (active):**
- Bankroll: $1,000 | P&L: $0.00 | Open: 0 | Resolved: 0
- PIPE-05 T1 first bets: expected at next 11:00 UTC run

---

## Active Cron on VPS (157.230.91.33)

```
# NBA (halted by kill switch — bets not firing)
0 21 * * *   — PIPE-01 health check
30 21 * * *  — PIPE-02 NBA pregame context
0 22 * * *   — PIPE-03 NBA paper bets (T1)
30 1 * * *   — PIPE-03 NBA paper bets (late)
0 6 * * *    — PIPE-03R NBA resolve
10 14 * * 1  — PIPE-03C NBA calibration monitor
0 23 * * *   — PIPE-07 NBA T4 (dark — NBA off-season)

# MLB (ACTIVE — MLB-G1 gate CLOSED 2026-06-27)
30 22 * * *  — PIPE-05FX MLB feature refresh
30 16 * * *  — PIPE-06pre MLB pregame context
0 11 * * *   — PIPE-05 MLB T1 paper bets
30 19 * * *  — PIPE-05.5 MLB T2 lineup overlay
30 6 * * *   — PIPE-05R MLB resolve
*/15 20-23 * * *  — T3 MLB pre-tip scan
*/15 0-3 * * *    — T3 MLB pre-tip scan (overnight)
# NOT ENABLED: T4 MLB (GG-007), MLB calib monitor (GG-044)
```

---

## Key Constraints to Remember

1. **NBA is halted:** drawdown kill switch fires at 24.9% (> 20% `MAX_DRAWDOWN_PCT`). Halted since S63. Do NOT disable kill switch without DS sign-off and ADR.
2. **No live capital until G6:** 30 resolved paper bets (count met via NBA) + **positive P&L** + DS sign-off (APR-0017/APR-0019/ADR-0028). P&L gate failing. EXP-017 (GG-004) is the binding blocker.
3. **MLB book is fresh $1,000 paper-only pool** (`logs/paper_portfolio_mlb.json`). Separate from NBA. No commingling.
4. **GG-004 (EXP-017) is the G6 blocker** — edge is anti-predictive vs Kalshi market prices (post-calibration). Requires adequate sample at EXP-017 CONFIRMED_POSITIVE. ADR-0024 structural adequacy: n≥500 unique markets OR ≥2 sports each n≥150.
5. **VPS MLB Stats API:** historical seasons (2024/2025) blocked via HTTP 406. Feature matrix generated locally, scp'd to VPS. Current feature CSV covers 2026 season only.
6. **Work wifi blocks Kalshi API** — use any other network for live Kalshi calls.

---

## ⚙️ DECISION AUDIT

Governance scan: **CLEAN** — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| ADR-0032 | N/A (ADR format — no decisions_logged field) | S90 ADR-0032 entry in ADR Index | ✅ |
| APR-0023 | N/A (APR format) | S90 kill switch drill entry | ✅ |
| GOVERNANCE_GAP_LOG.md | N/A | GG-043 + GG-044 entries | ✅ |
| DECISION_LOG.md | N/A | S90 header + ADR-0032 ADR Index + 3 judgment call entries | ✅ |
| TODO_NEXT.md | N/A | MLB-G1 gate CLOSED; all 8 tasks COMPLETE | ✅ |
| MEMORY_BANK.md | N/A | S90 CLOSE entry prepended | ✅ |
| PLAN.md | N/A | S90 CLOSE header updated | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and 11_MEMORY_HANDOFF/SESSION_HANDOFF_20260627_1722.md.
# MLB-G1 gate is closed. 6 MLB crons are live. MLB bankroll $1,000, 0 bets placed.
# Priority: monitor first MLB bets at 11:00 UTC, then check EXP-017 (GG-004) progress."
```
