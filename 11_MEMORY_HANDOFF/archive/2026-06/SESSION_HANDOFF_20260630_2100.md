# Session Handoff — 2026-06-30T21:00Z

**Trigger:** Context window limit / operator-initiated session-end
**Last commit:** `bbaf86a` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live on VPS
- **Tests:** 2109/2109 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — all MLB crons running; t4-mlb systemd service ACTIVE
- **Paper bets:** G6 gate governed by EXP-017 (GG-004 OPEN) — not yet met

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-052 fix: `cycle_start_at = snapshot_fetched_at` | Kalshi paginated fetch (3+ pages, 60–130s with rate-limit backoff) burned the 90s freshness window before `_run_cycle()` ran. Moving `cycle_start_at` to after the fetch resets the window to when data is actually ready. 1-line fix with major throughput impact. | `src/prediction_market_bot/run_t4_mlb_live.py`; GOVERNANCE_GAP_LOG.md GG-052; DECISION_LOG SESSION 103 entry | EL |
| T-209 registered (dual T4 sessions) | Two T4 sessions (CE494B3A 06:30 UTC + B7193041 22:05 UTC) both hitting Kalshi API simultaneously, doubling rate-limit pressure. Root cause unknown — investigate before next T4 session to avoid compounding the fixed staleness issue. | TODO_NEXT.md SESSION 103 OPEN ITEMS | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| GG-052 root cause diagnosis | ✅ Audit JSONL forensics: all halts per cycle at same timestamp → `_run_cycle()` sub-second; window expired before entry. C0017 anomaly explained: Kalshi fetch happened to complete in ~86s (just under 90s), letting 50 evals pass. |
| GG-052 fix deployed | ✅ `cycle_start_at = snapshot_fetched_at` in `run_t4_mlb_live.py`. Commit `bbaf86a`. VPS deployed, t4-mlb restarted. |
| GG-052 governance registered | ✅ GOVERNANCE_GAP_LOG.md entry; DECISION_LOG SESSION 103 entry. |
| Session-end protocol | ✅ DECISION_LOG, TODO_NEXT, MEMORY_BANK, PLAN, SESSION_HANDOFF all updated. |

---

## ONE THING PENDING

**Verify the GG-052 fix is working on July 1 games.** Check `logs/audit_mlb_t4.jsonl` on VPS for July 1 — should show evaluation bursts (≥50 evals/cycle) rather than zero-eval staleness halts. If still showing 0-eval cycles: check whether `cycle_start_at = snapshot_fetched_at` is actually landing in the deployed code (`grep "cycle_start_at = snapshot_fetched_at" /opt/prediction-market-bot/src/prediction_market_bot/run_t4_mlb_live.py`).

---

## Current Paper Portfolio

- **MLB T1/T2 book:** `paper_portfolio_mlb.json` — accumulating since June 30 with YES+NO bets enabled
- **MLB T4 book:** `paper_portfolio_mlb_t4.json` — clean $1,000 (reset post-GG-050). First valid accumulation since June 30 (GG-052 fix deployed end of day)
- **NBA book:** $751.10 bankroll, 0 open, 158 closed, 24.9% drawdown — HALTED at kill switch. ADR-0035 ACCEPTED: reset at 2026-27 season start (October 2026).
- **G6 gate:** Requires EXP-017 CONFIRMED_POSITIVE (GG-004 OPEN) — needs ≥150 MLB closed positions (Tier 1). Not near threshold yet.

---

## Active Cron on VPS (157.230.91.33)

```
11:00 UTC  — PIPE-05 T1 MLB (run_mlb_paper_trade.py)
16:30 UTC  — PIPE-06pre MLB pregame context (run_mlb_pregame.py)
19:30 UTC  — PIPE-05.5 T2 MLB (run_t2_mlb_sameday.py)
*/15 20-23 — PIPE-06 T3 MLB momentum scan
*/15 0-3   — PIPE-06 T3 MLB midnight wrap
22:00 UTC  — PIPE-07 T4 MLB via systemd t4-mlb (run_t4_mlb_live.py) [FIXED GG-052]
22:30 UTC  — PIPE-05FX MLB feature refresh
06:30 UTC  — PIPE-05R MLB resolution (run_resolve_mlb.py)
21:00 UTC  — Health check
```

---

## Key Constraints to Remember

1. T4 MLB fix (GG-052) is live as of `bbaf86a` — next session should verify July 1 evaluation counts
2. T-209 (dual T4 sessions) is an open investigation — two concurrent sessions double Kalshi rate-limit pressure
3. ADR-0035 accepted — NBA paper portfolio reset at October 2026 season start (operator must execute checklist)
4. MLB YES-ONLY gate rescinded (SESSION 102) — both YES and NO bets now eligible for MLB paper record

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null` — clean at session start (no matches).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `GOVERNANCE_GAP_LOG.md` (GG-052 added) | N/A (not a decisions_logged doc) | SESSION 103 entry written | ✅ |
| `run_t4_mlb_live.py` (fix) | N/A (source code) | SESSION 103 entry written | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260630_2100.md.
# Verify GG-052 fix on VPS by checking audit_mlb_t4.jsonl for July 1 evaluation counts."
```
