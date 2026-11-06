# W104.2 — How far to move off Kalshi's line (B-049) — DESCRIPTIVE

**Not a verdict.** No frozen test, pre-registration, sealed cell or sizing is touched. EXP-041 stays frozen.
Method: `quant/blend.py` (PR #437). `p = pm + w(pe − pm)` and its log-odds form; `w ∈ [0,1]` by log loss; 5-fold
**game-clustered** CV for the out-of-sample gain; 1000-draw whole-game bootstrap intervals; Holm and BH(0.10) across
the 8 cells with ≥15 games (one-sided p = share of bootstrap draws with w = 0). Known-answer tests: planted skill →
w≈1 and beats market; pure noise → w≈0 (8 tests, `tests/test_quant_blend.py`).
**When it applies:** settled rows with the model and the market price at the same snapshot, ≥ ~15 independent games, a
model not tuned on those games. **When it does not:** fewer games (v3 here), or a market that is itself over-confident —
then a skill-free model can earn a small w just by shrinking it toward the middle.
**Data epoch:** forecasts only, no fills or P&L — epoch note n/a.

## Data (box, read-only, 2026-11-06)
NBA engine arms v1/v2/v3 (`NBA_ENGINE_LIVE{,_V2,_V3}/rows.jsonl`, first row per ticker, price = `p_market` at the
engine's own snapshot), finals from the public ESPN scoreboard (53 completed games, 10-29 → 11-05). Cluster = game.

| engine | family | games | rows | market LL | w (linear) | w 95% CI | OOS LL gain/row [95% CI] | Holm p | w>0 beats market? |
|---|---|---|---|---|---|---|---|---|---|
| v1 | moneyline | 34 | 68 | 0.585 | 0.00 | 0–0.63 | 0.000 [0, 0] | 1.0 | no |
| v1 | spread | 33 | 1089 | 0.425 | 0.00 | 0–1.00 | −0.0057 [−0.011, −0.001] | 1.0 | no (worse) |
| v1 | game total | 32 | 928 | 0.495 | 0.05 | 0–1.00 | −0.0160 [−0.038, −0.002] | 1.0 | no (worse) |
| v1 | team total | 26 | 988 | 0.467 | 0.00 | 0–1.00 | −0.0005 [−0.001, 0.000] | 1.0 | no |
| v2 | moneyline | 37 | 74 | 0.601 | 0.00 | 0–0.27 | 0.000 [0, 0] | 1.0 | no |
| v2 | spread | 32 | 1056 | 0.453 | 0.00 | 0–1.00 | −0.0032 [−0.007, 0.000] | 1.0 | no |
| v2 | game total | 29 | 841 | 0.558 | 0.00 | 0–1.00 | −0.0044 [−0.013, 0.002] | 1.0 | no |
| v2 | team total | 28 | 1064 | 0.505 | 0.22 | 0–1.00 | −0.0041 [−0.014, 0.004] | 1.0 | no |
| v3 | moneyline | 11 | 22 | 0.570 | 0.00 | 0–1.00 | 0.000 | – | too few games |
| v3 | spread | 9 | 297 | 0.391 | 0.11 | 0–1.00 | −0.0129 [−0.041, 0.005] | – | too few games |
| v3 | game total | 9 | 261 | 0.400 | 0.00 | 0–0.92 | 0.000 | – | too few games |
| v3 | team total | 9 | 342 | 0.404 | 0.00 | 0–1.00 | −0.0055 [−0.016, 0.001] | – | too few games |

Log-odds form agrees (all w ≤ 0.22, none beats the market; `nba_blend_result.json`). Zero of 8 testable cells reject
at Holm or BH. Rows within a game are strongly dependent (many strikes per game) — intervals are by whole game.

## One line per sport (for the operator)
- **NBA:** on this first week of regular-season games, v1/v2/v3's view is worth about **0%** of a move off Kalshi's
  line on every family (the best fitted w is 0.22, on v2 team totals, with an interval spanning 0–1 and a negative
  out-of-sample gain). Taken at face value on spreads and game totals, following the model would have cost log loss.
  The intervals are very wide (~30 games, not hundreds): this says "no evidence of a useful w yet", not "w is 0".
- **NFL, NHL, MLB:** **not computed.** Their logged forecasts are the sealed pre-registered shadow cells
  (`PREGAME_SHADOW/`, `data/shadow/nhl/`); the rows carry no outcome and scoring them belongs to their own
  pre-registered looks, below judged n. Counts only: NFL ~66k rows, NHL ~42k, MLB ~8k logged, none settled in-file.
  MLB player-hits arms and NFL EXP-045 / NHL engine rows were not located on the box under a path I could read in
  time; left for a follow-up.

## Recommendation (not applied)
A future pre-registration that uses a market-anchored price should fix **w = 0 as the default arm** and treat any
fitted w as a *challenger* with a pre-declared prior shrinking to 0 and a minimum of ~100 independent games per
family (v2 team totals needs this before even the point estimate means anything). Don't hardcode 0.22 anywhere.

MEASURE MOVED: engine×family cells with a fitted out-of-sample w: **12 of 12 NBA** fitted, **8 of 8 with ≥15 games**
(of N=12 NBA + sealed NFL/NHL/MLB cells not attempted); cells where w>0 beats the market: **0**. Stage: **interpreted**
(a tested path from fact to a weight; not applied to any price). Pillar PROOF/DEPTH (D5).
