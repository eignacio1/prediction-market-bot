# Session Handoff — 2026-09-25T06:32Z

<!-- session-meta
task_id: T-577
tier: MICRO
timestamp: 2026-09-25T06:32:17Z
commit: 7cf7a54
one_line_summary: T-577 cohort salvage pre-registered analysis complete -- UNRECOVERABLE verdict, only n=35 CONFIRMED-REAL is usable.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** Task complete, clean cutover.
**Last commit:** `7cf7a54` (already on origin/main — pushed directly in a prior segment of this session)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Paper bets:** unchanged this session (read-only analysis task; no ledger writes)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T-577 cohort declared UNRECOVERABLE (trigger (a)) — no combination beyond n=35 CONFIRMED-REAL passes both screens | UNCONFIRMED-CLEAN (n=336) fails Bonferroni bias screen on 2/5 covariates; DUPLICATE-SUSPECT excluded (GG-303) | `T577_RESULTS_cohort_salvage.md` | DS |

Formal `DECISION_LOG.md` entry deliberately **not** written this session — T-577's scope fence bars editing `DECISION_LOG.md`/`GOVERNANCE_GAP_LOG.md` directly. Handoff to session "35.1".

---

## What changed this session

- Delivered T-577's four deliverables (pre-registration, four-tier partition, bias-corrected estimate, UNRECOVERABLE verdict) — already committed as `7cf7a54`; this close-out only produces handoff artifacts.
- No `src/`, `DECISION_LOG.md`, or `GOVERNANCE_GAP_LOG.md` edits (by design).
- Committing two untracked evidence-snapshot JSONs (`exp_output/T577_cohort_salvage/`), path-scoped.

## One thing pending

Session "35.1": (1) log the verdict in `DECISION_LOG.md`, (2) register the two candidate GG items from the results doc's closing section (2026-09-22 mass-cancellation concentration; price/size correlation with Kalshi retrievability).

## Resume command

`scripts/session_delta.sh 7cf7a54` from a fresh worktree, then read `T577_RESULTS_cohort_salvage.md` for full context.

## Step 9 — stray branches (flag only, not mine, not merged)

7 unlanded `origin/session/*` branches found by `sweep_stray_branches.sh 14` at close-out (3–13 days old): `20260915T003401Z-nfl-capture-gap-0912`, `20260918T142928Z-gg291-threshold-backfill`, `20260918T142949Z-install-closeout-fix`(+`-v2`), `20260923T005837Z-vig-grounding-from-archive`, `20260924T045012Z-clv-harness`, `20260924T045227Z-resolved-filter`. This session's own branch landed cleanly on `origin/main`.
