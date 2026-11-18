# Session Handoff — 2026-06-10T23:00Z (SESSION 46 CLOSE)

**Trigger:** Operator-initiated — session-end at clean stopping point; G5 is Saturday
**Last commit:** `0f38112` (main) — pushed to GitHub + VPS
**Session:** SESSION 46 CLOSE (continued from compacted SESSION 46 context)

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live
- **Tests:** 843/843 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — T4 cron active (PIPE-07, 23:00 UTC); T1 cron active (PIPE-03)
- **T1 Bankroll:** $1,000.00 (reset; 0% drawdown; 3 open positions from G4 unresolved?)
- **T4 Pool:** $1,869.68 (paper; 0 open positions; daily_loss $86.69 — auto-clears on G5 date change)
- **Paper bets:** 114/30 resolved (T1) — G6 gate met on volume; blocked on commercial validation (GG-004)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-026 registered: PAPER_T4_FLAT_SIZING is an architectural shortcut that has outlived its scope | T4 pool grew $500→$1,869.68; flat $500 cap is now 26.7% of pool and doesn't scale. Production path (T4_BAND_WEIGHT=0.10) would yield $186.97 — less than the current cap, never calibrated. DS directive: "no arbitrary capital restraint — no bandaid fixes." | GOVERNANCE_GAP_LOG.md GG-026; DECISION_LOG SESSION 46 CLOSE entry | DS (Earl) |
| T-163 registered as PRE-G5 CRITICAL: ADR-0023 — remove PAPER_T4_FLAT_SIZING, calibrate T4_BAND_WEIGHT from Kelly math | DS explicitly: "we'll need to rework that again — no bandaid fixes." Derivation must use G1–G4 trajectory data (expected concurrent positions × Kelly fraction × average edge → target utilization fraction). Not an arbitrary constant. | TODO_NEXT.md T-163 priority 0; DECISION_LOG SESSION 46 CLOSE entry | DS |
| EXP-018 Hypothesis C ruling elevated to PRE-G5 CRITICAL (0b) | SESSION 43 ruling (injury-filtered governs T1 Tier 2B) is invalidated by G4 data: injury-filtered EV flipped CONFIRMED_NEGATIVE at n=98. DS ruling required before G5 or G5 bets are placed without governance clarity on which markets are eligible. | TODO_NEXT.md T-163 0b; DECISION_LOG SESSION 46 entry 231 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Session-start protocol (Q1–Q6) | ✅ Full protocol run; 4 worries surfaced; Worry 1 → GG-026/T-163; Worry 3 → MEMORY_BANK updated |
| MEMORY_BANK.md updated to SESSION 46 final state | ✅ `Last reviewed` and `Last major milestone` updated to reflect ADR-0021, ADR-0022, 843/843, bankroll reset, G5 clean strip |
| GG-026 registered in GOVERNANCE_GAP_LOG.md | ✅ T4 pool architecture gap: flat $500 cap doesn't scale with pool growth; T4_BAND_WEIGHT never calibrated |
| T-163 registered in TODO_NEXT.md (priority 0 — pre-G5 critical) | ✅ ADR-0023: remove PAPER_T4_FLAT_SIZING; calibrate T4_BAND_WEIGHT from Kelly math |
| EXP-018 Hypothesis C DS ruling added to TODO_NEXT as priority 0b | ✅ Pre-G5 critical — DS ruling required on T1 Tier 2B before G5 bets placed |
| DECISION_LOG updated — SESSION 46 CLOSE entry | ✅ GG-026 gap + T-163 registration + governance scan findings |
| TODO_NEXT.md priority queue reordered for G5 | ✅ Priority 0 (T-163), 0b (Hypothesis C ruling), 1–6 unchanged |
| PLAN.md updated | ✅ `Last reviewed` + Phase 6 paper evidence row updated to post-G4 state |

---

## ⚠️ ONE THING PENDING (MOST IMPORTANT)

**T-163 must be implemented before G5 (Saturday).** This is the T4 pool architecture fix the DS ordered. The task:

1. Remove `PAPER_T4_FLAT_SIZING` flag and its `PAPER_T4_POOL_USD` shortcut from `run_t4_live.py`
2. Activate `_compute_t4_band_budget(portfolio)` = `deployable × T4_BAND_WEIGHT`
3. Calibrate `T4_BAND_WEIGHT` from Kelly math — not arbitrarily. Derivation: use G1–G4 trajectory data from `t4_position_trajectories.jsonl` to measure average edge, average concurrent positions, average hold duration → compute expected peak utilization fraction → set T4_BAND_WEIGHT to cover 2× expected peak. This is a one-ADR derivation before implementation.
4. Write ADR-0023 with full derivation
5. Deploy to VPS before Saturday

