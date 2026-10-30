# W95.2 — frozen evidence reproduction: PARTIAL (2026-10-30)

**Status: PARTIAL.** The harness and its box tasks are merged and the box archive was inventoried. The 13 cells were NOT re-run.
The re-run needs the settlement cache, and that is 2,334 of 5,907 events short. **No cell is classified. Reproduced: 0 of 13 (unchanged).**

## What is established
- Box archive (task `frozen_inventory_read`, 2026-10-30T14:16:41Z, box HEAD d9c4a08b): 91 files, 2026-08-01 to 2026-10-30.
- KXMLBHIT has 199,937 two-sided pre-start rows. The local re-run's n=0 for 89.2 cells 1 and 2 is therefore an **archive-coverage
  artifact of the partial local copy**, not a proven failure of the frozen cells. The full re-run is what decides it.
- Other series: KXMLBSPREAD 153,442; KXMLBTOTAL 256,821; KXMLBF5 65,793; KXMLBF5TOTAL 153,832.
- Hypothesis for the small n gaps (179 vs 186, 84 vs 85, 42 vs 44): files or settlements added after the reported run. Not tested.
- Settlement fetch: 509 events fetched in the last 200 s call. 2,334 remain, about 4 more calls of ~200 s each, each with a 5-10 min push/poll turn.
  The 780 s task died twice (SSH "Connection reset by peer"), so the short task is the one that works.

## Per-cell table
| Cell | Reported n | Re-run n | Class |
|---|---|---|---|
| all 13 (EXP-042 x11, EXP-043 x2) | see frozen files | not run | NOT YET TESTED |

## GG-1460 (Part B, code half)
Three `nfl_board_v2` scripts passed `safe_out("12_EXPLORATORY/…")`; `safe_out` already prefixes `12_EXPLORATORY/`. Fixed in PR #381, with a
test that scans every exploratory `.py`. **Their JSONs were not regenerated:** the inputs (the 2026-10-20 schedules parquet and the
price archive) exist only on the box, and the scripts write into the repo tree, so they are not read-only box tasks. Whether 93.4's
result changes is **unknown**. Nothing is claimed either way.

## EXP-042 / EXP-043 / EXP-045
Not assessed. I did not read EXP-043, EXP-045 or `score_exp045.py` this session. No finding yet exists to change any look.
Operator decisions: none. A frozen definition has not been found wrong.

## Next (one block)
1. Run `frozen_settle_fetch_short` until `remaining`=0, then `frozen_repro_window` and `frozen_repro_full`, then classify.
2. Add an allowlisted box task that runs the three scripts and prints the JSON (the writer-set test needs a deliberate change), then compare to 93.4.
