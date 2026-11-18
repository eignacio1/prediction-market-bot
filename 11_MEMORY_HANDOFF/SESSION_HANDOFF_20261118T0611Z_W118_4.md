# Session handoff - W118.4 (INFRA: disk measured, retention as code, days-to-90% alarm; install proposed)
Common rules first line quoted: "# Wave 118 common rules". Model: Sonnet. PRs: #521 (Part A + alarm), #525 (Part B/C), both merged on green CI I read.
<!-- session-meta
task_id: B-102
tier: STANDARD
timestamp: 2026-11-18T06:12:00Z
commit: 328361a
one_line_summary: W118.4 disk: measured 87%, retention-as-code + days-to-90% alarm merged (#521, #525); install awaits approval.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: PLUMBING (disk %, bytes freed by dry run, days to 90%)
gap_delta: dry run frees ~3.36 GB; disk 87% -> ~72-73% once installed (box dry run 20261118T0608Z); nothing freed yet
pattern_sweep: grep readers of KALSHI_HISTORY raw/thin in scripts/ src/ 12_EXPLORATORY/ -> 3 readers taught .gz; PRICE_ARCHIVE (~25) and seek reader HELD
surface_delta: +1 cron (disk_retention, registered, paused until approval)
-->

vision_pillar: PLUMBING (infrastructure; room to keep logging). gap_measure: disk % / days-to-90%. gap_delta: none (no gap text or status edited; the gap burner owns those).

## Part A - measured (box `disk_read`, 20261118T0551Z)
| item | value |
|---|---|
| / (vda1) | 24G size, 20G used, 3.2G avail, **87%** |
| growth (health.log, 7d) | **+1.54 pct/day** -> **~2.0 days to 90%** |
| journald | 1681 MB |
| KALSHI_HISTORY raw/thin (Oct) | ~1.9 GB compressible, 3 files over 300 MB |
| PRICE_ARCHIVE | ~2.5 GB across ~25 daily files |
| KALSHI_HISTORY rebuilt_* | 342 MB single file (seek-read) |
Full table: `04_EXECUTION/BOX_TASKS/results/20261118T0551Z_disk_read.md`.

## Part B - retention as code (`src/prediction_market_bot/disk_retention.py`)
- Compress only, never delete: age gate, `.gz.tmp`, sha256 of decompressed stream must equal the original, then rename; skip if free space low.
- Verified-reader targets: KALSHI_HISTORY raw + thin (3 d), `logs/*.json.bak` (14 d). Readers taught `.gz` (Store x3 globs, gate.done_keys, efficiency.load + glob) and tested; Store digest unchanged.
- HELD (readers not taught): PRICE_ARCHIVE, KALSHI_HISTORY rebuilt, audit ledgers. Bytes reported, nothing touched.
- journald capped at 200M on `--apply`.
- Box dry run (`disk_retention_dryrun`, results/20261118T0608Z_disk_retention_dryrun.md): **9 files, ~1880 MB** by compression + **~1481 MB** journald = **~3361 MB** if applied. Held adds ~1819 MB.
- Estimated disk after install: ~72-73% (target under 75%); ~65% once the held targets' readers are taught.

## Part C - guard + proposal
- healthcheck step 10b WARNs when the 7-day growth reaches 90% within 14 days (deploy/healthcheck.sh, tests in test_w118_4_disk.py).
- `disk_retention_install` (+ uninstall, readback) written and tested, **NOT RUN**. Paused registry entry `cron|17 14 * * *|scripts/run_disk_retention.py`. Approval sentence is in ACTIVE_QUEUE "Needs your decision". Install refuses on RED surface budget; backs up crontab; one BEGIN/END block.

MEASURE MOVED: disk now 87%; dry run would free ~3.36 GB (1.88 compress + 1.48 journald); days to 90% at +1.54 pct/day = ~2.0. Nothing is freed until the install is approved and run.

directive_conflicts: none (D-20 operator gets no commands, only an approval sentence; D-29 $0; D-28 all parts ran on existing data).
pattern_sweep: every reader of KALSHI_HISTORY raw_*.jsonl enumerated (board_survey_sports_store x3 globs, gate.done_keys, thin_markets/efficiency load + glob) and taught .gz; PRICE_ARCHIVE (~25 readers incl. nba_engine/live.py) and kalshi_history.py (seek) deliberately HELD.
surface_delta: +1 paused cron (not live), +4 box tasks (dryrun read, install, readback, uninstall), +1 healthcheck step. Live components added: 0.

## Pushback / Surface / Dependencies
- Pushback: ~2 days to 90% is tight; if approval is slow, the box FAILs and blocks installs. A manual `--apply` is not offered (would be an install).
- Surface: held targets (PRICE_ARCHIVE ~1.8 GB would-free) need a reader-teaching block; not done here. Gap arm index went stale on main twice (guard failure), a generator-on-merge fix is worth a gap.
- Dependencies: operator approval of `disk_retention_install` by name; then the window runs it, reads `disk_retention_readback`, re-reads disk %.
- Pre-existing, unrelated: tests/test_w54_kalshi_settlement.py::test_settlement_value_parsing fails with and without these changes.