**Second pending item:** DS ruling on EXP-018 Hypothesis C — which markets fire in G5?

---

## Current Paper Portfolio

- **T1 Bankroll:** $1,000.00 (reset; 0% drawdown)
- **T1 Open:** 3 (G4 residual — should resolve via GHA workflow)
- **T1 Closed/Resolved:** 114 | G6 gate: 114/30 ✓ (volume met; commercial validation GG-004 blocks)
- **T4 Pool:** $1,869.68 (paper isolated; 0 open positions)
- **T4 deployed (G5):** $0.00 (ADR-0022 game_date keying; strip is clean)
- **T4 daily_loss:** $86.69 (from G4; auto-clears on G5 date change via date-reset guard)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
05:30 UTC  — GHA post_game_resolve.yml (T1 + T4 auto-resolve — primary path)
06:00 UTC  — Mac cron post_game_g5_resolve.sh (fallback + experiment runner)
23:00 UTC  — PIPE-07 T4 in-play (run_t4_live.py)
14:00 UTC Mon — Model freshness check
```

**PIPE-03 in-progress guard (T-162) is active.** The PIPE-03 late cron will skip bet placement if the game is already in progress (ESPN `STATUS_IN_PROGRESS` check; commit `c8a59f2`).

---

## Key Constraints to Remember

1. **GG-004 OPEN — G6 live capital blocked.** EXP-017B is DIRECTIONAL_NEGATIVE (-$0.0361/bet, n=96 vs actual Kalshi prices). Commercial validation is negative, not just unproven. G6 requires positive commercial validation before live capital.
2. **EXP-018 Hypothesis C DS ruling required before G5.** SESSION 43 ruling (injury-filtered governs) is invalidated. DS has three options: (a) T1 Tier 2B FAILS — suspend those markets; (b) insufficient sample — continue with caution flag; (c) other. Currently no ruling → ambiguous eligibility for G5 bets.
3. **T4 pool architecture (GG-026) is the pre-G5 implementation priority.** PAPER_T4_FLAT_SIZING=true bypasses the production Kelly budget path. Fix required before Saturday.
4. No live capital until G6 (**30 resolved paper bets met**; commercial validation and DS sign-off still required).

---

## ⚙️ DECISION AUDIT

**Governance scan:** ENOSPC on temp filesystem prevented bash scan; hook output at session start confirmed CLEAN (no `decisions_logged: false` documents in 02_ARCHITECTURE_DESIGN/, 08_MODEL_RISK_GOVERNANCE/, 01_SPEC/).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md (GG-026 added) | N/A — tracking doc, not CANONICAL strategy doc | DECISION_LOG SESSION 46 CLOSE entry written | ✅ |
| TODO_NEXT.md (T-163, 0b added) | N/A — task list | DECISION_LOG SESSION 46 CLOSE entry written | ✅ |
| MEMORY_BANK.md (updated) | N/A | — | ✅ |
| PLAN.md (updated) | N/A | — | ✅ |

---

## Pre-G5 Priority List (Saturday game)

| Pri | Task | Why | Owner |
|-----|------|-----|-------|
| **0 — CRITICAL** | T-163: ADR-0023 — Remove PAPER_T4_FLAT_SIZING; calibrate T4_BAND_WEIGHT | DS directive: no arbitrary $500 cap; must scale with bankroll; no bandaid | Next session |
| **0b — DS RULING** | EXP-018 Hypothesis C | SESSION 43 ruling invalidated; which T1 markets fire on Saturday? | DS: Earl |
| **0c — VERIFY** | Confirm VPS T4 has ADR-0021+0022 code deployed | VPS HEAD should be `0f38112`; confirm grep on `_exit_budget_credit` and `null_delta_sigma` | Pre-game |
| **0d — VERIFY** | Confirm T1 open positions (3) are resolved before G5 | GHA workflow should resolve by 05:30 UTC; verify before G5 tip | Pre-game |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260610_2300.md.
# T-163 is the opening task — ADR-0023: remove PAPER_T4_FLAT_SIZING, calibrate T4_BAND_WEIGHT
# from Kelly math using G1-G4 trajectory data. Also need DS ruling on EXP-018 Hypothesis C
# before G5 (Saturday). Confirm 843 tests and VPS HEAD = 0f38112."
```

---

## NEXT SESSION PRIMER

Read `MEMORY_BANK.md` and this file. T-163 is the first and only implementation task before G5: write ADR-0023 (remove PAPER_T4_FLAT_SIZING, derive T4_BAND_WEIGHT from G1–G4 trajectory data via Kelly math), implement, test, deploy. Before writing code, confirm the DS ruling on EXP-018 Hypothesis C (priority 0b) — that ruling may also affect T1 market selection for Saturday. VPS HEAD should be `0f38112` — verify before any deploy.
