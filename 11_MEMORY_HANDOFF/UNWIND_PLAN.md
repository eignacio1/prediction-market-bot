**RETIRED 2026-07-14 (Window 4 repo-hygiene close-out).** All four windows closed: A (GG-116 credential rotation — operator-executed) and D (real-terminal verification) are done; B (T-352 worktree/branch pruning, T-353/T-355 collision-check hardening) is RESOLVED per `GOVERNANCE_GAP_LOG.md` GG-107's Status line; C (T-354/GG-113 vig-sign bug) is RESOLVED via ADR-0043, DS sign-off, and a verified VPS deploy — see GG-113's own Resolution entry. Moved from repo root to `11_MEMORY_HANDOFF/` as a historical artifact; content below is unchanged and reflects 2026-07-14 planning-time state only — do not treat any status/exit-criterion language below as current, and see the governance-gap entries cited above for the authoritative close-out record.

---

# UNWIND PLAN — Post-Crash Recovery to Clean / Green / Auto

**Author:** analytical-copilot, 2026-07-14. **Diagnosis verdict: NO WORK LOST.** main=origin/main=`69fb152`, clean. All 7 residual branches (local+remote) have `unique-vs-main:0` — every crashed session's work is already in main. What remains is 1 security decision, 1 strategy fix, and mechanical residue.

**IDs:** T-351 already registered (GG-116). New here: **T-352–T-354** (re-check highest-in-use before claiming).

---

## WINDOW A — Security (OPERATOR-ONLY; do FIRST, do not delegate blindly)
### T-351 — GG-116: leaked Kalshi credential
- Key ID + private-key path were in a tracked handoff; plaintext redacted from live tree (`c7be13a`) but **still in git history, and the key is NOT rotated**.
- **Operator actions:** (1) **rotate the Kalshi API key** in the Kalshi dashboard; (2) decide git-history scrub (`git filter-repo`/BFG) — coordinate with all sessions since it rewrites history; (3) update `THREAT_MODEL` + flip GG-116 RESOLVED.
- **Claude may NOT rotate credentials.** A terminal session can prep the filter-repo command + verify no other secrets remain, but you execute the rotation.
- **Exit:** key rotated, history decision made+executed, GG-116 RESOLVED.

## WINDOW B — Residue cleanup (mechanical, safe, independent)
### T-352 — prune stale branches + worktrees
- All `prunable`, all `unique-vs-main:0`. From main checkout:
  ```bash
  # worktrees (5) — verify clean first, then:
  for w in 20260710T151127Z-workstream-b-edge-sign 20260711T225312Z-window2-n03-n05-cleann-gate \
           20260712T095020Z-gg092-gg093-readiness-debt 20260712T171320Z-gg114-followup-ci-nba-api-fix \
           20260713T235242Z-pr14-window3-rebase-merge; do
    git worktree remove --force ../PM-worktrees/$w; done
  git worktree prune -v
  # local branches (merged → -d; the 2 local-only stale → -D):
  git branch -d fix/gg-band-monitor-summary-gitignore session/20260710T151127Z-workstream-b-edge-sign \
     session/20260711T225312Z-window2-n03-n05-cleann-gate session/20260712T095020Z-gg092-gg093-readiness-debt \
     session/20260712T170200Z-orphaned-branch-gg-log session/20260712T171320Z-gg114-followup-ci-nba-api-fix
  git branch -D session/20260712T101511Z-gg112-adr0024-recommendations-recovery \
     session/20260713T235242Z-pr14-window3-rebase-merge
  # remote stale (confirm each is merged/superseded first):
  # git push origin --delete <same session/* branch names>
  ```
- **Exit:** `git worktree list` = main only; `git branch -a` = main + any genuinely-active session; `PM-worktrees/` empty.

### T-353 — GG-107/109: kill the root cause of this whole episode
- The duplicate-claim / unmerged-branch churn came from **no collision check on task-ID claims** (recurred GG-109→110, GG-111→112, T-346/347 dup). Add a pre-claim check to `claim_session.sh` (grep highest-in-use across TODO_NEXT+SESSION_CLAIMS+DECISION_LOG, refuse a taken ID) and enforce "push+merge before session-end, never leave a branch unmerged overnight" in `session-end.md` Step 8.
- **Exit:** claim script rejects a taken ID in test; GG-107 RESOLVED.

## WINDOW C — Strategy fix (GATED on DS sign-off)
### T-354 — GG-113: vig-sign bug (the GG-105 driver)
- `run_t4_mlb_live.py` flips vig sign for NO bets → +2×vig inflated edge on 81.8% of T4M-PROJ book. Requires a **superseding ADR + DS sign-off** (Hard Rule 3, live-formula change). After fix, re-run the GG-105 tercile test on corrected vig to isolate residual miscalibration.
- **Exit:** ADR accepted, formula corrected, GG-105 re-tested; DECISION_LOG updated.

## WINDOW D — Real-terminal verification (NOT cowork sandbox)
- Run FULL test suite (~2,400) on real hardware — sandbox is dependency-incomplete (T-337 owed).
- Step-4 VPS health: T1/T4 cron liveness, `SemanticFloorViolation`, `CONTAMINATION_HALT`.
- Confirm VPS HEAD == main `69fb152`.
- **Exit:** full-suite green count recorded; VPS current + healthy.

---

## Sequencing
1. **A first** (security — rotate before anything touches history). 2. **B + D in parallel** (cleanup + verify, independent). 3. **C** when DS is ready (gated). 4. **T-353** folds into B or its own window — it prevents recurrence, so don't skip it.

## Status of the prior chaos (for the record)
- GG-115 (CI gate broke on first run) — RESOLVED. GG-117 (gitignore deploy-blocker) — RESOLVED. GG-110 (SemanticFloorViolation) — RESOLVED false-alarm (date mismatch). GG-092/093 (readiness debt) — RESOLVED, merged PR #14. No data lost; recovery complete.
