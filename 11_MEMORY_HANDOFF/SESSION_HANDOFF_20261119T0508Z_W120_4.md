# Handoff — W120.4 (docs only, Haiku-block run by Sonnet 5.5)
rules_first_line: "# Wave 120 common rules" (origin/main COMMON_RULES_W120.md)
vision_pillar: PLUMBING — docs out of line with DOCTRINE 2 -> 0; open PRs 3 -> 1 (#149 left open: unlanded GG-279 work)

## Built
- STRATEGY_OVERVIEW.md and ARCHITECTURE_OVERVIEW.md bodies rewritten to DOCTRINE.md / ADR-0077; link to DOCTRINE, no restating; operator 11-10 21:41 PT quote verbatim; Last reviewed 2026-11-18.
- Old bodies kept verbatim: 00_ADMIN/STRATEGY_OVERVIEW_ARCHIVE_2026-11-18.md, 00_ADMIN/ARCHITECTURE_OVERVIEW_ARCHIVE_2026-11-18.md.
- DOCTRINE.md stack table: both rows dated 2026-11-18.
- Strategies A-J are mapped to arm/layer using only the existing Strategy 0 text; no new strategy added.

## Pointers fixed
ARB_FRAMEWORK.md:9, BAND_ASSIGNMENT_FRAMEWORK.md:9, CHANGE_CONTROL.md:58 (band table retired; EXECUTION_BANDS.md § Live Registry).
## Pointers listed, not edited
- ADR-0009 (lines 8, 130, "Layer 2") and ADR-0075:63 (Strategy J): ADRs immutable (Hard Rule 3); Strategy J / multi-arm Layer 2 text is in the archive.
- Code comments (.py, not docs-only): execution_bands_orchestrator.py:10,36 ("STRATEGY_OVERVIEW.md P6 / Section 5"), scoring_distribution.py:37 ("Strategy I"), complement_lock_scanner.py:21 ("Strategy C") — now resolve to the archive file.
- Historical pointers (CHANGELOG, PLAN, APPROVALS, T597 summary): dated records, left.

## PRs
- #477 closed: superseded by DOCTRINE 1b; registry on main reads "hypothesis closed (<EXP-id>, parked for R&D)".
- #458 closed: landed as #459, #464, #455 (its test file and dash-build footer are NOT on main; the footer is the only unlanded piece).
- #149 left open.

## directive_conflicts
- 04_EXECUTION/visual_dashboard/body.html:125,206,221 and script.js:83,105,151,477 on main still say "fade arm closed (routed)" — contradicts DOCTRINE 1b (11-11 16:51 PT). Needs a code/dashboard fix block (script.js is not docs-only).
## Not mine
- Working tree had uncommitted edits to decision_trees/router.py and shadow_route.py from another session; not committed here.
