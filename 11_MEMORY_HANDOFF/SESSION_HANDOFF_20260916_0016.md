# Session Handoff — 2026-09-16T00:16Z

<!-- session-meta
task_id: T-550
tier: STANDARD
timestamp: 2026-09-16T00:16:00Z
commit: cd59841
one_line_summary: EXP-027/HYP-012 verbatim re-run: UNDERPOWERED (clean_n=14 vs n*=2610); GG-281/283/284 registered, none fixed
gg_touched: GG-281, GG-283, GG-284
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** Task complete. **Tier:** STANDARD (rule 3 — GG-283/284 opened this session, no `src/` change).

**Last commit:** `cd59841` (branch `session/20260915T235134Z-exp027-rerun-weeks1-2`) — pushed, not merged.

## Status
Phase 6/7 ACTIVE. Tests not re-run (verbatim, no `src/` diff). No live capital. VPS/cron/paper bets untouched (out of scope).

## ⚠️ STRATEGIC DECISIONS

| Decision | Rationale | Ref |
|---|---|---|
| No WAS/WSH ticker fix | Would change cohort mid-run | GG-283 |
| Disclosed wrong "Weeks 1-2" premise | Don't absorb a wrong premise | GG-281 |
| No CLE_JAX cause-chase | Out of scope; Rule 11 | GG-284 |

## Tasks Completed

| Item | Result |
|---|---|
| T-550 verbatim re-run | UNDERPOWERED — clean_n=14, n*=2610.35, P&L/bet=+0.032 |
| GG-281 | Premise wrong — only Week 1 resolved |
| GG-283 | No "WAS" in ticker alphabet — drops WAS_PHI. Not fixed. |
| GG-284 | CLE_JAX zero archived rows. Cause unconfirmed. |
| DECISION_LOG entry | Appended |
| GG-276 check | Unrelated to the two exclusions |

## ONE THING PENDING

Branch pushed, not merged — MICRO fast-path merge eligible (no `src/` change), pending divergence check. GG-283 fix is scoped but must not touch this cohort without fresh pre-registration. GG-284 cause handed to archiver-owning session.

## Key Constraints
No live capital until G6. Scope fence held: script (no fix needed), `exp_output/`, gap-log, DECISION_LOG only.

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Read MEMORY_BANK.md + this file. EXP-027 2026 re-run: UNDERPOWERED.
```
