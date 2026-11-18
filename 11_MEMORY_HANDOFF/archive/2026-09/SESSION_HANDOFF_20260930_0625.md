# Session Handoff — 2026-09-30T06:25Z

<!-- session-meta
task_id: T-596
tier: MICRO
timestamp: 2026-09-30T06:25:00Z
commit: 5a17e79
one_line_summary: EXP-029 (T-596): frozen EXP-028 model scored once vs KXMLBHIT market on 215 games -> HARMFUL (dBrier -0.0039).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** operator-initiated. **Last commit:** `5a17e79`.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| EXP-029 verdict HARMFUL; pre-game cell on this feature set not worth activating; D4 permutation criterion re-specified one-sided (disclosed post hoc in pre-reg) | DECISION_LOG 2026-09-30 |

## What changed
- exp_output/EXP-029/* (join, controls, gate, lock), pre-registration + results summary. No src/ change.
- Extended matrix + ORIGINAL copy are gitignored in the worktree (not committed).
- Frozen-window result is one-shot (lock file); do not rerun.

## One thing pending
Register gaps from "GAPS FOUND -- FOR REGISTRATION" in EXP029_market_gate_RESULTS_2026-09-30.md (fresh highest-GG check first). Q1-Q7 formal answers not run. Stray-branch sweep output below.

## Resume
`scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`
