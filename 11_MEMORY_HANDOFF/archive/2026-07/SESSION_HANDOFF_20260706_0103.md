# Session Handoff — 2026-07-06T01:03Z

**Trigger:** Operator-initiated ("Good - /session-end")
**Last commit:** `14ffe69` (main) — pushed to GitHub + VPS (session-end doc-only commit for this continuation pending on top)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 2,370 passed / 7 skipped / 1 pre-existing unrelated failure (`test_feature_csv_freshness`) — unchanged this continuation
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; `t4-mlb` systemd service active
- **Paper bets:** MLB 99/30 resolved (G6 count+sign met, EXP-017 sample-adequacy + DS sign-off still required) | NBA 158/30 resolved (DARK/FROZEN, historical)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| EXP-ARITH-MLB-01 rerun (n=7, INCONCLUSIVE) accepted as final — no `execution_bands.py` registry change | The experiment's own MIN_N=20 gate was not met; a looser exploratory grid cell (n=28, DIRECTIONAL_NEGATIVE at gate=0.70) within the same run is a different parameterization and was explicitly judged not to count as evidence against the live gate=0.80 config | DECISION_LOG.md 2026-07-05 | DS |
| GG-090 fixed at the call site only (`run_exp_flow_mlb_01.py`); the general module-level `BOT_C4_ACTIVE` guard in `run_t4_mlb_live.py` was deliberately left unfixed | Minimal, test-verified call-site fix vs. a broader refactor of the live T4 service's entry point — judged out of scope for a same-session bug fix; the pandas/venv false start during relaunch was a separate, unrelated environment mistake, not part of this decision | DECISION_LOG.md 2026-07-05, GOVERNANCE_GAP_LOG.md GG-090 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| GG-090 investigation | ✅ Root-caused: `run_exp_flow_mlb_01.py`'s deferred import of `run_t4_mlb_live.py` hits that module's unconditional module-level `BOT_C4_ACTIVE` guard (`sys.exit(1)` on import, not gated by `__main__`). EXP-ARITH-MLB-01 unaffected (reimplements math locally, zero imports from `run_t4_mlb_live.py`, confirmed via grep). |
| GG-090 fix | ✅ Call-site `os.environ.setdefault("BOT_C4_ACTIVE", "true")` added to `run_exp_flow_mlb_01.py`, mirroring the existing in-process pattern in `run_mlb_paper_trade.py`/`run_paper_trade.py` and the exact workaround already present in `tests/test_run_exp_flow_mlb_01.py:22`. 25/25 tests passed. Committed `14ffe69`, pushed, VPS pulled clean. |
| EXP-FLOW-MLB-01 relaunch | ✅ First attempt (bare `python3`, PID 931714) hit unrelated `ModuleNotFoundError: pandas` — wrong interpreter. Corrected via `venv/bin/python3`. Current run: **PID 931930**, log `/tmp/exp_flow_run2_20260705.log`, launched ~17:50 UTC 2026-07-05, confirmed progressing normally (healthy 406-retry/ESPN-fallback activity across multiple game-dates). Verdict still pending. |
| Docs corrected | ✅ GG-088's stale "still running" note fixed to point to GG-090; new GG-090 entry added to GOVERNANCE_GAP_LOG.md; TODO_NEXT.md header updated across two passes (crash discovery, then final relaunch state); 2 new DECISION_LOG.md rows; MEMORY_BANK.md and PLAN.md Last-reviewed/Current-State-Snapshot/What-Must-Happen-Next sections updated for this continuation. |

---

## ONE THING PENDING

**Check EXP-FLOW-MLB-01's verdict.** Relaunched as PID 931930, log `/tmp/exp_flow_run2_20260705.log`, launched ~17:50 UTC 2026-07-05. A `ScheduleWakeup` was set for ~18:36 UTC 2026-07-05 to check it — if that already fired and reported a verdict earlier in this session (before this handoff was written), that verdict supersedes this note; check the conversation and GOVERNANCE_GAP_LOG.md GG-090 first. If not yet checked: `ssh prediction-market-vps "ps -p 931930; tail -80 /tmp/exp_flow_run2_20260705.log"`. If complete, record the verdict in GOVERNANCE_GAP_LOG.md/TODO_NEXT.md; only flip `execution_bands.py`'s T4M_FLOW registry status away from `BLOCKED` if the verdict actually clears the experiment's own gate (deemed unlikely given EXP-ARITH's INCONCLUSIVE result against the same underlying cycle-log data) — do not flip it on a partial or ambiguous result.

---

## Current Paper Portfolio

- **MLB (ACTIVE):** Bankroll $646.33 — Open 55 ($431.48 deployed) — Resolved 99/30 (G6) — 0.0% drawdown — P&L +$77.81
- **NBA (DARK/FROZEN):** Bankroll $751.10 — Open 0 — Resolved 158/30 (G6) — 24.9% drawdown — P&L -$248.90 (historical/adjudicated, not a live risk signal)

---

## Active Cron / Services on VPS (157.230.91.33)

- T1/T2/T3 MLB — cron-scheduled, active
- `t4-mlb.service` — systemd, active (T4M-PROJ, `run_t4_mlb_live.py`)
- T1 NBA — cron-scheduled but off-season / tabled (0 games expected)
- EXP-FLOW-MLB-01 — ad hoc background process, PID 931930, not cron/systemd (one-off experiment run)

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016) — MLB has met the count+sign floor; EXP-017 sample-adequacy (ADR-0024 Tier 1/2) and DS sign-off remain outstanding (GG-004)
3. VPS Python scripts requiring project dependencies (pandas, etc.) must be run with `venv/bin/python3`, not bare `python3` — bare `python3` lacks project dependencies (newly-discovered operational fact this session, cost one relaunch false-start)
4. `run_t4_mlb_live.py` has an unconditional module-level `BOT_C4_ACTIVE` guard that fires on *import*, not just execution — any future script that imports helpers from it needs `os.environ.setdefault("BOT_C4_ACTIVE", "true")` set first (GG-090)

---

## ⚙️ DECISION AUDIT

**Step 1 result:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → clean, no matches.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md | n/a (gap log, not a decisions_logged-tracked doc) | GG-090 entry added | ✅ |
| DECISION_LOG.md | n/a (is the log itself) | 2 new rows (ARITH-accepted-as-final, GG-090 fix-scope) | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260706_0103.md, confirm 2,370 tests, then check EXP-FLOW-MLB-01 (PID 931930) for its verdict"
```
