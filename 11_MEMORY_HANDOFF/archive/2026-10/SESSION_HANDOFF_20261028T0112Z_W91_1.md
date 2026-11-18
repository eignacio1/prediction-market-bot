# SESSION HANDOFF — W91.1 ride cells (EXP-042)

```
vision_pillar: PROOF (Part C: PLUMBING)
gap_measure: P1/P3 — ride cells pre-registered; ride cells tested out of sample
gap_delta: pre-registered 0 -> 11 (EXP-042, sha256 4efbc15f...ab35); tested OOS 0 -> 0 of 11 (backward test VOID); forward look dates registered
pattern_sweep: ADR-0076_DRAFT / "DRAFT ADR-0076" / "ADR-0076 (DRAFT)" swept; live refs fixed (ACTIVE_QUEUE header, CLAUDE.md G6 lines); archives/claims/handoffs/DECISION_LOG left as history. Also swept `safe_out()` isolation fix across 12_EXPLORATORY/ride_cells (only backward_w91.py had raw writes).
surface_delta: none (no new live component; research code in 12_EXPLORATORY only)
```

## Result
- EXP-042 frozen before any new row read. Backward test VOID: overlap check on 2026-08-01..10-27 (1,902 matched obs) — same-5c-bucket 83.8% < 85% bar (mean diff -0.0002 passes; per-cell CI check not evaluable). No pre-August date scored. All 11 cells IN_SAMPLE, RIDE empty, `ride_cells.toml` unchanged.
- GG-1253 validated: ticker HHMM as ET matches rules_primary 100% (non-HIT families), 99.57% KXMLBHIT. Resolved.
- Registered: GG-1340 (hourly method fails bar), GG-1341 (Kalshi rate limit), GG-1342 (no scored look until MLB resumes). GG-204, GG-285 RESOLVED by ADR-0076.
- Forward looks (full effect; PASS needs half-effect judged n): cell 6 ~2026-12-21; 3 04-11; 10 04-15; 5 04-28; 2 04-29; 4 05-06; 1 05-18; 9 06-07; 8 06-11; 7 06-17; 11 06-25 (2027).
- Part C: ADR-0076 file renamed/ACCEPTED; ADR-0057 and ADR-0028 got partial-supersession lines; CLAUDE.md Gate structure / Capital status / Hard Rule 2 parenthetical updated.

## Deploy / t4-mlb
PR #355 (6480b6b) touched only `12_EXPLORATORY/ride_cells/` and `tests/`. Its own main run was cancelled (superseded by later docs-only pushes); the latest main run was still pending/in progress at close. t4-mlb decision: no restart needed (no imported file changed). Next session: confirm the latest main Test Suite is green.

## Open
- Optional: new EXP for a finer-than-hourly price source (GG-1340). No operator decision required.
