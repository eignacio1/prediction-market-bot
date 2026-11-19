# Handoff W120.3 - held readers read .gz; Mac copy compressed; disk measured (PLUMBING)

<!-- session-meta
task_id: W120.3
tier: MICRO
timestamp: 2026-11-19T05:30:00Z
commit: e39bf49 (PR #531 merged on green; handoff pushed direct to main)
one_line_summary: W120.3: three held readers read .gz, Mac evidence copy compacted 7.21->5.70 GiB, box disk still 74% until the 14:17Z retention apply (~63% expected); weekly Mac job awaits operator yes.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: box disk %; held bytes; Mac folder GB
gap_delta: held 1.87 GB -> 0 (readers); Mac 7.21 -> 5.70 GiB; box disk 74% -> 74% (apply pending 14:17Z)
pattern_sweep: plain open() on *.jsonl swept in src/ scripts/ tests/ deploy/ .claude/; only writers remain allowed
surface_delta: 0
directive_conflicts: none
-->


Common rules quoted: "# Wave 120 common rules". Branch w120-3-box, PR #531 merged on green. Box HEAD f1380fb contains it.

- vision_pillar: PLUMBING (infra, B-103)
- gap_measure: box disk %; held bytes; Mac evidence folder GB; weekly job loaded
- gap_delta: held 1.87 GB -> 0 from the three readers (dry run 05:22Z: 1139 files / ~2.68 GB compressible; 13 files / ~367 MB
  still held, none from these readers). Mac folder 7.21 -> 5.70 GiB (189 files, sha-verified, 0 failures). Box disk 74% -> 74%
  (05:24Z): retention applies only in the daily 14:17Z job. Weekly job loaded: NO (awaiting operator yes).
- pattern_sweep: src/ scripts/ tests/ deploy/ .claude/ grepped for plain open() on *.jsonl; the three scripts left the
  tests/test_w119_4_readers.py ALLOW set. Still allowed: archive_cron_install.py, archive_market_prices.py (writers).
- surface_delta: 0 live components. +scripts/ops/evidence_compact.py (Mac side, runs inside evidence_pull.sh; EVIDENCE_NO_COMPACT=1 skips).
- directive_conflicts: none.

## Done
A. arm_orders_read.load_rows, demo_fill_forward_report.load_events/load_markouts, run_ride_board.recent_mids read via io_jsonl;
   tests/test_w120_3_readers_gz.py covers plain and .gz for each (recent_mids incl. big-tail case).
B. evidence_compact.py: plain duplicate removed only if its sha matches the decompressed .gz (or .gz covers a prefix); old plain
   compressed; a plain file with a differing .gz is kept and flagged. tests/test_w120_3_evidence_compact.py.
   Growth compressed: price archive ~18x (39 MB -> 2.2 MB per day), so ~2-4 MB/day, about 100-150 MB/month all paths.

## Part C - box 74%, top consumers (NOT acted on)
1. exp_output/PRICE_ARCHIVE 2.6 GB - compress (already in retention, ~2.68 GB saved at 14:17Z).
2. 12_EXPLORATORY/frozen_evidence_check 1.3 GB - compress or move off box.
3. logs/ride_board/decisions.jsonl 1.1 GB - cut at the writer (rotate/dedupe), then compress.
4. logs/audit_mlb_t4*.jsonl + audit_mlb.jsonl ~1.1 GB - MLB idle to 2027; rotate and compress (writer holds files open).
5. kalshi_history_rebuilt/KXNFLGAME.jsonl 342 MB - reader seeks by byte offset; needs a reader change before compress.
Also: venv 664 MB, t4_mlb_cycle_log.jsonl 245 MB.

## Pushback / Surface / Dependencies
- Pushback: the block said the three readers hold the 1.87 GB; #529 had already unheld PRICE_ARCHIVE, so the gain is #529 plus these readers.
- Surface: no new cron. Dependencies: daily 14:17Z retention apply; operator yes to install the weekly Mac job.
- Next window: run disk_read after 14:17Z and record disk % after (expect ~63%).
