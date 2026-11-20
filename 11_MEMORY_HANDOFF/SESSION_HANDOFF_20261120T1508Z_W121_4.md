# Handoff W121.4 - Live Terminal panels (PLUMBING)
Rules read: first line of COMMON_RULES_W121.md = "# Wave 121 common rules". Model: Sonnet (block said Haiku; D-34 only bars Opus/Fable).
vision_pillar: PLUMBING. surface_delta: +4 panels/keys on the Live Terminal, +1 launchd job on the Mac, 0 box components.

## Built (PR #537, merged on green CI, 7m)
- shadow.candidates_today: per sport x candidate (router_v2 / nba_depth / nhl_v2): rows, same arm as v1, agree %, errors, rows that differ (40 cap).
- D6 panel: hover on wired/registered now names each cell, wired vs not (n/7 layers).
- weekly_look: newest exp_output/EVIDENCE_WEEKLY/*.json; "first look not run yet" until it exists (it does not today).
- box_health: disk % and days to 90% (disk_guard, same number the healthcheck uses) + Mac copy from LAST_RUN.json.
- Tests: tests/test_w121_4_terminal_panels.py (6); test_web_dashboard_terminal.py key list extended. 65 dashboard tests pass.
- Checks: Playwright 1440px, seeded NBA rows, 0 console errors; 8 rows -> 75% agree rendered.
## Not done / caveats
- node is not installed on this Mac, so `node --check` did not run; the Playwright run (page script executes, 0 errors) stands in for it.
- Mac-copy row reads ~/PredictionMarketEvidence/LAST_RUN.json: it shows only where the server runs on the Mac. On the box it reads "not visible from this host". Window decision: ship the status to the box, or serve a Mac-side dashboard.
- Seeded screenshot rows were removed; screenshot is in the session scratchpad only.
## Part C
Decision 8 approved 11-18 22:44 PT. Ran evidence_pull_launchd.sh install; `launchctl list` shows com.predictionmarket.evidence-pull (loaded, exit 0, Sunday 03:00 local). Mac weekly job loaded: YES.
