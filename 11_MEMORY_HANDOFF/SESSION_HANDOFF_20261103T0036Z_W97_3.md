# SESSION HANDOFF W97.3 (flex lane) - PARTIAL - 2026-11-03 ~00:40Z

vision_pillar: PROOF (visibility) + PLUMBING
gap_measure: games with a plain-English pick line on the dashboard per night; MLB arms idle with a written reason; peak memory per runner
gap_delta: picks 0 -> 4538 picks / 161 games on a box dry run (2026-11-02), recurring cron NOT installed; MLB idle reasons 0 -> all three MLB arms (#393); memory: peaks measured (table in results_W97_3.md), builder 141 -> 19.8 MB. Sources: box dry run, /proc VmHWM, dmesg 2026-11-03
surface_delta: +1 cron (picks builder, registered, NOT installed; held by Hard Rule 14: surface RED on a silent NBA engine v3 arm and another block's uninstalled NBA events cron)
pattern_sweep: n/a (no defect fixed); the streaming fix to tail_rows applies to the new module only (no other whole-file tail reader in the picks path)
Claim T-1580..1582 / GG-1580..1582. PRs: #389, #392, #393 (all CI pass, merged). Results: 12_EXPLORATORY/picks_sheet_w97/results_W97_3.md

## Done
- Part A: builder, panel, tests merged and deployed; box dry run OK (39 s, 19.8 MB). Panel shows its missing-file message until the cron runs.
- Part B: silent-arm IDLE text states the reason; alarm logic and GG-163 detection unchanged; tests pin both. SemanticFloorViolation explained (2026-10-16: no-player-markets postseason day); 2026-07-10 hit unexplained (GG-1582).
- Part C: memory table written. FINDING (GG-1581, HIGH): 20 OOM kills in ~90 min; T3 shadow runners stack 2-3 deep with no flock. Not fixed (edits existing cron lines, outside PERMISSIONS).

## Not done
1. Install deploy/cron.picks_sheet (new BEGIN/END block, crontab backup first) when `runtime_registry.py live` is GREEN apart from this line; then read the panel back after a 22:37Z/05:37Z run.
2. GG-1581 fix by the strategic window: flock -n per T3 runner + stagger, after checking each arm's pre-registration; find why an NBA pregame T3 run lasts 62 min.
3. GG-1580 (pick reasons) needs a permissioned runner change.

## Ticket states (ROLLING_BACKLOG not edited)
B-026: PARTIAL (built/merged/deployed; cron held; no night read back). B-006: DONE (#393; explanation recorded). B-007: PARTIAL (measured; GG-1581 open, fix needs permission).
Operator decisions: none required; GG-1581 is the one that matters for the window.
