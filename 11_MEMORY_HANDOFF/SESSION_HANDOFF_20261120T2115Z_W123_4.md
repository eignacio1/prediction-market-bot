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
