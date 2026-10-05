# W53.2 — Shadow ledger + crontab audit (read-only)

**Measured:** 2026-10-05 04:13 UTC (VPS clock) · **Method:** read-only `ssh` row counts over the ledger files; `crontab -l` diffed against `deploy/`. No NHL or NFL score, outcome value, Brier or E_net was read or computed — only row counts, field validity and timestamps. Nothing on the VPS was written, restarted or edited.
**Valid row** = numeric `p_yes` in [0,1], numeric `mid` in (0,1), `market_ticker` present. Rows are one per (market, evaluation).

## D1 — NHL (`data/shadow/nhl/`)

| Market type | Band | Rows | Valid | Runs | First row (UTC) | Last row (UTC) | Settled rows |
|---|---|---|---|---|---|---|---|
| NHL_MONEYLINE | T1 | 14 | 14 | 2 | 10-03 14:00 | 10-04 14:00 | 8 |
| NHL_MONEYLINE | T2 | 220 | 220 | 26 | 10-03 15:00 | 10-04 20:30 | 204 |
| NHL_MONEYLINE | T3 | 164 | 164 | 47 | 10-02 23:30 | 10-05 00:40 | 154 |
| NHL_PUCK_LINE | T1 | 28 | 28 | 2 | 10-03 14:00 | 10-04 14:00 | 16 |
| NHL_PUCK_LINE | T2 | 440 | 440 | 26 | 10-03 15:00 | 10-04 20:30 | 408 |
| NHL_PUCK_LINE | T3 | 328 | 328 | 47 | 10-02 23:30 | 10-05 00:40 | 308 |
| NHL_GAME_TOTAL | T1 | 63 | 63 | 2 | 10-03 14:00 | 10-04 14:00 | 36 |
| NHL_GAME_TOTAL | T2 | 990 | 990 | 26 | 10-03 15:00 | 10-04 20:30 | 918 |
| NHL_GAME_TOTAL | T3 | 736 | 736 | 47 | 10-02 23:30 | 10-05 00:40 | 691 |

All nine files exist, 0 malformed lines, 0 invalid rows. **No cell has zero rows: #160's flip of the nine NHL cells is supported.** Settled counts are the `settled/` file line counts (rows joined to an outcome), not outcome values.

## D2 — EXP-037 (`exp_output/PREGAME_SHADOW/`)

**NFL — 12 ledgers, all valid (0 malformed, 0 invalid rows):**

| Market type | Band | Rows | Valid | Runs | First row (UTC) | Last row (UTC) | Settled |
|---|---|---|---|---|---|---|---|
| NFL_MONEYLINE | T1 | 48 | 48 | 5 | 10-04 00:05 | 10-05 00:05 | 0 |
| NFL_MONEYLINE | T2 | 112 | 112 | 15 | 10-04 06:10 | 10-04 20:10 | 0 |
| NFL_MONEYLINE | T3 | 132 | 132 | 21 | 10-04 12:30 | 10-05 00:00 | 0 |
| NFL_SPREAD | T1 | 609 | 609 | 5 | 10-04 00:05 | 10-05 00:05 | 0 |
| NFL_SPREAD | T2 | 1424 | 1424 | 15 | 10-04 06:10 | 10-04 20:10 | 0 |
| NFL_SPREAD | T3 | 1677 | 1677 | 21 | 10-04 12:30 | 10-05 00:00 | 0 |
| NFL_GAME_TOTAL | T1 | 456 | 456 | 5 | 10-04 00:05 | 10-05 00:05 | 0 |
| NFL_GAME_TOTAL | T2 | 1064 | 1064 | 15 | 10-04 06:10 | 10-04 20:10 | 0 |
| NFL_GAME_TOTAL | T3 | 1254 | 1254 | 21 | 10-04 12:30 | 10-05 00:00 | 0 |
| NFL_TEAM_TOTAL | T1 | 635 | 635 | 5 | 10-04 00:05 | 10-05 00:05 | 0 |
| NFL_TEAM_TOTAL | T2 | 1498 | 1498 | 15 | 10-04 06:10 | 10-04 20:10 | 0 |
| NFL_TEAM_TOTAL | T3 | 1766 | 1766 | 21 | 10-04 12:30 | 10-05 00:00 | 0 |

No `settled/` directory exists yet. That is expected: the only settle firing so far (10-04 09:30) preceded the games, wrote 0 for every cell, and the next is 10-05 09:30.

