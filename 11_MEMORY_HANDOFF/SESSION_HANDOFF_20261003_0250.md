# Session Handoff — 2026-10-03 (cloud block 50.1)

<!-- session-meta
task_id: 50.1
tier: STANDARD
timestamp: 2026-10-03T03:20:00Z
commit: 1dd4d660
one_line_summary: 50.1 (cloud): GG-419/427/428 + pycache ignore fixed, queue rotated, GG-400..429 triaged; PR #157 green, unmerged (merge restarts t4-mlb via CI deploy).
gg_touched: GG-419, GG-427, GG-428 (RESOLVED); GG-400..429 triaged (recommendations only)
adr_touched: none
plan_deliverable_moved: no
-->

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| Claim guard: refuse unless HEAD ⊆ origin/main | DECISION_LOG 2026-10-03 50.1 |
| Network tests opt-in; CI keeps them on | same |
| pyarrow/nba_api lower bounds only | same |
| PR #157 left for operator (merge → CI restarts t4-mlb) | same |

## What changed (branch claude/peaceful-heisenberg-51g2ee, PR #157)
- Items 1-5 of the block done; suite 3620 passed / 0 failed; CI green.
- Triage: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG400_429_TRIAGE_2026-10-03.md`.
- **Correction:** 49.x WAS deployed by CI (VPS `077558b1`); `deploy.yml` restarts t4-mlb + dashboard on every code push.
- Bet count / G6: not re-checked this close-out.

## New discoveries (handoff only, Hard Rule 11)
- **`scripts/close_session_claim.sh` has the GG-419 defect** (pushes HEAD:main). Run it only from a clean origin/main checkout until fixed.
- GG-419/427/428 RESOLVED but not yet moved to the archive.
- DEPENDENCY_LOCKS disagree with pyproject (sklearn, scipy).

## One thing pending
LOCAL: `bash scripts/arm_shadow_crons.sh` before NFL Week 5 (10-4). Then operator merges PR #157 when a t4-mlb restart is acceptable.

## Carry (local / operator)
a) arm_shadow_crons (14 refused files, --allow each) · b) browser check against running dashboard · c) authorizations: --include-postseason, VPS jobs, EXP-034, ADR-0070, CI t4-mlb restart policy · d) apply triage.

## Resume
`git fetch origin && git checkout -B work origin/main`; read this file and PR #157.
