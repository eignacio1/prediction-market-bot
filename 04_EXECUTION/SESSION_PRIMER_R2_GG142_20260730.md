# Session Primer — R2/GG-142 (signed edge gate), parked 2026-07-30 ~05:55Z

**Why this file exists:** parent session hit its context/token limit mid-task. All
substantive work is DONE, COMMITTED, and PUSHED — nothing is at risk of loss. This
file exists only so a follow-on session can resume the small amount of bookkeeping
left (PR creation) without re-deriving context.

## Status: PR OPEN (#60), not yet merged

**Update 2026-07-30 (tokens reset, session continued):** PR opened —
https://github.com/eignacio1/prediction-market-bot/pull/60. GG-126 register
parity also fixed same session: ADR-0048 and ADR-0049 were both missing from
`00_ADMIN/APPROVALS_REGISTER.md` (flagged by `governance_scan.sh`'s parity
check); written back directly to `main` in commit `f9c9605` (doc-only,
path-scoped, no HEAD drift at write time). Remaining step is merge — left
for the operator or a follow-on session, not done unilaterally here.

## (historical) Status: work complete, not yet merged

- Branch: `session/20260730T052831Z-r2-gate-fix`
- Worktree: `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260730T052831Z-r2-gate-fix/`
- All commits pushed to `origin/session/20260730T052831Z-r2-gate-fix`
- **No PR opened yet** — that is the only remaining step.

## Commits on this branch (in order)

1. `1b0a8f8` — the actual fix: `risk.py` CHECK 3 changed from `abs(edge) < MIN_EDGE_TO_APPROVE`
   to signed `edge < MIN_EDGE_TO_APPROVE`; new CHECK 4b direction/gross_edge sign-consistency
   check; `edge_signal` diagnostic corrected to signed. Plus `tests/test_c4_risk.py`: fixed
   one test that encoded the bug as expected behavior, added 3 new tests.
