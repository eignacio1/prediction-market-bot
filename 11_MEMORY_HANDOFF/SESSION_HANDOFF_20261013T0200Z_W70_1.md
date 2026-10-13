# SESSION HANDOFF - W70.1 (T-853..T-855) - re-arm forward test; NFL fill audit

vision_pillar: EXECUTION
gap_measure: E1/E2/E3
gap_delta: none. Re-arm not done; NFL +0.39 audited (no post-kickoff fills) and judged non-evidence (GG-624).

Status: PARTIAL

## Done
- PR #237 merged (`5b5c693`), CI green; deployed (box HEAD `5b5c693`, tree clean of tracked edits).
- Report re-run (--no-act): shadow/MLB and NFL cancel "failures" reclassified already_terminal (360 / 229).
- NFL audit scripts + results in `W65_2_forward_test_on_results.md` "Read-back W70.1".

## Not done / blocker
- `deploy/demo_fill.override.env` NOT deleted: cancel_fail_rate still tripped by 8 real paper KXMLBHIT cancel failures (resting, 404 then 503) - GG-623. 7 paper orders left resting on demo.
- Control-arm read-back (GG-586/570/571), GG-564 split, governance-scan/panel comparison: need switches ON and the NHL nightly / NFL 10-15 runs.
- ACTIVE_QUEUE 70.1 row: updated with this status.

## Operator decisions
- Re-arm anyway (accept a re-trip) or fix the MLB-HIT cancel path first? Recommend fix/diagnose GG-623 first.
