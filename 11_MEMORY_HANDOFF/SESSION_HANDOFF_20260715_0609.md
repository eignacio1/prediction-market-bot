# Session Handoff — 2026-07-15T06:09Z

**Trigger:** Operator-initiated (`/session-end` after task completion)
**Last commit:** `1d528bf` (branch `session/20260715T054123Z-gg119-t2-vig-diagnosis`) — pushed to GitHub, PR #22 open, not yet merged

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** No test count change this session (diagnosis-only, zero `src/` changes) — last certified count remains 2465 passed / 29 skipped / 0 failed (2494 collected, 2026-07-11 T-336/T-337)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (not re-verified this session; last Step 4 health check was a prior session)
- **Paper bets:** T1 MLB 259 resolved (freshest count, pulled live this session via the diagnostic script) — clears G6's 30-bet floor; APR-0024 `clean_n ≥ n*` standard governs go-forward gate language (see CLAUDE.md)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-119 diagnosis confirmed T1 CONFIRMED / T2 RULED OUT, but **no code change made** despite a clear, quantified, dollar-denominated finding | Explicit task instruction: "diagnosis only, full stop — no code change regardless of outcome," and T1/T2 is the active/primary G6 book, so the bar for touching its live formula is higher than it was for GG-113/T4M-PROJ. Any fix requires fresh DS sign-off (Hard Rule 3). | `GOVERNANCE_GAP_LOG.md` GG-119, PR #22 | DS (pending) |
| Finding packaged as a PR (diagnosis + quantification, zero production diff) rather than a GOVERNANCE_GAP_LOG note alone | Matches the GG-113/ADR-0043 escalation precedent — gives Earl a single reviewable artifact with the full technical case, mirroring how the prior sign-flip bug was surfaced. | PR #22 (https://github.com/eignacio1/prediction-market-bot/pull/22) | DS (pending) |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-362/GG-119: read `run_mlb_paper_trade.py::_directional_edge()` and `run_t2_mlb_sameday.py`'s local gating formula against `run_exp017.py`'s symmetric-vig convention | ✅ T1 CONFIRMED to carry GG-113's sign-flip pattern; T2 RULED OUT (no NO-direction branch) |
| Quantify T1's impact empirically against the live resolved ledger (`scripts/run_t362_gg119_t1_vig_diag.py`, mirroring `run_t344_vig_sign_diag.py`) | ✅ 259 resolved positions, 248 NO/11 YES; all 248 NO bets inflated by exactly `2 × half_spread`; 74 (28.57% of the full book) falsely admitted past `MIN_EDGE_TO_APPROVE=0.04`; that subgroup net -$48.26 vs. book-wide +$34.56 |
| Update `GOVERNANCE_GAP_LOG.md` (GG-119), `DECISION_LOG.md` (Hard Rule 7), `TODO_NEXT.md` | ✅ All updated, committed `1d528bf`, zero drift vs. `origin/main` at commit time |
| Open PR #22 as the decision-request vehicle for Earl | ✅ https://github.com/eignacio1/prediction-market-bot/pull/22 — zero production-code diff, same escalation shape as GG-113 |
| `/session-end`: update `MEMORY_BANK.md` (Last reviewed, Current State Snapshot Thread 8, What Must Happen Next, Compass OS Health/M1), `PLAN.md` (Last reviewed) | ✅ This document + those edits |

---

## ONE THING PENDING

**PR #22 is open and unmerged, awaiting Earl's decision.** This is a documentation/diagnosis-only PR (zero `src/` diff — touches `GOVERNANCE_GAP_LOG.md`, `DECISION_LOG.md`, `TODO_NEXT.md`, plus a new diagnostic script and its JSON output). It does not itself require DS sign-off to merge — only the *proposed fix* to `_directional_edge()` requires sign-off. Recommend merging PR #22 promptly (no code-risk, pure documentation) and treating the DS sign-off as a separate, subsequent decision about whether/how to fix the formula. Next session should check PR #22's status first: if still open, either merge it directly (safe — no production diff) or confirm with Earl why it should stay open longer.

---

## Current Paper Portfolio

- T1/T2 MLB (ACTIVE): 259 resolved positions (T1), pulled fresh this session via `scripts/run_t362_gg119_t1_vig_diag.py` — book-wide realized P&L **+$34.56** on the 248 NO / 11 YES resolved T1 subset examined. Bankroll/open-position figures not re-pulled this session (last known: $877.85 bankroll, 22 open, per the 2026-07-11 consolidated snapshot in `MEMORY_BANK.md` — treat as stale, re-pull before relying on it for kill-switch-proximity judgments).
- MLB T4M-PROJ (ACTIVE): post-GG-113-fix epoch reset (`CURRENT_LOGIC_EPOCH=4`), `clean_n` rebuilding from 0 as of 2026-07-14 — not touched this session.
- NBA (DARK/FROZEN): unchanged, $751.10, 0 open, 158 resolved, 24.9% drawdown, −$248.90.
- G6 gate: T1 `clean_n` progress unchanged by this session (no code fix applied, no epoch bump).

---

## Active Cron on VPS (157.230.91.33)

Not re-verified this session (Step 4 VPS health check was not re-run — this session ran entirely in an isolated worktree on diagnosis/documentation work, no VPS-affecting change). Last known-good cadence per prior sessions:
```
T1/T2/T3 MLB — daily cron, cron-scheduled
t4-mlb.service — systemd, live 45s poll loop
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (30 resolved paper bets + positive P&L — APR-0016); per-band `clean_n ≥ n*` now governs go-forward gate language (APR-0024)
3. **GG-119 (T1 vig-sign-flip) and GG-105 (T4M-PROJ `ba_l10` shrinkage) are two separate, independent decision requests sitting with Earl (PR #22 and APR-0025 respectively) — do not conflate them or re-diagnose either cold next session.**
4. GG-119's proposed fix pattern (when authorized) should reuse the `_directional_edge()`-style direction-aware recompute GG-077/ADR-0043 already established — not be re-derived from scratch.

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null` — clean, no matches (re-run at session start this session, confirmed clean before any work began).

**Step 2:**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `GOVERNANCE_GAP_LOG.md` (GG-119 fields) | N/A (gap-log entry, not a `decisions_logged` doc) | T-362 row, 2026-07-15 | ✅ |
| PR #22 | N/A (code PR, not a strategic doc) | T-362 row covers the underlying finding | ✅ |

Sprint/session is closed — no `decisions_logged: false` document was created or substantially modified this session.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260715_0609.md, check PR #22's status, confirm test count"
```
