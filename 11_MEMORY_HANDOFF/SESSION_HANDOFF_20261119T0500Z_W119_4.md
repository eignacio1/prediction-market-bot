<!-- session-meta
task_id: W119.4
tier: STANDARD
timestamp: 2026-11-19T05:00:00Z
commit: 1e7ff0b
one_line_summary: W119.4: verified evidence copy on the Mac (5827 files, 7.2 GB, sha256 match both sides); io_jsonl + ~45 readers; retention compresses PRICE_ARCHIVE/depth/frozen_evidence_check; merged (#529)
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING (evidence safety, B-103)
gap_measure: box disk %, bytes off-box verified
gap_delta: off-box verified 0 -> 7.2 GB / 5827 files (LAST_RUN.json 20261119T043238Z); box disk % NOT yet re-measured (dry-run result pending)
pattern_sweep: grepped src/ scripts/ 12_EXPLORATORY/ tests/ for prices_/depth_ globs + open(); ~45 readers converted; tests/test_w119_4_readers.py audits it. Left alone: different datasets (thin_markets/depth_stats, nba_depth_splits/score_depth, thin_market_depth_capture)
surface_delta: 0 box components; +1 Mac launchd job WRITTEN, NOT LOADED (awaits operator yes)
directive_conflicts: none found
-->
# W119.4 handoff
**Done.** (1) `scripts/ops/evidence_pull.sh`: pull-only rsync, sha256 on box and Mac, one re-copy, live append-only ledgers verified as an exact byte-prefix. Ran clean: 5827 files, 7.2 GB, 0 mismatch. (2) `io_jsonl.py` (`open_jsonl/iter_jsonl/jsonl_files/jsonl_paths/glob_files/resolve`); ~45 readers converted; static audit test. (3) disk_retention POLICY: `price_archive` (>14d), `price_archive_depth`, `frozen_evidence_check_pre` now verified targets. Full suite 5901 passed; CI green. PR #529 merged.
**Also touched (not mine):** regenerated `RUNTIME_MAP.md` (stale on main after 119.3's registry write; CI red without it).
**HELD, with reasons.** `pregame_shadow_ledgers`: 29 readers plus live appenders, not every reader provable. `mlb_inplay_logs`: same. Both stay uncompressed until a wave converts them.
**Readers 119.1-119.3 must adopt next wave (inputs kept plain until then):** `scripts/run_ride_board.py` (newest day only), `scripts/arm_orders_read.py`, `scripts/demo_fill_forward_report.py`. Also `archive_cron_install.py` (freshness check), `archive_market_prices.py` (writer).
**Caveat.** If the box compresses a day the Mac already holds plain, the Mac keeps both copies.
**Open.**
- Weekly job: `scripts/ops/evidence_pull_launchd.sh install|uninstall`. NOT loaded. Question for the operator: install the weekly copy (about 7.2 GB now, ~2 GB a month: archive averages ~71 MB/day plain)?
- `disk_retention_dryrun` requested (`BOX_TASKS/requests/20261119T0500Z_...`): bytes it would free are NOT yet read. The daily 14:17Z job applies after deploy. Disk % after: not read.
- CLAUDE.md Right-now block is RED in the scan (not touched by this block).
**Pushback:** compression alone will not reach ~50%; the dry-run number decides, and the Mac copy is what makes any later box deletion safe (nothing is deleted here).
**Surface:** no box component added. **Dependencies:** box deploy of #529 before the dry-run means anything; operator yes for the launchd job.
