# Session Handoff — 2026-09-30T05:30Z

<!-- session-meta
task_id: T-595
tier: STANDARD
timestamp: 2026-09-30T05:30:00Z
commit: a367019
one_line_summary: T-595: 40.3 landed, VPS provenance snapshotted (13/13 verify), T4M-PROJ model_identity stamped forward-only, claim re-check fixed.
gg_touched: GG-321, GG-322
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** deliverables D0–D4 complete. **Last commit:** `a367019`.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| Two-label T4M-PROJ identity; shrunk registered forward-only; allowlist stays inert | DECISION_LOG 2026-09-30 T-595 row |

## What changed
- D0 `6d29962`; D1 `9d36ba7` snapshot + verifier; D2 `763939a` stamp/passthrough/registry; D3 `214d517`,`f68d784`; D4 `a367019`.
- Tests: 296 passed on affected suites, 36 evidence/epoch. Nothing deployed, no row touched (GG-228).
- Bet count vs G6 not re-checked this close-out — see live governance scan.

## Hand-backs
- `.git/index.lock` (PID 33525) blocks the shared-tree `git checkout HEAD -- CLAUDE.md 02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md 02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md 03_DECISIONS/ADR-0014_per-band-decision-tree-mechanics.md`; not bypassed. Backups in scratchpad `shared_tree_backup/`.
- Do NOT merge/deploy T-589 branch `session/20260930T001343Z-t4-ledger-durability` (MissingModelIdentityError) before D2 is deployed.

## One thing pending
Operator decision: deploy D2 and wire `is_countable_evidence` into counters (rows are not countable until then).

## Resume
`scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`; read the T595 results summary.
