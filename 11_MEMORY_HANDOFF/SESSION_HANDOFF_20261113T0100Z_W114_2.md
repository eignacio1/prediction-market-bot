<!-- session-meta
task_id: B-090
tier: STANDARD
timestamp: 2026-11-13T00:50:00Z
commit: cbf7d64
one_line_summary: W114.2: D6 measured on the box (0/117) and first E1-E3 per arm via two new read-only box tasks (#498).
gg_touched: GG-1933, GG-1934, GG-1935
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH, EXECUTION
gap_measure: D6, E1, E2, E3
gap_delta: D6 uncountable -> 0/117 wired (d6_read @ 2026-11-13T00:45:55Z); E1 fills RIDE 21/162, FADE 1/37, MOMENTUM 1/7 (arm_orders_read @ 00:45:26Z)
pattern_sweep: n/a (no defect fixed); Python 3.9 "Z" fromisoformat defect found in demo_fill_forward_report, registered GG-1934
surface_delta: +2 read-only allowlisted box tasks (arm_orders_read, d6_read), no cron or service
-->

# SESSION HANDOFF — W114.2 (B-090) — D6 counted on the box

Status: DONE · Ticket B-090 · branch session/20261113T002213Z-w114-2-d6-box-reads · PR #498 merged e8e06a1 on green CI (test job, run 43336788400)
Common rules read first: `# Wave 114 common rules`.

## Result
Two read-only box tasks (`arm_orders_read`, `d6_read`) are allowlisted and ran on the box (box HEAD 70f9c8b9 contains e8e06a1).
Results: 04_EXECUTION/BOX_TASKS/results/20261113T0044Z_arm_orders_read.md (ran 00:45:26Z), ..._d6_read.md (ran 00:45:55Z).

## MEASURE MOVED
- **D6 (DEPTH), measured on the box: 0 of 117 wired.** Source: d6_read, 2026-11-13T00:45:55Z. Cells by layers present: 0:72, 1:12, 2:5, 3:4, 4:15, 5:5, 6:4, 7:0.
  Per sport (registered / wired / per_layer L1..L7): MLB 42/0 [3,12,0,3,0,0,0]; NBA 25/0 [9,12,9,7,7,0,4]; NFL 29/0 [9,12,0,9,9,3,2]; NHL 21/0 [9,9,0,8,7,0,0].
  Missing exactly one layer: NBA_SPREAD T2 and T3 (layer 6 sizing); NFL_GAME_TOTAL T3 and NFL_SPREAD T3 (layer 3 filters).
- **E1-E3 per arm (EXECUTION), first values.** Source: box logs/arm_orders/orders.jsonl, 6,578 rows, last 2026-11-13T00:44:44Z; all rows post-GG-1771 epoch, all sides (no pre-epoch rows). Fills from read-only Kalshi demo GETs, 0 lookups failed.
  | Arm | Orders | Fills (E1) | Fill rate | Settled | E2 | E3 |
  | RIDE | 162 | 21 | 12.96% | 0 | null | null |
  | FADE | 37 | 1 | 2.70% | 0 | null | null |
  | MOMENTUM | 7 | 1 | 14.29% | 0 | null | null |
  E2/E3 are null: no settled fills yet. Orders by sport: RIDE NBA 162 / NFL 0, FADE NBA 31 / NFL 6, MOMENTUM NBA 6 / NFL 1. NHL: 0 orders.
- Skips: daily_breaker 690 (RIDE 487, FADE 93, MOMENTUM 110); size_zero 36; no_bet 3,542; unrouted 593 (NBA/NFL); NHL UNROUTED 1,415.

## Stage reached per factor
Unchanged by this block (a measurement block). The measurement shows layer 3 supplies filters on the box for NBA only.

## NHL layer 3 = 0 on the box — Monday install proposal (NOT installed)
Cause: `exp_output/NHL_EVENTS` does not exist on the box (`nhl_store_dir_exists=false`, no games_2025/2026.parquet). It is git-ignored and built only by `src/prediction_market_bot/c1_signal_ingestion/nhl_event_store.py`; no RUNTIME_REGISTRY entry builds it (GG-1898).
The job that builds it, two steps, both public no-login GETs, no orders, no .env:
1. `PYTHONPATH=src venv/bin/python -m prediction_market_bot.c1_signal_ingestion.nhl_event_store fetch --from-season 2025 --rps 2 --threads 2` (resumable raw cache under exp_output/NHL_EVENTS/raw)
2. `... nhl_event_store compile` (writes `<table>_<season>.parquet`, including games_2025/2026 that `filter_supply.nhl_store_dir()` reads)
Proposed shape: a one-time backfill, then a daily cron (e.g. `30 9 * * *`, after the 09:00 nhl_backfill) running fetch then compile, flock-guarded, logging to logs/nhl_event_store.log, with a RUNTIME_REGISTRY entry (Hard Rule 14) and a staleness alarm. Open sizing question: disk and first-run time for 2025-26 only; not measured. Even with the store, NHL rows are UNROUTED (1,415), so layer 3 would count but arm orders would not appear until a route exists (GG-1935).
Needs operator approval by exact task name when the `*_install` task is written; nothing installed here.

## Other findings
- NFL layer 3 is 0 on the box although wired locally: `default_nfl_providers()` returns None when its snapshots are absent (GG-1933).
- Python 3.9 "Z" timestamp defect in `demo_fill_forward_report.arm_orders_report` (GG-1934), not fixed here.
- Daily breaker dominates skips (GG-1935).

## Required fields
- pattern_sweep: n/a (no defect fixed); the 3.9 timestamp pattern was swept for in scripts/ only as far as demo_fill_forward_report and registered as GG-1934.
- surface_delta: +2 read-only allowlisted box tasks (arm_orders_read, d6_read); no cron, no service, no writes outside the results file.
- vision_pillar: DEPTH D6 (measured 0/117 on the box); EXECUTION E1-E3 first per-arm values.
- gap_measure: GG open count; gap_delta: +3 (GG-1933, GG-1934, GG-1935).
- directive_conflicts: none known.
- Operator decisions: none. NHL_EVENTS box job proposed for Monday.
