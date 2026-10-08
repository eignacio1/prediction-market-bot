# Session handoff — W60.1 (2026-10-08)

<!-- session-meta
task_id: T-740
tier: STANDARD
timestamp: 2026-10-08T02:30:00Z
commit: fa14f9a
one_line_summary: W60.1: only 107/1952 (5.5%) T4M-PROJ epoch-12 rows have a real demo fill (-$0.40/bet); GG-228 overwrite guard merged.
gg_touched: GG-300, GG-228, GG-527
adr_touched: none
plan_deliverable_moved: no
-->


Status: DONE. Branch session/20261008T020449Z-w60-1-fill-truth; code PR #185 merged as 42754c2, CI green.

- Part A: of 1,952 epoch-12 T4M-PROJ closed rows, 107 (5.5%) match a real demo fill, 1,845 do not (complete fills history back to 2026-05-19). Real fills: -$0.403/bet (CI -0.650..-0.156, 41 games). All rows: -$0.0526/bet (CI -0.148..+0.043, 176 games). GG-300 resolved, GG-527 registered. Details: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W60_1_cohort_fill_truth_results.md`.
- Part B: GG-228 guard merged; t4-mlb restart not_needed; on the VPS. First real exercise: Mon 2026-10-12 14:20 UTC.
- Operator decisions: (1) how the G6 cohort is defined, all intended orders vs filled only (GG-527); (2) whether entry should re-poll order status. Nothing about cohort, status, ledger, sizing was changed.
- GG-300 and GG-228 are RESOLVED in place in the live gap log; the archive move is left to the sweep.
