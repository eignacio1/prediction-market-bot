# SESSION HANDOFF — PARKED BEFORE START (token scarcity)

**Claim:** T-419, `2026-08-05T01:14:39Z` row in `SESSION_CLAIMS.md`.
**Branch:** `session/20260805T011351Z-gg159-propagation-citation-rule` (worktree only — not yet merged, not yet pushed at park time; no `src/` touched, doc-only work never started).
**Why parked:** operator flagged near token exhaustion mid-protocol, before Task 1 execution began. Session-start protocol (git pull, worktree launch, claim) completed; adversarial Q1-Q6 review NOT run. No analysis, no edits made. This file exists so the next session picks up cold with zero re-derivation.

## ID note for next session
- **T-418 was already taken** (claimed AND closed same-day by a concurrent/prior session for GG-153 T1 adjudication + T-416 stuck-positions diagnosis — unrelated task, same ID number the operator's prompt assumed was free).
- **GG-161 is confirmed taken** (registered by that same T-418 session, stuck-positions causal finding).
- This session claimed **T-419** instead. Next session: re-grep `SESSION_CLAIMS.md`/`TODO_NEXT.md`/`DECISION_LOG.md` for highest T-/GG- before claiming — do not assume T-419+1 is free without checking, per the T-418 collision just observed.

## Full task spec (verbatim intent, unexecuted)

### Task 1 (mandatory) — propagate GG-159's correction everywhere
GG-159 (registered by T-413, closed same-day per SESSION_CLAIMS.md 2026-08-04T23:35:00Z entry) found `PROJECT_ASSESSMENT_2026-07-30.md` §8 Assumption 1's headline (n=344 / +10.99% / P=0.972 / monotonic terciles) used a code-unverified symmetric-vig reconstruction. Verified correct figures: **n=388 / +9.65% / P=0.961 / NOT monotonic** (as-of-2026-07-30 cohort); current cohort n=404 / +9.71% / P=0.963.

Nine files listed by the operator as carrying the superseded figure (re-enumerate with `git grep -ln "10\.99%\|n=344"` first — list is from commit `0f93a81`, may be stale after Window D's merges):
- `00_ADMIN/APPROVALS_REGISTER.md`
- `03_DECISIONS/ADR-0050_t4m-proj-flat-measurement-stake-reactivation.md`
- `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md`
- `04_EXECUTION/PLAN.md`
- `04_EXECUTION/SESSION_PRIMER_VC6_2026-08-04.md`
- `04_EXECUTION/TODO_NEXT.md`
- `05_RESEARCH_EXPERIMENTS/PROJECT_ASSESSMENT_2026-07-30.md`
- `11_MEMORY_HANDOFF/MEMORY_BANK.md`

Correct in place with a pointer to GG-159; supersede visibly (ADR-correction style), do not rewrite archive-shaped file history.

**Two non-mechanical corrections that matter more than the number:**
(a) Tercile monotonicity is dead — the one monotonic row in the original table was the mis-specified reconstruction; under the production formula the middle tercile dips in both cohorts. Kill any "pick the right coefficient and the scaler cleans up" phrasing. §2(b)'s retraction stands on firmer ground, say so explicitly.
(b) The "five edge definitions" table is not five independent rows — `fee_net_edge` IS the cascade output (799/799 row match, max abs diff 0.000000), so three of five rows are mathematically forced to agree. Collapses to one verified number + one genuinely independent row (`gross_edge`). Kill any "robust across five independent edge definitions" phrasing — it's false. This is a real epistemic downgrade of the project's central positive result; do not soften it.

### Task 2 — epoch-12 citation rule into ADR-0050 §8
Make it structural (name the script + its data source, not advisory prose) so the table can't drift from the ledger. **Must be recomputed from live data at execution time** — cohort has grown since the 2026-08-04T03:28Z snapshot (46 positions were open then). Reference figures at that snapshot for reproduction-check only, do not just copy them forward:
- n=141 closed, +$48.52 on $122.25 stake, +39.69% ROI, 42.6% win
- top 5 winners = 71.18% of P&L
- excluding top 10: n=131, −$10.01 on $115.70 stake, **−8.65%** (NOT −8.84% — that figure was a bad-denominator approximation from the 2026-08-03 strategic review, superseded by Window A's exact figure; do not propagate −8.84%)
- LOW stratum (<10c, 10-contract cap binds): n=30, +167.78% ROI, 16.7% win
- 0/83 tickers held both directions; 141/141 ADR-0050 sizing conformance

### Task 3 — fold Window B's re-check date into `MARKET_EXPANSION_ACTION_PLAN.md`
Explicit dated item: **2026-08-09**, threshold ≥200 post-fix depth observations/family, projected crossing 2026-08-08. State plainly: projection ≠ clearance, table re-runs on the date. Also record: no pre-fix depth data exists, because `--depth-sample-per-family` and `_balanced_sample()` shipped in the same commit (T-412) — there is nothing to compare against.

### Scope fence (unchanged, still binding)
No `src/` change, no sizing change. ADR-0050 **amendment** only — do not supersede it, do not touch the $1.00 stake or the 10-contract cap. Do not re-run VC6's analysis — consume it (`05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md` and `GOVERNANCE_GAP_LOG.md` GG-159 are the sourced facts, already merged to `origin/main`).

## State at park time
- Worktree created, on branch `session/20260805T011351Z-gg159-propagation-citation-rule`, clean (no file edits yet).
- Claim row pushed directly to `origin/main`'s `SESSION_CLAIMS.md` (script pushes claims independent of the worktree branch).
- Adversarial Q1-Q6 review: **not run**, flag per Hard Rule — do not silently treat as passed.
- Next session: resume from this file, re-verify the 9-file list and GG-159's content are still current on `origin/main` before editing (Hard Rule 10), then execute Tasks 1-3 as specified above.
