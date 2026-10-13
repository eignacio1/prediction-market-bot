# EXPLORATORY — W71.3 NBA games availability challenger: RESULT = **NO** (D1 stays)

Plan: `README.md` (committed before any fit). Not a verdict about any cell (CHARTER rule 6). Fit once; no tuning after seeing results.

## Integrity
- Fold A `ctrl_refit` 2025 moneyline Brier = **0.2110515179**, identical to the frozen artifact (`models/nba_pregame_v1_heldout.json` held_out_2025) and Platt (a,b) identical to 12 digits. Check passed.
- **Disclosed invalid first run:** my first run put season 2015 into training (the frozen script uses it only as feature history); it failed the integrity check (0.21086 vs 0.21105). Cause: implementation bug, not a result-driven change. Fixed the train filter to 2016+ and re-ran; run 1 kept as `results_run1_INVALID_2015_in_train.json`. Its verdicts were also NO, so nothing hinged on the fix.
- No-look-ahead tests: 4/4 pass (`test_lookahead.py`).

## Coverage
Personnel rows exist only 2023–2026 (1,230 games/season, 1,187–1,190 per season with snapshots for both teams, ≈96.5%). Seasons ≤2022 carry zeros + inj_missing=1, so coefficients are identified by 2023+ data only (1 season in fold A, 2 in fold B).

## ΔBrier vs frozen (challenger − control; negative = better), 98.33% game-cluster bootstrap CI (m=3, B=20000, seed 71303)
| Family | Fold A (test 2025) | Fold B (test 2026) | Pooled (n=2462) | Beats frozen? |
|---|---|---|---|---|
| Moneyline | −0.00083 [−0.00376, +0.00203] | −0.00247 [−0.00565, +0.00064] | −0.00165 [−0.00377, +0.00056] | No (CI includes 0) |
| Spread (5 strikes) | +0.00005 [−0.00280, +0.00288] | −0.00367 [−0.00669, −0.00068] | −0.00181 [−0.00389, +0.00024] | No (CI includes 0; fold A not favourable) |
| Total (5 strikes) | +0.00025 [−0.00121, +0.00175] | −0.00060 [−0.00197, +0.00077] | −0.00017 [−0.00116, +0.00084] | No |

Fold B spread alone excludes zero, but it is one test season, not the pooled CI the rule requires, and fold A is flat/unfavourable. Reported, not acted on (rule fixed in README §8).
Market comparison: none (no NBA Kalshi price history); not computed.

## Reading
Matches the written modal outcome (NO/negligible). Direction is mildly favourable (moneyline and spread improve ≈0.002 Brier), consistent with availability carrying a little signal that two identifying seasons cannot resolve. A re-test is worth it only after another season of personnel data accrues (2026-27 in-season, point-in-time) — a new dated pre-registration, not a re-read of these numbers.

## Measure
D1 (NBA games condition on team only → team + personnel): **unchanged** (team-only). D3: **no change** (no challenger earned a pre-registration). Source: this file, `results.json`.