2. `a1b9757` — `logic_epoch.py` epoch 9→10 boundary (`resolving_gap="GG-142"`,
   `bands_affected={ALL_BANDS}`, commit_sha references `1b0a8f8`'s full SHA), new
   `03_DECISIONS/ADR-0049_signed-edge-gate-and-direction-consistency-check.md`,
   `GOVERNANCE_GAP_LOG.md` GG-142 Resolution/Status updated to RESOLVED (gate defect),
   `DECISION_LOG.md` R2 entry appended.
3. `a1fa1f2` — closure bookkeeping only: `R2 DONE` line appended to
   `04_EXECUTION/ITERATION_MC_PROGRESS.md`, closure row appended to
   `04_EXECUTION/SESSION_CLAIMS.md`. No code changes.

## What the fix does (one paragraph)

`risk.py`'s CHECK 3 gated trade approval on `abs(edge) < MIN_EDGE_TO_APPROVE`, but `edge`
is already direction-resolved by every producer (fee/vig-net edge *in the recommended
direction*) — a negative value means a confidently-**wrong** bet, not a smaller-but-valid
one. `abs()` rescued 239/239 (46.1%) of T4 epoch-8 evaluations with `vig > |model_p − mid|`
into approval. Fixed to a signed check. Added CHECK 4b as a second, independent guard:
validates `recommended_direction` against the sign of an optional `gross_edge` field when
present, catching a *different* bug class (producer assigns direction inconsistently with
the raw signal) that a signed-but-internally-consistent `edge` alone wouldn't reveal.

**This is a correctness fix only. It does NOT re-expose live capital risk.** R1 (prior
session, commit `6be807f`, ADR-0048) already zeroed `kelly_fraction` for
T1_MULTI_DAY/T2_SAME_DAY/T3_PRE_TIP/T4M_PROJ. Sizes remain zero after this fix — this just
makes the gate correct for whenever those bands are reactivated.

## Verification performed

- 3 new unit tests in `tests/test_c4_risk.py` + 1 corrected (was asserting the buggy
  behavior). All pass.
- Full suite run with changes: same failure count as baseline.
- **Differential proof of zero regressions**: `git stash` (reverting this session's changes),
  re-ran the same failing test files, got the *identical* failure set — proving all
  remaining failures pre-exist from R1's Kelly-zeroing (fixture assumptions built on
  nonzero Kelly) plus one unrelated `exp015` EV-formula issue, not caused by this fix.
  `git stash pop` restored the changes afterward. This matches R1's own documented
  baseline exactly (2754 passed / 17 known-failed / 28 skipped).

## Remaining steps for the next session

1. **Open the PR.** From the worktree:
   ```bash
   cd "/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260730T052831Z-r2-gate-fix"
   gh pr create --title "R2/GG-142: signed edge gate + direction-consistency check (C4)" \
     --body "$(cat <<'EOF'
   ## Summary
   - Fixes GG-142: risk.py CHECK 3 gated on abs(edge), rescuing confidently-wrong
     bets (46.1% of T4 epoch-8 cohort) into approval. Now signed.
   - Adds CHECK 4b: direction/gross_edge sign-consistency check (independent guard).
   - New ADR-0049 (Hard Rule 3 — did not amend ADR-0043/0045/0048).
   - logic_epoch 9->10, bands_affected={ALL_BANDS} (shared unconditional code, GG-077 precedent).
   - Correctness fix only — ADR-0048's kelly_fraction=0 for T1/T2/T3/T4M-PROJ unchanged,
     no live sizing goes active at this boundary.
   - DS sign-off: operator, 2026-07-29 (Strategic Analysis §A/§E/§H).

   ## Test plan
   - [x] 3 new unit tests + 1 corrected in tests/test_c4_risk.py, all passing
   - [x] Full suite: zero new regressions (git stash differential vs pre-fix baseline)
   EOF
   )"
   ```
2. After PR is created/reviewed, standard merge into `main` (follow the R1/G2/G3 precedent
   of prior sessions this week — squash or merge per repo convention, then release the
   session claim if not already released — it already was, in the `SESSION_CLAIMS.md`
   closure row).
3. **Flagged as explicitly out of scope by this fix** (do not assume these are done):
   - VIG_CEILING recalibration (mentioned in GG-142's Resolution notes as item (c))
   - `power_calc`/GG-105 tercile re-measurement needs to run against a **fresh epoch-10
     clean cohort** (item (d) in GG-142 Resolution) — epoch-9 and earlier cohorts include
     the abs()-bug-contaminated evaluations and should not be used for that re-derivation.
   - GG-135/ADR-0048's "T4 edge is negative" rationale was itself derived from
     abs()-contaminated data and needs re-derivation against clean epoch-10 data before
     being treated as still-settled — this is a live open item, not resolved by this fix.
4. No further code changes anticipated for GG-142 itself — item 1 (PR) is the only hard
   blocker to calling this fully closed.

## Key files touched (for quick orientation)

- `src/prediction_market_bot/c4_risk_engine/risk.py` — CHECK 3 (signed) + CHECK 4b (new) + `edge_signal` fix
- `tests/test_c4_risk.py` — 1 corrected test, 3 new tests
- `src/prediction_market_bot/logic_epoch.py` — epoch 10 boundary appended to `_BOUNDARIES`
- `03_DECISIONS/ADR-0049_signed-edge-gate-and-direction-consistency-check.md` — new
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-142 Resolution/Status updated
- `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` — R2 entry appended
- `04_EXECUTION/ITERATION_MC_PROGRESS.md` — R2 DONE line appended
- `04_EXECUTION/SESSION_CLAIMS.md` — closure row appended

## Session-crash safety note

Everything above is pushed to `origin/session/20260730T052831Z-r2-gate-fix`. Even if this
worktree or the parent session's window is lost, `git fetch && git checkout
session/20260730T052831Z-r2-gate-fix` from any clone recovers the full state. Nothing here
depends on uncommitted local state.
