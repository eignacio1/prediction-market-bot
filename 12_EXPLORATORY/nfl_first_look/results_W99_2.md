# Wave 99.2 — PROOF lane results (B-034 + B-002 + B-035)

Read-only except the registry change merged in #406. No frozen file, `ride_cells.toml`, model, runner, order, gate or ledger was touched.

**Plain English:** (A) the two RULED_OUT NFL game-total cells are now in the registry with reason and date; the other 10 NFL cells keep accruing to the second look. (B) The re-run supports a lower edge than the frozen threshold in all 11 ride cells; one cell (10) should be retired before its look, and two more (9, 11) are close behind. (C) Partial: the box output cap cut the per-game rows to 18 of 72 games, so the decomposition below is a first read, not the full 60-game one. A compact box task is the one remaining step.

## Part A — EXP-037 verdicts carried out (B-034)

| Cells | EXP-037 verdict | Done |
|---|---|---|
| NFL GAME_TOTAL T1, T2 | RULED_OUT at first look (delta Brier vs market −0.0161 [−0.0294, −0.0027]; −0.0157 [−0.0299, −0.0011]) | `RULED_OUT`, reason, measured_date 2026-11-02, via `promote_cell_status` (#406); seat file + NFL_SEAT.md regenerated; registry test added. Arms keep logging (nothing gates the shadow cron). |
| 10 other NFL cells (GAME_TOTAL T3; SPREAD T1-3; TEAM_TOTAL T1-3; MONEYLINE T1-3 incl. QB) | KEEP ACCRUING | No status change. Next look: second look at n=150 or week 18, whichever first; regular season ends 2027-01-10 (EXP-041 s.4). Judged n now 72 (T3 game-total 63; NFLQB moneyline 47). |

Box read-back (2026-11-04): P1 12/49, P2 12, P3 2026-11-13 (NFLQB_NFL_MONEYLINE_T1, modal KEEP ACCRUING ~91%). `PROOF_CALENDAR.md` regenerated from the box emit.

**Two generator defects found (registered, not fixed here):** (1) the calendar still prints "KEEP ACCRUING ~91% (first look)" and a `> 2029-01-01` upper bound for cells already past the first look — it has no second-look state; (2) B1 (cells logging) under-counts RULED_OUT arms that still log.

## Part B — frozen evidence outlook (B-002 / B-035)

Re-run net edge (exact fee) vs the frozen net the look must beat. Cells in the order of `results_W98_2.md`. J = judged games the re-run supports at power 0.80, alpha 0.05 (full-edge / half-edge), from the re-run's own standard error; "—" = lower bound ≤ 0 under the re-run so no finite J at that edge.

| # | Cell | frozen net / lo | re-run net (k007) [lo] | exact lo | J full / half | Look reads (most likely) |
|---|---|---|---|---|---|---|
| 1 | KXMLBHIT 20-25c all yes | .027 / .0065 | .0124 [−.0053] | +.0009 | 1693 / 6771 | NOT MET; edge ~half of frozen |
| 2 | KXMLBHIT 20-25c tight yes | .044 / .017 | .0218 [.0011] | +.0072 | 708 / 2834 | NOT MET |
| 3 | KXMLBF5TOTAL 90-95c all yes | .038 / .022 | .0381 [.0215] | .0230 | 39 / 156 | MET if sample holds |
| 4 | KXMLBF5TOTAL 90-95c wide yes | .033 / .011 | .0428 [.0387] | .0400 | 1 / 6 | MET |
| 5 | KXMLBF5TOTAL T2-6h tight yes | .043 / .017 | .0454 [.0219] | .0238 | 38 / 150 | MET |
| 6 | KXNFLTOTAL D1 5-10c all no | .038 / .0065 | .0370 [.0014] | .0014 | 133 / 531 | Marginal; lo barely >0 |
| 7 | KXMLBSPREAD 20-25c tight no | .052 / .0026 | .0385 [−.0061] | −.0003 | 445 / 1780 | NOT MET |
| 8 | KXMLBTEAMTOTAL 15-20c tight no | .095 / .0085 | .0702 [−.0065] | −.0017 | 96 / 384 | NOT MET |
| 9 | KXMLBF5 10-15c all no | .078 / .0087 | .0428 [−.0224] | −.0184 | 280 / 1121 | NOT MET |
| 10 | KXMLBTOTAL 85-90c wide yes | .089 / .047 | .0383 [−.0301] | −.0265 | 370 / 1479 | NOT MET |
| 11 | KXMLBF7 40-45c wide yes | .065 / .0006 | .0509 [−.0119] | −.0033 | 257 / 1029 | NOT MET |
| H1 | KXMLBTOTAL net5c+ (EXP-043) | .2166 | holds under both fee treatments | — | — | Supported; n small (30 reported) |
| H2 | KXMLBTOTAL net2-5c (EXP-043) | .087 | holds under k007, not under the exact fee | — | — | NOT MET under exact fee |

All 11 ride cells reproduced as DIFFERS with a smaller net than reported (sign held everywhere). No forward data has accrued for any cell since the freeze: MLB paused after the World Series (~2026-11-01) until ~2027-03-25, so **no look on an MLB cell can read before spring 2027**; cell 6 (NFL) can read this season. H1/H2 were classified from the remaining shards; numbers are in the `frozen_resume_*` box results.

**Cells whose frozen threshold sits above what the re-run supports:** 1, 2, 7, 8, 9, 10, 11 (re-run net well below frozen with lower bound ≤ ~0).

### Operator line (recommendation, no frozen file edited)

> **Retire EXP-042 cell 10 (KXMLBTOTAL T0-2h 85-90c wide yes) before its look:** frozen net .089 / lo .047, re-run .0383 / lo −.0301 (exact fee −.0265); the frozen threshold is above anything the re-run supports and it needs ~370 judged games, against 19 frozen. Cells 9 and 11 are next (lo −.018 / −.003); cells 1, 2, 7, 8 are weaker but not clearly dead. Say yes/no on cell 10; I will not edit `ride_cells.toml` or any prereg.

## Part C — NFL game-total model vs market (descriptive only, nothing re-scored) — PARTIAL

Source: box task `nfl_total_rows_read` (20261104T0325Z_w992_rows_rerun). **Coverage limit:** the result hit the 60KB output cap and holds **395 ladder rows from 18 games (T1 11, T2 7, T3 4)**, early weeks only (weeks 4 and 8), not the 60 judged games. Weather columns are blank for week 8 (schedule feed gap). Treat every number as a first read.

Sign convention: dBrier = model Brier − market Brier on the market's mid, per ladder strike; **positive = model worse than market**. (EXP-037's reported delta uses the opposite sign, which is why the verdict is negative there.) Magnitudes are per-rung, not per-game, so they are not comparable to −0.016.

