# Session Handoff — 2026-07-12T16:45Z

**Trigger:** Operator-initiated wrap-up — explicit usage-capacity constraint ("almost at usage capacity, 95%, 2 other terminal windows also need to close"). Session closed promptly on instruction rather than pursuing optional follow-on work.
**Last commit:** `91435bb` (main) — PR #13 merged, pushed to GitHub. VPS deploy auto-triggered by the merge (GitHub Actions `Deploy to VPS` workflow fired on push, run in_progress at close of session, not manually confirmed complete due to the usage constraint).

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** No test suite changes this session (diagnostic script + doc/governance-log edits only); full suite not re-run this session — last known-clean baseline from prior sessions was 2672 passed / 29 skipped / 0 failed.
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (not re-verified this session beyond the merge/deploy trigger — no Step 4 operational health check run this session; last confirmed healthy in a prior session)
- **Paper bets:** T1 clean_n=81/n*=2,322; T4M-PROJ clean_n=412/n*=3,059 (both `cadence_immature`, neither clears its own `n*` bar) — G6 gate (30/30 raw floor) still cleared on both bands, but APR-0024's `n*` standard is the governing bar for go-forward commercial-validation language, and neither band meets it yet.

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T-344/T-345 closed diagnose-only: GG-105's anti-predictive T4M-PROJ edge/win-rate pattern decomposed into 4 candidate mechanisms; leading mechanism is (d) model miscalibration/overconfidence, not (a) sign-inversion, (b) fee/edge-frame artifact, or (c) sizing artifact. No recalibration ADR proposed. | Explicit task scope: "DIAGNOSE, do not fix... use current data, do not wait for more sample." All four mechanisms tested against fresh clean_n=412 data with a definite verdict on each. | `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T344_GG105_DECOMPOSITION_MEMO.md`; DECISION_LOG.md 2026-07-12; GOVERNANCE_GAP_LOG.md GG-105 | DS |
| New governance gap registered: `run_t4_mlb_live.py`'s NO-direction gating flips vig from a cost to a credit, contradicting the codebase's own established symmetric-vig convention (`run_exp017.py`). Real bug, but does NOT explain GG-105 (correcting it sharpens the anti-predictive pattern, p 0.046→0.0094). Not fixed — diagnosis only, per Hard Rule 3 any live-formula change needs its own DS sign-off + ADR. | Found via direct code read + empirical confirmation (`scripts/run_t344_vig_sign_diag.py` against live clean_n=412 ledger); 337/412 (81.8%) of clean_n is NO-direction, 137/412 (33.3%) would fail to clear gating under the corrected formula. | GOVERNANCE_GAP_LOG.md GG-113 (renumbered from a session-local GG-112 draft) | DS |
| GG-112 ID collision resolved on merge: this session's draft GG-112 and a concurrent session's independent, unrelated, already-RESOLVED GG-112 (governance_scan.sh dashboard clean_n self-consistency bug) both existed at push time. Kept the merged RESOLVED entry as GG-112; renumbered this session's OPEN entry to GG-113. | Established project precedent: renumber the fresher/OPEN entry, not the RESOLVED one (GG-104/GG-109/GG-111 precedent). | DECISION_LOG.md 2026-07-12 (merge-resolution row); GOVERNANCE_GAP_LOG.md GG-112/GG-113 | DS |
| T-344 task-ID collision (same concurrent session used T-344 for an unrelated dashboard-fix task) noted but NOT renumbered — both now coexist in SESSION_CLAIMS.md, disambiguated by worktree name in DECISION_LOG.md rather than by changing either session's already-written task ID everywhere. | Renumbering task IDs retroactively across all already-committed prose (memo, script docstring, multiple log rows) was judged higher-cost than a one-line disambiguation note, given this session's explicit low-usage constraint. | DECISION_LOG.md 2026-07-12 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-344 (GG-105 decomposition) | ✅ Decomposition memo complete, all 4 mechanisms tested, leading mechanism identified (miscalibration/overconfidence), no recalibration ADR proposed per scope |
| T-345 (GG-020 fee verification) | ✅ No new evidence found (network blocked), GG-020 remains OPEN, clarified as orthogonal to GG-105 |
| PR #13 merge | ✅ Merged to main (`91435bb`), CI green pre-merge, GG-112 ID-collision conflict resolved manually on merge (renumbered to GG-113) |
| Worktree/branch cleanup | ✅ `scripts/end_session_worktree.sh` run, local + remote feature branch deleted |
| Nav-file updates | ✅ DECISION_LOG.md, GOVERNANCE_GAP_LOG.md, TODO_NEXT.md, MEMORY_BANK.md, PLAN.md all updated this session |

