# Session primer — VC6 vig cascade verification (T-413)

**Status: COMPLETE. All work committed and pushed. Nothing pending.**

Branch: `session/20260804T045829Z-vc6-vig-cascade`
Worktree: `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260804T045829Z-vc6-vig-cascade`
Commit range: `383605b..5f807dd` (3 commits: session claim, VC6 script+memo, GG-159 registration)
Pushed to origin, remote branch exists. No PR opened (not requested).

## What was done

Closed `PROJECT_ASSESSMENT_2026-07-30.md` §8 Validation Check 6. Verified
row-by-row (778/778 and 799/799 exact matches) that the assessment's headline
"raw − 2.0·vig" T4M-PROJ reconstruction (n=344, ROI +10.99%) does NOT match
`paper_trader.py::open_position()`'s real cascade (L460-468). The real
cascade's code-verified output is n=388, ROI +9.65% (as-of-2026-07-30 cohort)
— identical to the assessment's own, differently-labeled "-1.0·vig"/
"fee_net_edge" rows.

Qualitative verdict ("abs() defect, not the model, made T4 look negative")
survives. Specific headline number is corrected. §8 Assumption 1 is falsified.

Also independently reproduced operator-supplied epoch-12 reference figures:
6 of 7 exact, 1 (excl-top-10 ROI: -8.65% vs ref -8.84%) close but not exact,
judged non-material and flagged transparently in the memo.

## Deliverables (all committed)

- `scripts/vc6_vig_cascade_verification.py` — reproducible script
- `05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md` — full memo
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-159 registered (OPEN, citation-correction only)

## Scope fence honored

No `src/` change, no sizing change, no epoch bump, no ADR.
`MARKET_EXPANSION_ACTION_PLAN.md`, `MARKET_UNIVERSE_SURVEY_SPEC.md`,
`SEGMENTED_POOL_ARCHITECTURE.md` untouched.

## If resuming

Nothing left to do for this task. If the user wants the branch merged, that's
a separate ask (not made yet). This primer file itself is a temporary
artifact — safe to delete once the user confirms they've read the diff.