| Cut | n rows | dBrier | model p − mid |
|---|---|---|---|
| T1 | 197 | +0.031 | +0.009 |
| T2 | 124 | +0.019 | −0.010 |
| T3 | 74 | +0.027 | +0.077 |
| Strike ≤38 | 105 | −0.004 | +0.015 |
| Strike 39-44 | 75 | +0.035 | +0.055 |
| Strike 45-50 | 83 | +0.063 | +0.024 |
| Strike >50 | 131 | +0.022 | −0.011 |
| Outdoors (13 games) | 280 | +0.019 | +0.042 |
| Dome (3) | 76 | +0.031 | −0.028 |
| Closed roof (2) | 38 | +0.071 | −0.090 |
| Week 4 / Week 8 | 196 / 198 | +0.031 / +0.022 | +0.009 / +0.022 |

What the 18 games say:
- **Direction:** the model is worse than the market in every band; its error lives in the middle of the ladder (strikes 39-50), where most of the probability mass sits, and is nil in the low tail.
- **Roofs:** the largest misses are indoor/closed games (KC@LV dome +0.098, ARI@DAL closed +0.099, MIA@MIN dome +0.075; DAL@HOU closed +0.043), where the model prices lower totals than the market (closed-roof p − mid −0.09). The model has no roof input.
- **Weather:** among outdoor games with a reading, wind was ≤9 mph in all of them, so no wind effect can be read; hot games (≥70F: GB@TB, DEN@SF) show dBrier +0.029 vs +0.008 for 45-70F — two games, not a finding.
- **Biggest single misses:** GB@TB (model 44 vs market 39 median total; result well under), MIA@MIN, TEN@BAL (model median 48.7 vs market 42.9). Both are cases where the model's 11 features (team EPA/points for-against, rest) disagree with the market's median by 4-6 points and the market was right.
- **What this says for the NFL engine (a note for 99.1 or later, not a change):** the shadow model has no roof, weather, QB or pace input, and the error concentrates exactly where those matter (indoor games priced low; 4-6 point median disagreements). That fits the DEPTH gap, not a bad-luck sample. The cheapest descriptive check on the full 60 is a compact box task that emits per-game aggregates (median implied total model vs market, dBrier, roof, week) instead of every rung.

## Registered follow-ups (no work done in this session)
1. `nfl_total_rows_read` output exceeds the 60KB box cap; needs a per-game aggregate mode, then Part C reruns on all 60+ games.
2. `proof_calendar.py` has no second-look state (prints first-look modal and a 2029 bound after the first look).
3. B1 under-counts RULED_OUT arms that still log.