---

## ONE THING PENDING

**Awareness item, not a blocking task:** the operator flagged mid-session that a *third*, separately-running terminal window has its own fully-refined GG-105/Tier-adequacy task list (recommendations: re-derive Tier1/Tier2 adequacy against `clean_n` specifically before citing "Tier 1 reached" anywhere externally-facing — at T1 clean_n=65-81 the honest status is "below floor," not "reached"; resolve GG-105 and the clean_n reconciliation before treating T4M-PROJ's growing n as Tier-2 progress; standardize status language to "DIRECTIONAL_POSITIVE, bootstrap-insignificant, sample accumulation in progress"; confirm NBA-dark forecloses the dual-sport adequacy path — no action needed there, standing directive is correct; correct any "ADR-0024 deferred" mislabeling — the ADR is ACCEPTED/closed, the Tier1/Tier2 evidentiary checkpoint it defines is OPEN). **This session did NOT action that list** (out of scope for T-344/T-345, avoided duplicating a concurrent session's work). The next session should check `SESSION_CLAIMS.md` and recent commits for whether that third window has since landed its own PR before starting any new GG-105/Tier-adequacy work, to avoid triple-duplicating effort across three sessions in one day.

**Also unconfirmed:** the VPS `Deploy to VPS` GitHub Actions run triggered by this session's merge was still `in_progress` at session close and was not watched to completion (deliberately, given the usage-capacity constraint). Next session should do one quick `gh run list --workflow=deploy.yml --limit 1` check before assuming the deploy landed.

**Explicitly deferred, not started:** T-348 (GG-107 cleanup — untracked `ITERATION_PLAN_calibration_hardening.md` / `_v2.md` files in the repo root) was named as optional "fold in if low on context" in the original task instruction; the operator's explicit usage-capacity message superseded that, so it was not picked up this session. Still pending for a future session.

---

## Current Paper Portfolio

- MLB T1: clean_n=81/n*=2,322 (cadence_immature); MLB T4M-PROJ: clean_n=412/n*=3,059 (cadence_immature) — figures as of this session's DECISION_LOG entries, not independently re-pulled at session-end
- NBA: dark/frozen, unchanged (see [[project_nba_deferred]] convention)
- No new capital-affecting action this session

---

## Active Cron on VPS (157.230.91.33)

Unchanged this session — not independently re-verified (Step 4 operational health check was not re-run; last confirmed in a prior session per project convention).

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (30 resolved paper bets + positive P&L — APR-0016) AND, per APR-0024 (2026-07-12), per-band `clean_n ≥ n*` for go-forward commercial-validation language — neither active band currently clears its own `n*`
3. **Third concurrent terminal window has its own GG-105/Tier-adequacy task list in flight** — check for overlap before starting new work in that area (see ONE THING PENDING above)
4. GG-113 (vig-sign-flip bug) is OPEN and unfixed — any live-formula change requires fresh DS sign-off + superseding ADR per Hard Rule 3

---

## ⚙️ DECISION AUDIT

**Step 1 result:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → clean, no matches.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| N/A this session | — | GG-105/GG-113 decisions logged directly to DECISION_LOG.md (no `decisions_logged` field applicable — these are governance-log/decision-log entries, not spec/architecture documents) | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260712_1645.md.
# Check SESSION_CLAIMS.md and recent commits for whether the third concurrent window's
# GG-105/Tier-adequacy task list has landed before starting new GG-105 work. Confirm VPS
# deploy from commit 91435bb completed via `gh run list --workflow=deploy.yml --limit 1`."
```
