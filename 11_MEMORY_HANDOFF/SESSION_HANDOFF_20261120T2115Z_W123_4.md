<!-- session-meta
task_id: W123.4
tier: MICRO
timestamp: 2026-11-20T21:15:00Z
commit: 590fd0c
one_line_summary: W123.4 H4 execution: two-sided quoting NOT SUPPORTED (0 of 18 cells net > 0, spread minus fee negative everywhere); parked for R&D
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, EXECUTION
gap_measure: P2, E3
gap_delta: P2 H4 verdict issued (RESULT.md @ 8c37f94); E3 pooled adverse selection -0.065 on 145 fills / 1,593 unfilled
pattern_sweep: n/a (no defect fixed; snapshot-spacing assumption error logged in WINDOW_ERROR_LOG)
surface_delta: 0
-->

# Session handoff - W123.4 H4 execution (2026-11-20)
Common rules first line: "# Wave 123 common rules". Branch session/20261120T200257Z-w123-4-h4-execution.
**Measure moved:** PROOF / EXECUTION - H4 verdict NOT SUPPORTED (frozen 15-min rule literally UNDERPOWERED, 0 fills; 35-min sensitivity run 70,346
fills, 18 cells judged, none net positive, gross negative in all). Adverse selection pooled -0.065 (filled did better; RIDE alone 70% vs 81%).
**Deliverables:** scripts/h4_quote_sim.py + tests/test_h4_quote_sim.py (3 pass); 12_EXPLORATORY/edge_location/h4_execution/RESULT.md + 2 JSON;
HYPOTHESIS.md Addenda A (pre-result) and B (post-0-fills, disclosed); H-EDGE-4 registry row; queue row 123.4.
**Gaps:** (1) archive spacing is 19-30 min and `close_time` is expiration: no horizon < 24h and no game start in the archive; (2) no consensus
fair; (3) no depth ladder (DEPTH_ARCHIVE absent) so queue/size untested; (4) window error: Addendum A assumed 3-8 min spacing unverified.
**pattern_sweep:** none (analysis only). **surface_delta:** 0 (no cron/service). **Data staged:** scratchpad only; box was read-only (ssh).
**Next:** if H4 is revisited, capture sub-minute top-of-book + game start for NBA, then re-register.
