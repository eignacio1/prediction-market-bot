# MLB Baseline — Pre NFL-Depth-Join Snapshot, 2026-09-09

**Purpose (T-537/GG-265, Deliverable 4):** capture MLB's production archive figures *before* NFL orderbook-depth sampling has run its full day, so tonight's post-hoc comparison has a real before-figure rather than a remembered one. Depth sampling was deliberately kept off NFL to protect T4M-PROJ's read budget (`deploy/cron.conf:405-412`); turning it on spends budget belonging to the only band that trades.

**Captured:** 2026-09-09T19:32Z UTC, read-only from `exp_output/PRICE_ARCHIVE/{prices,depth}_2026-09-09.jsonl` on the VPS. No writes were made to this directory this session.

## MLB price rows per series (today, so far)

| Series | Rows |
|---|---|
| KXMLBGAME | 1,480 |
| KXMLBSPREAD | 2,301 |
| KXMLBTOTAL | 3,624 |
| KXMLBTEAMTOTAL | 4,886 |
| KXMLBHIT | 9,232 |
| KXMLBF3 | 807 |
| KXMLBF5 | 882 |
| KXMLBF5SPREAD | 1,176 |
| KXMLBF5TOTAL | 2,051 |
| KXMLBF7 | 963 |
| **MLB total** | **27,402** |

## MLB depth rows per series (today, so far)

| Series | Rows |
|---|---|
| KXMLBGAME | 36 |
| KXMLBSPREAD | 18 |
| KXMLBTOTAL | 18 |
| KXMLBTEAMTOTAL | 36 |
| KXMLBHIT | 36 |
| KXMLBF3 | 18 |
| KXMLBF5 | 18 |
| KXMLBF5SPREAD | 18 |
| KXMLBF5TOTAL | 18 |
| **MLB total** | **216** |

(MLB's cron uses `--depth-sample-per-family 2`, vs. NFL's `1` — the per-series row counts reflect that, not a capture-rate difference.)

## Last MLB cron fire

Last MLB `run_ts` in both `prices_2026-09-09.jsonl` and `depth_2026-09-09.jsonl`: **2026-09-09T05:40:02Z**.

This is **not staleness** — the MLB price-archive cron (`deploy/cron.conf` / live crontab) only runs during two windows, `*/20 22-23 * * *` and `*/20 0-5 * * *` (UTC), i.e. the MLB evening-game window. At capture time (19:32Z) the current hour falls in the scheduled idle gap between the 05:xx window's last fire and the 22:xx window's next one — confirmed by inspecting the live crontab's MLB archive lines directly, not assumed. No anomaly.

## Errors / backoff / rate-limit lines today

```
grep -iE 'error|backoff|rate.?limit|exception|traceback|WARNING' logs/price_archive_cron.log | grep -c '2026-09-09'
0
```

Zero matches for today's date across all series (MLB and NFL) in `logs/price_archive_cron.log`.

## Context: NFL depth already joined production during this capture

Between this baseline capture starting and finishing, the real day-3 NFL cron line fired **8 times** for real (17:05Z through 19:25Z, every 20 minutes, `17-23 * * 3` window), each writing exactly 4 depth rows (one per NFL series family) — see Deliverable 3/verdict in the session's final report for detail. NFL depth rows in today's production `depth_2026-09-09.jsonl`: KXNFLGAME 8, KXNFLSPREAD 8, KXNFLTEAMTOTAL 8, KXNFLTOTAL 8 (32 total) — all attributable to real scheduled fires, not hand-runs (hand-run verification in this session wrote only to `exp_output/_PREFLIGHT_SCRATCH`, never to this file).
