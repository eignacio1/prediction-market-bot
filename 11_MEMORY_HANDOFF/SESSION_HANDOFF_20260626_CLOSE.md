# Session Handoff — 2026-06-26 SESSION 92 CLOSE

**Trigger:** Context window near limit — /session-end protocol
**Last commit:** `69a6b61` (main) — pushed to GitHub + VPS (HEAD confirmed on 157.230.91.33)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 2070/2070 passing (7 skip)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — 6 MLB crons active (PIPE-05, PIPE-05R, PIPE-05FX, PIPE-06pre, PIPE-05.5 T2, T3 MLB). T4 MLB paused (GG-007).
- **Paper bets (MLB):** Accumulating — bankroll $1,000, 0 open (as of session start)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Inning-aware `ab_remaining` uses conservative min-of-two-signals | `ab_from_inning` and `ab_from_total` can each be wrong; taking the minimum prevents over-estimating remaining ABs regardless of which signal is stale | DECISION_LOG.md T-200 entry | DS |
| Extra-innings (inning > 9) clamp `ab_remaining` to 0 | Conservative is correct for paper trading; no Binomial evaluation fires in extras rather than risk an uncalibrated estimate with negative `innings_remaining` | DECISION_LOG.md T-200 entry | DS |
| `_load_t2_batting_slots()` date-filters by today's date string in filename | Prevents yesterday's lineup from being used as today's (stale lineup → wrong slot → wrong expected ABs) | DECISION_LOG.md T-200 entry | DS |
| `SystemMonitor` in PIPE-05R scoped to T1/T2 pool only | T4 has its own separate kill switch and budget; C7 alert thresholds (e.g. drawdown %) are calibrated to T1/T2 initial bankroll, not T4's isolated pool. T4 monitoring belongs to its own C7 scope. | DECISION_LOG.md T-201 entry | DS |
| T4 pool resolution silently skips if `paper_portfolio_mlb_t4.json` absent | Allows PIPE-05R to run before T4 is ever enabled without error. Clean separation of concerns. | DECISION_LOG.md T-201 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-200: Inning-aware `ab_remaining` formula** | ✅ `_AB_BY_SLOT` constant added (Slots 1-9: 4.2→3.1 ABs). `_compute_ab_remaining(ab_so_far, inning, batting_slot)` uses `min(ab_from_inning, ab_from_total)`. `_load_t2_batting_slots()` loads today's T2 batting slots. Extra-innings clamp to 0. 22 new tests. `tests/test_run_t4_mlb_live.py`. |
| **T-201: Dual-pool resolution PIPE-05R** | ✅ `_resolve_pool(pool_label, trader, logger, session_id)` helper extracted. T4 pool resolves alongside T1/T2 in single PIPE-05R cron. T4 silently skipped if file absent. Audit log includes `resolved_t4`/`still_open_t4`. 5 new tests. `tests/test_t187e_mlb_resolve.py`. |
| **Test fix: `test_no_open_positions_exits_cleanly`** | ✅ Old assertion `"No open MLB positions"` → new `"No open positions"` (pool-labeled output from refactored main). |
| **Decision log entries** | ✅ T-200 formula architecture + T-201 dual-pool architecture logged in DECISION_LOG.md. |
| **Commit + deploy** | ✅ 5 files committed as `69a6b61` [SESSION 92 CLOSE]. Pushed to origin/main. VPS deployed HEAD confirmed. |
| **Governance scan (Step 0)** | ✅ CLEAN — no `decisions_logged: false` documents found. |

**Test delta:** 2044 → 2070 (net +26: 22 T-200 + 5 T-201 − 1 already counted from prior context)

---

## ONE THING PENDING

**T-202: dry-run mode for MLB T4.** Add `T4_MLB_DRY_RUN` env flag to `run_t4_mlb_live.py`. When `T4_MLB_DRY_RUN=true`:
- Compute all evaluations normally (Binomial model, C4 edge check, Kelly sizing)
- Log each evaluation to `logs/t4_mlb_dryrun_YYYYMMDD.jsonl` (one JSON line per evaluation: player, threshold, ab_so_far, ab_remaining, ba_l10, model_p, mip, edge, kelly_size, would_bet)
- Skip `trader.open_position()` — no portfolio mutations

Enable on VPS by adding `T4_MLB_DRY_RUN=true` to the `0 22 * * *` cron line in `deploy/cron.conf`. Run for 2-3 live games. Output will be used in T-203 to calibrate `MIN_EDGE_T4` for MLB (GG-007 resolution).

**No infrastructure changes needed before T-202**: `paper_portfolio_mlb_t4.json` already exists (T4 kill switch already in place). Just add the env flag + logging branch.

---

## Current Paper Portfolio

- **MLB:** Bankroll $1,000, 0 open (as of session start; bets accumulate at 11:00 UTC daily)
- **NBA:** Bankroll $751.10 (dark period — no NBA games; kill switch at 24.9% drawdown)
- G6 gate: 30 MLB resolved paper bets required (0/30 as of session start; G6 blocker = GG-004 EXP-017 commercial validation)

---

## Active Cron on VPS (157.230.91.33)

```
06:30 UTC     — PIPE-05R: MLB resolution (run_resolve_mlb.py) — resolves BOTH T1/T2 and T4 pools
11:00 UTC     — PIPE-05: MLB T1 paper bets (run_mlb_paper_trade.py)
16:30 UTC     — PIPE-06pre: MLB pregame context (run_mlb_pregame.py)
19:30 UTC     — PIPE-05.5: MLB T2 same-day bets (run_t2_mlb_sameday.py)
*/15 20-23    — T3 MLB (run_t3_mlb_pretip.py)
*/15 0-3      — T3 MLB (run_t3_mlb_pretip.py)
22:00 UTC     — T4 MLB PAUSED (run_t4_mlb_live.py) — enable after T-202/T-203
22:30 UTC     — PIPE-05FX: MLB feature refresh
14:10 UTC Mon — PIPE-05C: MLB calibration monitor
```

---

## Key Constraints to Remember

1. **T4 MLB is PAUSED** — `0 22 * * *` line is commented out in `deploy/cron.conf`. Re-enable only after T-202 (dry-run) + T-203 (calibration) complete.
2. **GG-007**: MLB T4 threshold constants uncalibrated. LOW severity while T4 paused, HIGH pre-activation. T-203 resolves this via calibration ADR.
3. **GG-043/GG-044**: MLB Kelly fraction (0.10) inherited from NBA without MLB derivation; C7 drift baselines are NBA G4 values. Both LOW severity — deferred to pre-MLB-G6.
4. **No live capital until G6** — requires 30 resolved MLB paper bets with positive P&L + EXP-017 CONFIRMED_POSITIVE (GG-004 open).
5. **`arb/` folder = REFERENCE ONLY** (APR-0010 required first).

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged | DECISION_LOG entries written | Status |
|----------|-----------------|------------------------------|--------|
| `run_t4_mlb_live.py` (T-200) | n/a (source file) | T-200 entry in DECISION_LOG.md | ✅ |
| `run_resolve_mlb.py` (T-201) | n/a (source file) | T-201 entry in DECISION_LOG.md | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260626_CLOSE.md.
# Session 92 is closed (T-200 + T-201 complete, 2070 tests, VPS HEAD 69a6b61).
# Next task is T-202: add T4_MLB_DRY_RUN env flag to run_t4_mlb_live.py."
```
