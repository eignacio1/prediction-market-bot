# W96.2 results: frozen ride evidence, full-archive reproduction (B-002)

Status: PARTIAL. The settlement cache is complete. No cell was re-run to a result. The nfl_board_v2 JSONs were not regenerated.
Date: 2026-10-30. Box: root@157.230.91.33, box HEAD 553d95c3 at the retry. Harness: `repro.py` (#383, #386).

## What was done
- Settlement fetch finished: 5,907 events, 2,334 missing at the start, 0 remaining (4 bridge rounds: 593 / 656 / 579 / 506).
- `frozen_repro_window` (`--until 2026-10-28`): first run dropped the ssh link (exit 255, no output). After the heartbeat (#386) the retry stayed alive for the whole run and was killed at the 900 s task timeout: **exit 124, no cell output** (`results/20261030T1640Z_w96_2_repro_window2.md`).
- `frozen_repro_full` was not run: it scans more data than the window run that already hit the limit.
- `nfl_board_v2_regen_read`: **exit 1**. `heldout_keynumbers.py` could not open `exp_output/NFL_EVENTS/raw/schedules/schedules_20261020T001136Z.parquet`. `exp_output/NFL_EVENTS` does not exist on the box, and a search of the box finds no `schedules_2026*.parquet`. It is not in this checkout either. The previous claim that these inputs "live only on the box" (GG-1471) is wrong.

## Per-cell table (13 cells)

| # | Cell | W89.2 / W91.2 reported | Re-run n, net, lo | Class |
|---|---|---|---|---|
| 1 | KXMLBHIT T0-2h 20-25c all YES | 1892/368, +.027, +.0065 | none | NOT RUN |
| 2 | KXMLBHIT T0-2h 20-25c tight YES | 1151/339, +.044, +.017 | none | NOT RUN |
| 3 | KXMLBF5TOTAL T6-24h 90-95c all YES | 143/138, +.038, +.022 | none | NOT RUN |
| 4 | KXMLBF5TOTAL T6-24h 90-95c wide YES | 111/107, +.033, +.011 | none | NOT RUN |
| 5 | KXMLBF5TOTAL T2-6h 90-95c tight YES | 85/83, +.043, +.017 | none | NOT RUN |
| 6 | KXNFLTOTAL D1 5-10c all NO | 154/92, +.038, +.0065 | none | NOT RUN |
| 7 | KXMLBSPREAD T>24h 20-25c tight NO | 186/147, +.052, +.0026 | none | NOT RUN |
| 8 | KXMLBTEAMTOTAL T6-24h 15-20c tight NO | 49/40, +.095, +.0085 | none | NOT RUN |
| 9 | KXMLBF5 T2-6h 10-15c all NO | 44/44, +.078, +.0087 | none | NOT RUN |
| 10 | KXMLBTOTAL T0-2h 85-90c wide YES | 52/52, +.089, +.047 | none | NOT RUN |
| 11 | KXMLBF7 T0-2h 40-45c wide YES | 121/88, +.065, +.0006 | none | NOT RUN |
| 12 | EXP-043 KXMLBTOTAL T0-2h tight net2-5c | 117 games, +.0870, [.0336, .1424] | none | NOT RUN |
| 13 | EXP-043 KXMLBTOTAL T0-2h tight net5c+ | 30 games, +.2166, [.0951, .3411] | none | NOT RUN |

"NOT RUN" is a status of this block, not a reproduction class. No cell is REPRODUCED, DIFFERS or NOT REPRODUCED. The earlier partial-archive differences (GG-1470: SPREAD 179 vs 186, F5TOTAL 84 vs 85, KXMLBF5 42 vs 44, 91.2 202/324 vs 117) remain unexplained; the hypothesis that they come from files or settlements added after the original run is untested.

## Why the run does not fit
`repro.py run` makes several full passes of per-line `json.loads` over 1.4 GB (180 files) on a 1-core, ~1 GB box: `inventory`, `run_89`, `run_91`, plus the bootstrap. The box task runner caps every task at 900 s and returns output only at exit. The heartbeat fixed the link drop, not the length. Fix: a resumable, cell-at-a-time run (one series per task, results cached under the fence), or a prefilter pass that writes the pre-start two-sided rows of the target series to a derived file once. Both are code PRs plus a box task; they do not fit in the 90-minute ceiling after the failures above.

## Part B: what each frozen test's look will read
Nothing below rests on a reproduced number. All of it is from the frozen documents.

- **EXP-042 (11 cells).** No finding from this block changes what a look reads: the forward test scores archive rows after the freeze, once per cell at its look, with the frozen entry rule and fee `fee_k007`. The in-sample numbers (table above) only set the judged n and the prediction that most cells regress to zero. The open risk is that the in-sample numbers are not shown to reproduce (GG-1470), so the judged n's were sized from figures that could shift by a few rows. A 2-4% row difference does not move a judged-n by an order of magnitude; it could move a cell with a lower bound near zero (cell 11, lo +.0006; cell 7, lo +.0026), which is already expected to fail at its look.
- **EXP-043 (H-A, H-B).** Same position. H-A's two bins come from the 91.2 held-out half; the partial-archive re-run gave 202/324 vs 117, so those two cells are the ones most likely to differ. The look rule (exact fee, with a k007 re-score beside it) is unaffected.
- **EXP-045 (NFL engine).** Its in-sample replay (86 settled games, every interval including 0) rests on 93.4's board_v2 numbers, which I could not regenerate because the pinned schedules parquet is not on the box or in this checkout. The look reads NOT DISTINGUISHABLE at about 85% by its own pre-registration, so the missing regeneration does not change what look 1 will read. It does leave the pin (sha256 c57e424c) unverifiable until the file is found.

No frozen artifact, `ride_cells.toml` status or pre-registration was edited.

## Operator line
None needed. Retire-or-keep applies only to a cell shown not to reproduce, and none was.

## Gaps
GG-1470 and GG-1471 stay OPEN (their text is unchanged; GG-1521 corrects GG-1471's claim about where the inputs live). New: GG-1520 (run exceeds the 900 s task limit), GG-1521 (EXP-045's pinned schedules parquet is on neither the box nor this checkout), GG-1522 (task output is lost when the link drops, no box-side output file).
