# W59.2 — Calibration correctness before the first look

Status: IN PROGRESS (Part A done; B, C, D pending). Counts only anywhere in this document; no cell has reached a look.

## Part A — Projection from the real schedule

**Defect.** `project_first_look` extrapolated a linear trailing-14-day settle rate. NFL plays one slate a week and the
season ends at week 18, so a daily rate misdates the look by up to a slate and cannot say "never reaches it".

**Fix.** The projection now walks the sport's remaining published schedule (one entry per scheduled regular-season game)
multiplied by the cell's measured coverage (settled games / scheduled games since the cell began logging), adds a
1-day settle lag, and reports `not reachable on the published schedule` instead of a date when the expected total falls short.
Schedule sources: NFL `data/schedules/nfl_2026.json` (snapshot of the nflverse 2026 schedule, 272 games, committed);
NHL `data/raw/nhl/schedule/2026.json` (VPS cache; 1,312 regular-season games); MLB: 2027 schedule not published, so no date is given.
Tests: `tests/test_calibration_engine.py` (weekly slate, slate-day landing + lag, unreachable, no schedule, tiny-sample coverage, reached).

**Corrected first-look dates (as of 2026-10-07, data copied read-only from the VPS):**

| Sport | Cells | Settled games | Old (linear) | Corrected |
|---|---|---|---|---|
| NFL | 12 (4 markets x T1-T3) | 15 each | trailing-rate date | **2026-11-02**, coverage 100% of 15 scheduled since logging began (208 games left; needs 45). Fragile: one week of coverage data |
| MLB | 12 | 0 judged (2-4 postseason, never scored) | n/a | none: judged games begin 2027-03-01 and the 2027 schedule is unpublished |
| NHL | 9 | 16-30 | trailing-rate date | **none: judged n 2,500 is not reachable.** Expected additional games 668 (T1) to 1,128 (T2) of 1,295 left; even at 100% coverage the season has 1,312 games |
