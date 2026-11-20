# Pot of gold re-score, W122.2 (2026-11-20)

Last reviewed: 2026-11-20. Governed by `PREREGISTRATION_2026-11-05.md` + `POT_OF_GOLD_ADDENDUM_2026-11-20.md` (written before any outcome was read).
Descriptive re-score, not a look. Looks stay 2026-12-10 and 2027-01-14. Method: `measure.py` unchanged, run by `rescore_w122.py`.
Data: 51,624 joined first-snapshot rows (736,317 settled tickers; 3,032 unsettled), games MLB 5,325 · NFL 591 · NBA 466 · NHL 411.

## The 17 pre-registered cells (premise correction: they are 15 MLB + 2 NFL, no NBA/NHL)
**0 earned · 17 still IN_SAMPLE · 0 closed (hypothesis closed, parked for R&D).** Counted on forward rows only (first snapshot at or after 2026-11-05).
- 15 MLB cells: 0 forward rows (MLB is idle until 2027). Nothing to score.
- KXNFLSPREAD/D1/1-5c: 31 contracts, 13 games. KXNFLTOTAL/D1/95-99c: 25 contracts, 23 games. Judged n is 150 contracts, 30 games, 5 rarer outcomes: no score is read.
- Holm across all 36 candidate cells measured: 0 rejected.

## Measured status by sport (book = all, counts of cells; descriptive)
| Sport | FAILED (test, parked) | IN_SAMPLE | UNTESTED (thin) |
|---|---|---|---|
| MLB | 114 | 24 | 68 |
| NFL | 48 | 6 | 170 |
| NBA | 21 | 1 | 90 |
| NHL | 19 | 1 | 24 |
Props are mostly UNTESTED: too few settled snapshots. They are measured, never promoted.

## Held-out leads, non-MLB (for a NEW pre-registration; none is a verdict)
All are IN_SAMPLE, below judged n or with a lower bound at or under zero. Gap = settled rate minus price.
NFL TOTAL D1 95-99c take-favourite yes (n 104, net +2.1c, lo +0.04c, held n 13) · NFL SPREAD D1 1-5c fade (n 109, net +2.0c, lo -0.05c) · NFL TOTAL D1 5-10c fade (n 221, +1.3c, lo -2.9c) · NFL TEAMTOTAL D1 10-15c fade (n 182, +1.7c, lo -2.8c).
Pattern worth a pre-registration: NFL fade-the-longshot and take-the-favourite in D1, by game. Held-out n is 13-21 per cell, so the next look needs the forward weeks.

## Routing outcome
In these leaves the pot-of-gold arm routes to no bet today (`NO_BET`, reason "cell status IN_SAMPLE is not orderable"), logged beside v1 so each leaf accrues forward rows.
That is a routing result, not a closure of the arm. Candidate table: `src/.../decision_trees/longshot_cells_w122.toml` (234 cells, 0 orderable).
Raw settlements stay out of git (`out/settle_w122/`, 69 MB).
