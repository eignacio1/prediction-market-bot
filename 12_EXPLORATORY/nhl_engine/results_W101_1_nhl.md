# W101.1 Part C — NHL totals spread-shrink challenger, held-out 2023–2025

Spec (committed before any challenger row, `d82d106`): `NHL_TOTALS_CHALLENGER_PREREGISTRATION_2026-11-05.md`. Raw: `results/w101_1_heldout.json`. n = 3,936 regular-season games (1,312 per season), game-clustered bootstrap (2,000), seed 0.

## Baseline reproduced
Regulation total-goals bias, merged model: −0.080 pooled (per season −0.149 / −0.095 / +0.006); model_pit −0.059 pooled (the −0.059 in the brief). Held-out slope (actual on predicted total): 0.38 / 0.35 / 0.61 for model_pit — the 0.4–0.5 miscalibration reproduces.

## Challenger (T' = m + s·(T−m), s from training-only 2-fold cross-fit, s = 0.60 / 0.50 / 0.53)
Pooled bias: −0.020 (vs pit −0.059). Slope: 0.60 / 0.62 / 1.06 (vs pit 0.38 / 0.35 / 0.61).

| Family | Brier pit | Brier chal | chal − pit [95% CI] |
|---|---|---|---|
| ML | 0.23939 | 0.23920 | −0.00019 [−0.00041, +0.00002] |
| SPREAD_HOME | 0.19699 | 0.19668 | −0.00031 [−0.00049, −0.00013] |
| TOTAL | 0.22138 | 0.22061 | −0.00077 [−0.00140, −0.00013] |
| TEAMTOTAL_HOME | 0.23264 | 0.23216 | −0.00048 [−0.00099, +0.00004] |
| TEAMTOTAL_AWAY | 0.23495 | 0.23422 | −0.00073 [−0.00124, −0.00025] |

## Verdict by the pre-registered rule: **NO**
TOTAL and TEAMTOTAL_AWAY improve with CI excluding zero; TEAMTOTAL_HOME's CI includes zero (upper bound +0.00004). The rule requires all three. No family is worse. A NO is a result; the direction is consistent and the effect small (≈0.0005–0.0008 Brier). Not edge, no cell, no order; nothing compared to market prices.