**MLB postseason — 0 ledgers, 0 rows.** No `MLB_*` file exists in `exp_output/PREGAME_SHADOW/`, and no cron line runs it (see D3). `scripts/run_mlb_pregame_shadow.py` (12 cells: MONEYLINE/RUN_LINE/GAME_TOTAL/TEAM_TOTAL × T1–T3) is present on the VPS but has never been scheduled.

**Cron firings that should have fired by 04:13 UTC (`logs/pregame_shadow_*.log`):**

| Job | Schedule | Fired? | Evidence |
|---|---|---|---|
| T1 `--refresh --bands T1` | `5 */6` | Yes, 5 runs (10-04 00:05 → 10-05 00:05) | last run wrote T1: 2/25/19/28 rows (ML/SPREAD/TOTAL/TEAM_TOTAL) |
| T2 `--bands T2` | `10 *` | Yes, 15 runs wrote rows; latest 10-05 04:10 ran, wrote `{}` | all candidates `outside_band_windows` (no game 4–8h out) |
| T3 `--bands T3` | `*/10` | Yes, 21 runs wrote rows; latest 04:10 ran, wrote `{}` | same reason |
| Settle `30 9` | daily | Yes, 1 run (10-04 09:30) | `settled_new` = 0 for all T1/T2 cells (games not final yet) |
| MLB postseason | — | **No cron exists** | no line, no log, no ledger |

## D3 — Crontab vs `deploy/`

* NHL block (7 non-comment lines, `crontab -l` lines 494–500) vs `deploy/cron.nhl_shadow`: **identical**.
* EXP-037 block (`# BEGIN EXP-037` … `# END EXP-037`, 4 jobs) vs `deploy/cron_exp037_pregame_shadow.conf`: **identical**.
* `deploy/cron.nhl_shadow.draft` is fully commented and is superseded by the installed file; it is not expected to match.
* The crontab header supplies `PROJ`, `PYTHON`, `PYTHONPATH`, which the NHL lines use.
* **Difference from what the queue records:** `04_EXECUTION/ACTIVE_QUEUE.md` says "NFL + MLB postseason shadow — Armed … the 33 pre-game cells now log unattended". 33 = 12 NFL + 12 MLB + 9 NHL. The installed block contains only the NFL runner (`run_pregame_shadow.py` defaults to `models/nfl_pregame_v1.json`) and its NFL-only settle. **The 12 MLB cells are not armed.** Registered as GG-453.
* Not audited: the separate pre-existing `# T1 MLB postseason flag` item in the queue (edits an existing line; out of scope for this block).

## D4 — Cross-check vs registry on `origin/w52/landing` (not changed)

| Finding | Cells |
|---|---|
| Log rows, SHADOW on landing | NHL × 9 (all three types × T1–T3); NFL × 4 (T1 only) |
| **Log rows, NOT SHADOW on landing** | **NFL × 8: NFL_{MONEYLINE,SPREAD,GAME_TOTAL,TEAM_TOTAL} × {T2, T3}** — each has valid rows (see D2). `_EXP037_NFL_SHADOW_CELLS` lists T1 only. |
| SHADOW on landing, no rows | none among game-market cells |
| MLB game-market cells, no rows, not SHADOW | MLB_{MONEYLINE,RUN_LINE,GAME_TOTAL,TEAM_TOTAL} × 3 bands — consistent with each other; the problem is upstream (no cron) |

The registry comment states a cell flips only after at least one valid ledger row exists. The 8 NFL T2/T3 cells now satisfy that, so the landing block's Live Terminal will under-show them (T2/T3 pre-game rows exist but render as not-SHADOW). This is an omission to fix at landing, not a defect in the ledgers.

## Defects and decisions

1. **GG-453 (registered):** the 12 MLB postseason shadow cells have no cron, no ledger, no rows, while the queue records them as armed.
2. **Operator decision:** authorize adding a `run_mlb_pregame_shadow.py` block to the VPS crontab (T1/T2/T3, same shape as the NFL block; the 2026-10-02 authorization wording covers "shadow-evaluation T1/T2/T3 jobs … for the EXP-037 shadow ledgers", but I did not read that as an install order for this block). MLB postseason games are live now, so each day without it loses pre-game rows that cannot be recovered.
3. **For the landing block:** add the 8 NFL T2/T3 cells to `_EXP037_NFL_SHADOW_CELLS`, or state why not.
4. No ledger invalidity, no NHL zero-row cell, no crontab drift.
