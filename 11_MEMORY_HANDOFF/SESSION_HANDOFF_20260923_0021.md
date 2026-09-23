<!-- session-meta
task_id: T-565
tier: MICRO
timestamp: 2026-09-23T00:21Z
one_line_summary: T4M-PROJ model-vs-market calibration reproduction from live VPS ledger, vs-ADR-0046 comparability verdict (NOT COMPARABLE), and extension to all bands/rejected cohort -- 5/5 deliverables complete.
commit: 2d3321d
plan_deliverable_moved: no
-->

# Session Handoff — T-565

**Strategic Decisions This Session:** None routed to DECISION_LOG.md — governing task block explicitly withheld DECISION_LOG.md/GOVERNANCE_GAP_LOG.md ownership this wave ("31.2 owns them"). Substantive judgment calls (NOT COMPARABLE verdict vs ADR-0046; T1/T2 clean_n=0 root-caused to T1 ledger staleness vs its own epoch floor; `rejected_positions` UNSCORABLE) are recorded as 7 gap candidates in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_RESULTS_calibration_model_vs_market.md` (pushed), for 31.2 to register next wave.

## What changed
- Pre-registered verdict criteria (`T565_PREREGISTRATION_...md`) before any computation — immutable, committed prior window.
- Built `scripts/t565_calibration_model_vs_market.py`: pulls live VPS portfolio snapshots (T4 MLB + main MLB files), reproduces all 13 CLAIM figures exactly (clean_n=765, Brier 0.2191, day-clustered t=2.87, etc.).
- Deliverable 3: live re-check of ADR-0046's own source shows Brier stable but ECE drifted +22% since derivation — verdict NOT COMPARABLE across 4/5 dimensions (filter, directional convention, scope, epoch window).
- Deliverable 4: extended to all bands (T1/T2 MLB structurally clean_n=0, root-caused), NBA/pre-band MLB rows excluded with documentation (no manufactured fields), `rejected_positions` found UNSCORABLE (exchange-side 404s, not risk declines; zero outcome-store overlap).
- Full write-up committed to `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_RESULTS_calibration_model_vs_market.md`.

## One thing pending
Merge `session/20260922T235038Z-calibration-model-vs-market` to `origin/main` (no `src/` changed — MICRO fast-path eligible if `origin/main` unchanged since fork).

## Resume command
```
cd /Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260922T235038Z-calibration-model-vs-market
git log --oneline -5
cat 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_RESULTS_calibration_model_vs_market.md
```
