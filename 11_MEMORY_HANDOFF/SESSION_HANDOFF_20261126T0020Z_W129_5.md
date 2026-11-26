# Session handoff — W129.5 PROOF / measurement (Sonnet)

<!-- session-meta
task_id: W129.5
tier: MICRO
timestamp: 2026-11-26T00:55:00Z
commit: 36e16f9
one_line_summary: W129.5 merged (PR #592): D6 from one box source (18/129, static 0 beside it), distance table, hypothesis registry 42->73 rows, 0 unregistered.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: D6 sources; hypothesis registry rows
gap_delta: D6 sources 2 -> 1; registry rows 42 -> 73 (DISTANCE_TABLE_W129.md, hypothesis_registry_check.py)
pattern_sweep: grep D6 readers in scripts/ src/ .claude/ - only distance_to_optimum.py computed a repo-static D6; box d6_read unchanged.
surface_delta: +1 Docs Guard step (alarm-only), +2 one-shot box requests, 0 crons/services.
-->

**Strategic decisions this session:** None - implementation-only.

**Branch:** session/20261126T001200Z-w129-5-d6-one-source · **Deliverable:** D6 from one source, distance table, hypothesis registry (B-110)

## What changed
- `scripts/distance_to_optimum.py` D6 = newest box `d6_read` result with its ran-date; repo-static count printed beside it, labelled static.
  Today: **18 / 129 wired** (box d6_read 2026-11-25T04:34Z, `results/20261125T0500Z_w1271_d6_read.md`); repo-static 0 / 129.
- Why 117 vs 129: W125.3 (e9bf88b, 2026-11-23) added 12 NOT_IMPLEMENTED combo cells; the box checkout lagged. Why 18 vs 0: the static
  call passes no orders / fills / box rows, so layers 6-7 read 0 by construction.
- 5 parsing tests in `tests/test_distance_to_optimum.py` (34 pass).
- `04_EXECUTION/DISTANCE_TABLE_W129.md`: every B/D/E/P with source and date. E1-E3, P1-P3 are the 2026-11-12 box values (STALE, MLB
  only). RUNNING SITREP untouched.
- `HYPOTHESIS_DOCTRINE.md` §II.8 backfill; `scripts/hypothesis_registry_check.py` (alarm-only) + test; Docs Guard step.
- Box requests in the PR: `20261126T0030Z_w1295_d6_read`, `20261126T0031Z_w1295_distance_read`.

## For the SW-10 window (read first)
- Box results landed 11-26 and are quoted in the table (follow-up PR): `distance_read` gave P1-P3 = 25/49, 25 verdicts, P3 unavailable.
  `d6_read` TIMED OUT (exit 124, empty), so D6 stays 18 / 129 from the 11-25 read; the timeout is undiagnosed. E1-E3 still MLB-only, ledgers 10-29.
- Backfill covers every PREREG file (no EXP-001..024 PREREG files exist). Verdict cells marked "not re-read here" quote the file head only.

## Measures
vision_pillar: PROOF (P1/P2 counting) · gap_measure: D6 sources · gap_delta: 2 -> 1
registry rows 42 -> 73; unregistered pre-registrations found: 31 on first run (29 after fixing the EXP-W id false positives, then 3 more
once the old preamble was replaced); 0 now.
pattern_sweep: grep D6 readers in scripts/ src/ .claude/ — only distance_to_optimum.py computed a repo-static D6; the box d6_read is unchanged.
surface_delta: +1 Docs Guard step (alarm-only), +2 one-shot box requests, 0 crons/services.
directive_conflicts: none. operator decisions: none needed.
Open gaps touching D6: GG-2010, GG-2011, GG-2012.
