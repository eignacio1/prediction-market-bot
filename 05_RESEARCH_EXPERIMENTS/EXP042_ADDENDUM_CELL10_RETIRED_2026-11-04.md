# EXP-042 addendum — cell 10 retired before its look (2026-11-04, W100.2)

Separate file. `EXP042_RIDE_CELLS_PREREGISTRATION_2026-10-28.md` is unedited. This addendum supersedes ONLY cell 10's forward look. Cells 1-9 and 11 are untouched (cells 9 and 11 are NOT retired). No decision rule, seed, look date or unit of any other cell changes.

## The operator's decision (quoted, ACTIVE_QUEUE.md "Needs your decision", 2026-11-03 19:16 PT: "Yes")

> **Retire EXP-042 cell 10 (KXMLBTOTAL T0-2h 85-90c wide yes) before its look:** frozen net .089 / lo .047, re-run .0383 / lo −.0301 (exact fee −.0265); the frozen threshold is above anything the re-run supports and it needs ~370 judged games, against 19 frozen. Cells 9 and 11 are next (lo −.018 / −.003); cells 1, 2, 7, 8 are weaker but not clearly dead. Say yes/no on cell 10; I will not edit `ride_cells.toml` or any prereg.

## What is retired

| Item | Value |
|---|---|
| Cell | #10: KXMLBTOTAL, T0-2h, bucket 85-90c, book wide, side YES |
| Frozen (W89.2, as in §1 / §3 table) | n 52 / 52 games, net +.089, 95% lo +.047; judged n (half effect) 75 games, full-effect 19 |
| Re-run (W98.2 / W99.2 frozen-evidence check; `12_EXPLORATORY/frozen_evidence_check/results_W98_2.md`, `12_EXPLORATORY/nfl_first_look/results_W99_2.md`) | n 72 games, net +.0383, 95% [−.0301, …]; exact Kalshi fee −.0265. Sign held; magnitude and lower bound did not |
| Judged n implied by the re-run | ~370 games (1,479 at half effect), against 19 frozen |
| Forward data | none: MLB is paused until ~2027-03-25, so the cell's first look (~2027-04-15 full-effect) never ran |

## Reason

The frozen pass rule needs a net lower bound > 0. The re-run's lower bound is below zero under both fee treatments, and the effect the cell was selected for (best of many, a winner's-curse upper bound) does not reproduce. Spending a 2027 look on it would test a threshold nothing supports.

## Status

**RETIRED before its look. Never scored forward; this is not a FAILED verdict and not a PASS.** It counts as closed (no look owed), not as evidence against the method. `ride_cells.toml` cell 10 `status = "RETIRED"` (reason and date recorded there); the router returns NONE for it (`ride:status_RETIRED`, since RETIRED is not in RIDEABLE). Open cells after this addendum: 10 of 11.

Modal outcome note: the preregistration (§4) already predicted cells 8-11 most likely UNTESTED/regressing; this retirement is consistent with that and does not alter the BH family size for the remaining cells' forward looks (stated here so it is not decided afterward: BH q = 0.10 is applied across the cells still open at each look).
