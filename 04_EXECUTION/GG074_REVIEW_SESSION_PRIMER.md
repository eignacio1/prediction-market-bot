# GG-074 Monthly Grounding-Docs Staleness Review — Session Primer (IN PROGRESS, parked 2026-07-23)

**Delete this file once the review is fully complete and its findings are folded into DECISION_LOG.md / TODO_NEXT.md.**

## Where this session is running
Worktree: `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260723T004002Z-gg074-grounding-docs-staleness-review`
Branch: `session/20260723T004002Z-gg074-grounding-docs-staleness-review`
Session-start protocol (Steps 0-4, Q1-Q6) already completed earlier this session — do not re-run unless resuming in a genuinely new session.

## Task
First-ever execution of GG-074 (monthly grounding-docs staleness review — adopted 2026-07-06, never run before this session). Reviewing 28 files with "Last reviewed" dates 2026-05-21 to 2026-05-29. Rule: **an old date does NOT automatically mean wrong content** — read each file fully, cross-check substantive claims against current reality (CLAUDE.md, MEMORY_BANK.md Current State Snapshot, GOVERNANCE_GAP_LOG.md), then either fix genuine drift in place + update header, or confirm accurate + refresh header with a "verified current, no drift found" note. Never silently bump the date without reading.

## Done (6 of 28 files) — all edits applied, NOT yet committed as of parking
1. `00_ADMIN/COMMUNICATIONS_PLAN.md` — no drift, header refreshed.
2. `00_ADMIN/GLOSSARY.md` — fixed: venue-selection row said "not yet selected"; ADR-0003 was ACCEPTED 2026-05-23 (Kalshi primary, Polymarket US secondary KYC-gated). Header + confidence updated.
3. `00_ADMIN/PROJECT_CHARTER.md` — fixed: §4 Constraints Venue row said "TBD — requires ADR-0003"; corrected to decided/ACCEPTED. Header updated.
4. `00_ADMIN/STAKEHOLDERS_RACI.md` — no drift, header refreshed.
5. `00_ADMIN/ACCESS_REQUESTS.md` — fixed: ACC-0005 (production compute, VPS 157.230.91.33) showed PENDING; it's been live since Phase 6 cutover (~2026-06). ACC-0004 (secrets vault) clarified as accepted-for-now OPEN per T-352/GG-093, not stale. ACC-0003 (Polymarket) confirmed still-accurately PENDING.
6. `00_ADMIN/CHANGELOG.md` — found significant drift: no entries since 2026-05-30 despite ~8 weeks of major changes. Full backfill judged out of scope for this pass → **registered as GG-133 (OPEN)** in `GOVERNANCE_GAP_LOG.md` (inserted between the GG-132 block and "## Gap Registration Template" heading). Header updated to reference GG-133 rather than being silently bumped.

**Key reusable fact discovered:** ADR-0003 (venue selection) is ACCEPTED 2026-05-23 — Kalshi primary (CFTC-DCM), Polymarket US secondary (KYC-gated), PredictIt not selected. Check every remaining file for stale "venue TBD/pending/placeholder" language — this was the single most common drift source in 00_ADMIN.

**GG numbering:** GG-133 was verified free via `grep -oE "GG-[0-9]+" 03_DECISIONS/GOVERNANCE_GAP_LOG.md | sort -t- -k2 -n -u | tail -5` (highest was GG-132) and cross-checked against TODO_NEXT.md/SESSION_CLAIMS.md. **Re-verify freshly against origin/main at merge time** — GG-131/GG-132 collision precedent shows concurrent sessions can grab the same ID; if GG-133 is taken by the time this merges, renumber consistently across GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, and TODO_NEXT.md (see that precedent's "Numbering note" for the exact renumbering procedure).

## Not yet done — remaining 22 of 28 files
Same read → cross-check → fix-or-confirm → header-update pattern. Check each for stale venue-TBD language first, then read fully for other drift.

- `01_SPEC/`: NON_FUNCTIONAL_REQUIREMENTS.md, SCOPE_IN_OUT.md, VISION_OUTCOMES.md, REQUIREMENTS.md
- `02_ARCHITECTURE_DESIGN/`: DEPENDENCIES.md, RESILIENCE_FAILURE_MODES.md, SYSTEM_CONTEXT.md, THREAT_MODEL.md, INTERFACES_CONTRACTS.md, ARB_FRAMEWORK.md, BAND_ASSIGNMENT_FRAMEWORK.md, STRATEGY_OVERVIEW.md (1131 lines — largest, needs multi-part reads)
- `07_TEST_VALIDATION_EVIDENCE/`: TEST_STRATEGY.md
- `08_MODEL_RISK_GOVERNANCE/`: CHANGE_CONTROL.md, DATA_PROVENANCE.md, MONITORING_DRIFT_PLAN.md, METHODOLOGY.md, ASSUMPTIONS_LIMITATIONS.md, MODEL_CARD.md, PERFORMANCE_METRICS.md, QUALITATIVE_SIGNALS.md, VALIDATION_SIGNOFF.md

## After all 28 are done
1. Re-read `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` fresh (Hard Rule 10 — concurrent sessions may have edited it; `00_ADMIN/APPROVALS_REGISTER.md` had foreign uncommitted edits noted earlier this session) and append a consolidated findings entry: files reviewed, drift found/fixed per file, GG-133 (and any further GGs registered for the remaining 22 files).
2. Re-read `04_EXECUTION/TODO_NEXT.md` fresh, update the GG-074 Standing Item to record this review actually ran, dated 2026-07-23 (currently just says "adopted 2026-07-06" with no run history).
3. Delete this primer file.
4. Commit (path-scoped, never `-A`/`-a`), push, open PR / merge to main per this project's established session-end pattern. Verify GG-133 ID is still free against fresh `origin/main` before finalizing — renumber if collided (see precedent above).
5. Consider running `/session-end`.

## State at parking time
All 6 files' edits are applied on disk in the worktree but **uncommitted** until the commit below lands. Committing now, path-scoped, as a checkpoint — do NOT wait until all 28 files are done to make the first commit, given context pressure.
