# SESSION HANDOFF - W105.1 B-051 blend-weight test (2026-11-06)

```
vision_pillar: PROOF
gap_measure: P3 (blend-test looks scheduled per sport, with dates; D3 unchanged)
gap_delta: NBA 12 cells scheduled, looks at 100/200/300/400 games (v3: 25/50/75/100), final-look dates 2026-12-29 (v3) to 2027-02-15 (v1 team total), hard cap 2027-04-20. NFL/NHL/MLB named, not scheduled.
pattern_sweep: n/a (no defect fixed)  [one CI-found lint (.replace in run_calendar) fixed; sibling scan: no other blend_test/ file affected]
surface_delta: +1 read-only allowlisted box task (blend_test_read); no cron, service or workflow
stage: engine views unchanged (aggregated/interpreted); blend weight = applied-against-market measurement, descriptive only
```

Status: DONE. PR #441 merged (squash 74729df), CI green. Pre-registration frozen on origin:
`12_EXPLORATORY/blend_test/BLEND_TEST_PREREGISTRATION_20261106.md`.

Result: games needed at w=0.25/0.5 (4-look OBF, 80% power) range 105-13013; v3 total and team total are underpowered by design. Modal outcome INCONCLUSIVE ~55%.

Notes for the next window:
- Claim row (SESSION_CLAIMS.md) reads "T-TBD GG-reserve-3"; no T-/GG- numbers were consumed by this block.
- Overlap with EXP-044/b/c rows is disclosed in the pre-registration §conflict; operator may hold NBA looks until 2027-01-31.
- blend_test_read has not been run on the box; first call expected to print counts only.
- ESPN finals are fetched live by the task; a fetch failure drops games silently from n (counts will read low, never leak).
