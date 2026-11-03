# NFL first look (EXP-037) — released verdicts, read 2026-11-03 (W98.2 Part A)

**Source:** box task `first_look_verdicts_read`, result `04_EXECUTION/BOX_TASKS/results/20261103T034324Z_first_look_verdicts_read.md` (engine file `engine_20261102T135056Z.json`, generated 2026-11-02T13:49:01Z). Read-only; nothing was scored, re-run or changed here.

## In plain English
All 12 NFL cells (moneyline, spread, game total and team total, each at T1/T2/T3) reached the first look at 60 settled games. **No cell is a candidate, and none is a win.** Two cells, both in game total (T1 and T2), are **ruled out**: the model did worse than the market's own price, and the gap is big enough that chance alone doesn't explain it (about 0.016 Brier worse; the interval stays below zero). The other 10 cells **keep accruing**: the model is a little worse than the market in every one of them (−0.006 to −0.014), but the intervals include zero, so 60 games can't separate "slightly worse" from "the same". Against the naive baseline (climatology, the long-run base rate), the model is better in all 12 cells on the point estimate (+0.002 to +0.017), but in none does the interval exclude zero, so that is not proven either. In short: the NFL models are a bit behind the market and a bit ahead of a naive baseline, and at this sample size neither difference is proven. That is the outcome the pre-registration called most likely (about 91% per cell for keep accruing).

## Per-cell table (delta = Brier(X) − Brier(model); positive = model better; 95% game-cluster bootstrap CI; n = 60 games each)
| cell | vs market [CI] | vs climatology [CI] | verdict |
|---|---|---|---|
| GAME_TOTAL_T1 | −0.0161 [−0.0294, −0.0027] | +0.0024 [−0.0079, +0.0128] | RULED_OUT |
| GAME_TOTAL_T2 | −0.0157 [−0.0299, −0.0011] | +0.0024 [−0.0073, +0.0131] | RULED_OUT |
| GAME_TOTAL_T3 | −0.0140 [−0.0279, +0.0007] | +0.0023 [−0.0074, +0.0128] | KEEP ACCRUING |
| MONEYLINE_T1 | −0.0061 [−0.0343, +0.0254] | +0.0174 [−0.0150, +0.0476] | KEEP ACCRUING |
| MONEYLINE_T2 | −0.0070 [−0.0360, +0.0250] | +0.0174 [−0.0166, +0.0487] | KEEP ACCRUING |
| MONEYLINE_T3 | −0.0075 [−0.0364, +0.0239] | +0.0174 [−0.0166, +0.0487] | KEEP ACCRUING |
| SPREAD_T1 | −0.0076 [−0.0217, +0.0078] | +0.0049 [−0.0112, +0.0200] | KEEP ACCRUING |
| SPREAD_T2 | −0.0084 [−0.0232, +0.0078] | +0.0049 [−0.0113, +0.0202] | KEEP ACCRUING |
| SPREAD_T3 | −0.0080 [−0.0231, +0.0082] | +0.0061 [−0.0105, +0.0212] | KEEP ACCRUING |
| TEAM_TOTAL_T1 | −0.0071 [−0.0148, +0.0009] | +0.0023 [−0.0052, +0.0092] | KEEP ACCRUING |
| TEAM_TOTAL_T2 | −0.0076 [−0.0151, +0.0006] | +0.0023 [−0.0054, +0.0096] | KEEP ACCRUING |
| TEAM_TOTAL_T3 | −0.0070 [−0.0148, +0.0015] | +0.0030 [−0.0052, +0.0107] | KEEP ACCRUING |

Tally: RULED_OUT 2, KEEP ACCRUING 10, CANDIDATE 0. (The engine labels keep-accruing as `SHADOW`.)

## Against the pre-registered expectations (`NFL_FIRST_LOOK_EXPECTATIONS.md`)
- **Expected:** keep accruing almost everywhere (~91% per cell). **Got:** 10 of 12.
- **CANDIDATE anywhere:** none (a surprise only if it had happened).
- **RULED_OUT in T1:** yes, GAME_TOTAL_T1. The pre-registration lists this as a surprise (about 9% per cell at the 2025 gap of −0.008; the observed −0.016 is twice that gap). Per EXP-037 the verdict is what the rule says; no interpretation is added here. Note T1/T2/T3 of a family share the same games, so GAME_TOTAL_T1 and T2 are one finding counted twice, not two independent ones. No pre-2026 game-total market price exists, so the 2025 gap for this family was never measured.
- **Monotone T1→T2→T3 ordering:** game total moves −0.0161 → −0.0157 → −0.0140 and moneyline −0.0061 → −0.0070 → −0.0075, in opposite directions; spread and team total are not monotone. The differences are far smaller than the intervals.
- **Model worse than climatology** on moneyline or spread: no (both positive). Moneyline's CI excluding zero (about 35% expected) did not happen.

## Next look
Second look at 150 settled games per cell (EXP-037). The engine returns no projected date for any cell (`date: null`, "first look reached"), so I am not inventing one. RULED_OUT cells are final under the pre-registration; the 10 keep-accruing cells continue to log.
