# Session handoff - W127.4 dense capture cut to pass its gate (2026-11-25 02:45Z)
<!-- session-meta
task_id: W127.4
tier: MICRO
timestamp: 2026-11-25T04:25:00Z
commit: b8eae18
one_line_summary: W127.4 dense capture cut 159.2 to 30.5 MB/day; box gate now PASS; install awaits operator approval
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: P3
gap_delta: none until installed; capture 159.2 -> 30.5 MB/day, gate REFUSE -> PASS (box read 2026-11-25T04:05Z)
pattern_sweep: only archive_dense_* scripts use the MEASURED/print constants; nothing else found
surface_delta: 0
-->

Rules read: COMMON_RULES_W127 first line "# Wave 127 common rules".

## What changed (PR on branch w127-4-dense-cut; code only: scripts/archive_dense_capture.py, scripts/archive_dense_install.py, tests)
- PART A (dry runs on the live public API, 02:34Z, evening slate; gz bytes per run): props 23,740 (28 req) · games 4,296 (21 req) ·
  prints 292,151 (115 req, 9,437 rows kept of 114,149 scanned). Gate constants (11-24 00:25Z peak): props 118,859 x 33 = 3.9 MB/day,
  games 34,167 x 288 = 9.8 MB/day, prints 505,150 x 288 = 145.5 MB/day. **Prints were 91% of the 159.2 MB/day.** Props and games were never the problem.
- PART B: only the prints stream was cut. Props (H1) and the last-3h 5-min game snapshots (H4) are unchanged, in full. Prints now keep
  only the families H3 named (NBA player props, NBA team totals, NBA + NFL game moneylines; H3 RESULT "next test") and only prints
  inside the market's 3 h pre-start window (same window as the game snapshots; start estimated as occurrence - nominal duration, +/- 30 min).
  Dropped: NHL (H3 goalie closed W118.3), NFL props, spreads, totals. Start map (307 markets) is cached in the prints state file, relisted every 20 min.
  Dry runs after the cut: 33,221 and 33,618 bytes/run (11.4% of uncut, 1,066-1,072 rows). Scaled to the gate's peak: 58,000 bytes/run -> 16.7 MB/day.
- Gate constants updated in archive_dense_install.py MEASURED (prints only; derivation in the comment). Cron lines unchanged (no registry edit).

## MB/day before -> after
159.2 -> 30.5 (props 3.9 + games 9.8 + prints 16.7). Ceiling 80% unchanged. Local gate on the 11-25 02:19Z disk inputs
(68%, 24.9 GB): PASS, projected 71.7% at 30 days; burst 7.9 req/s vs 10 allowed; scale 1.0.

## Open
- PART C DONE: box `archive_dense_gate_read` 2026-11-25T04:05Z (box HEAD = origin/main, deploy_truth OK): **PASS**, 30.5 MB/day, 71.7% at 30 d, burst 7.92 req/s. Results: BOX_TASKS/results/20261125T0401Z_archive_dense_gate_read.md.
- Headroom of ~69 MB/day under the ceiling is NOT spent. Candidates if wanted: NFL prop prints, NHL prints, spread/total prints.
- Known miss: a market first listed after the last 20-min relist and starting inside 4.5 h waits for the next relist (small).
- directive_conflicts: none found. surface_delta: 0 (no new cron / service). pattern_sweep: only archive_dense_* touch these constants.
- operator decisions:
  - approve archive_dense_install   (not installed; gate PASS)

Strategic decisions: None - implementation-only session.
Resume: operator decides archive_dense_install; then verify rows land after install.
