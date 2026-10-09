# NFL Translation Map: which MLB/NBA modelling mechanisms carry into NFL pre-game

**EXPLORATORY. Part A of W63.2 (T-766). Read-only audit of code and ADRs; nothing run live.**
Purpose: DEPTH D1 (NFL pre-game model toward the granularity bar). Pillar: DEPTH.

## 0. Plain finding first

The "months of MLB mechanisms" are mostly NOT in the MLB *game-level* model. They live in the
MLB **player-hit stack** (`c2_feature_store/mlb_features.py`, T1 LR+Platt) and in NBA T1 props.
The MLB game model (`pregame_shadow/mlb_model.py`, `models/mlb_game_pregame_v1.json`) is
structurally the **same object as the frozen NFL model**: ridge (lambda=100) means, probit-Platt on
the margin, sigma/rho from 2024 residuals, train 2015-2023 / cal 2024 / held-out 2025. Its only
personnel input is the starting pitcher's shrunk runs-allowed feature. So NFL is not "missing what
MLB has"; the gap is that NFL has **zero personnel/context inputs** (QB, injuries, weather, travel),
which MLB game-level has exactly one of (SP).

Also: the empirical-Bayes shrinkage (ADR-0047) is in the feature CSV but **not in the trained T1
model's 18 features** (T-597), so "carry shrinkage" has no proven MLB benefit in a deployed model.
Temperature scaling (ADR-0027) was ruled out for MLB (GG-105); `calibration.py` defaults to identity
for any new sport by design. Both are therefore not candidates.

## 1. Mechanism inventory (verified in code path unless marked)

| # | Mechanism | Where (code) | ADR / ref | In MLB deployed path? |
|---|---|---|---|---|
| 1 | Starting-pitcher shrunk runs-allowed, `(sum RA over last 8 starts + 4*team_RA)/(n+4)` | `c1_signal_ingestion/mlb_game_pregame_features.py` `_sp_ra` (SP_STARTS=8, SP_PRIOR_STARTS=4) | MLB game model spec | Yes (game model) |
| 2 | Recency-decayed rolling team form (WINDOW=20, DECAY=0.95, MIN_PERIODS=10) | same file `_team_form` | same | Yes (game model) |
| 3 | League run-rate context feature (`league_rpg`) | same file `row` | same | Yes (game model) |
| 4 | Bivariate Gaussian (margin,total), ridge lambda=100, probit-Platt, sigma/rho from cal season | `pregame_shadow/*_model.py`, `scripts/train_*_pregame.py` | ADR-0070 (distributional deviation from ADR-0004) | Yes; NFL already has it |
| 5 | Empirical-Bayes shrinkage of rolling BA (`ba_l10`, K=40; A1 candidate K=400) | `c2_feature_store/mlb_features.py` | ADR-0047 | In CSV, NOT in trained T1 model (T-597) |
| 6 | Opposing-SP overlay (era/k9/bb9 L5, is_known) | `mlb_features.py` | T1 player stack | Player stack only |
| 7 | Park factor table (hits, 2022-2024 averages) | `mlb_features.py` | T1 player stack | Player stack only |
| 8 | Opponent runs-allowed L10 | `mlb_features.py` | T1 player stack | Player stack only |
| 9 | Opponent-adjusted Poisson lambda | NBA T1 props | ADR-0015 | NBA only, not MLB |
| 10 | Temperature scaling | `c3_forecasting/calibration.py` | ADR-0027; ruled out for MLB by GG-105 | Identity default |
| 11 | PRF qualitative amplifier (context-conditional interactions) | `c2_feature_store/qualitative_amplifier.py` | EXP-009 | NBA basketball construct; MLB T1 model has 0 qualitative features |
| 12 | Isotonic recalibration contingency | `scripts/run_a3_train_isotonic.py` | GG-105 A3 (offline, not deployed) | No |

Not re-verified in depth: ADR-0068 horizon doctrine, ADR-0070 text beyond header.

## 2. NFL analogue, PIT data availability (2019-2025), cost

nflverse sources: `games.csv` (rest, roof, surface, temp, wind, QB ids/names, coaches, referee,
gametime), `injuries_YYYY.csv` (per-row `date_modified`, `report_status`, `practice_status`),
`stats_team_week` (EPA etc.).

| Mechanism | NFL analogue | PIT source 2019-2025? | Look-ahead risk | Work |
|---|---|---|---|---|
| 1 SP shrunk RA | **Starting-QB shrunk performance** (QB rolling EPA/dropback shrunk toward team prior, same `(sum+k*prior)/(n+k)` form) plus a QB-out/backup flag | QB id per game is in `games.csv` (actual starter). Per-QB rolling EPA needs play/player stats (nflverse `player_stats`), same ecosystem | Small: actual starter can differ from the starter known at kickoff-minus-N-hours (late scratch). Injury report status Fri/Sat mitigates | Medium |
| 5 EB shrinkage | Shrink early-season team EPA/points rates toward prior (week 1-4 are noisy; WINDOW=8, MIN_PERIODS=3 currently) | Yes (derived from existing team stats) | None | Low |
| 2 Recency decay | Already present (WINDOW=8, DECAY=0.85). Window/decay search is the only open item | Yes | None | Low, but 2025 already consumed once |
| 3 League context | League-average points/total by season as a feature | Yes | None | Very low |
| 7 Park factor | **Stadium/roof/surface factor** (dome vs outdoor, turf) | Roof/surface static, PIT-legal. W61.3 tested dome: no help | None | Low (already tested) |
| 6/8 Opponent SP/RA | Opponent-adjusted defense (partly in EPA features already) | Yes | None | Low, likely redundant |
| (none in MLB game) | **Injury-report features by position group** (QB, OL, pass rush, secondary) | `injuries_YYYY.csv` with `date_modified`: PIT-legal if only rows modified before as_of are used | Low if timestamp filter enforced | High (position mapping, snap-weighting) |
| (none) | **Rest/travel** (rest already used; travel distance, time zones) | Rest yes. Travel needs stadium coordinate table (not built); static, PIT-legal once built | None | Medium |
| (none) | **Weather** (temp, wind) | Values in history are *observed*, not forecast | **High**: not PIT. Exclude, or flag as upper bound only | n/a |

## 3. Ranking by expected information per unit of work

1. **Starting-QB shrunk performance + QB-change flag** (analogue of the one personnel mechanism MLB
   game-level actually has; QB is the single largest NFL personnel variance; data available; small
   look-ahead risk).
2. **Early-season EB shrinkage of team rates** (cheap, zero look-ahead, targets the weeks where
   MIN_PERIODS=3 is thin).
3. **Injury-report features, QB-only first** (QB availability overlaps with #1; broader position
   groups are expensive). Timestamp filter is mandatory.
4. League-context and travel/rest-extension (low information expected; rest already captured).
5. Window/decay search (cheap, but the forking-paths and 2025-reuse constraints bind hardest).

## 4. What is NOT translatable, and why

- **Temperature scaling (ADR-0027) and Poisson opponent-adjusted lambda (ADR-0015):** NBA player-prop
  mechanisms; temperature scaling was disproven for MLB (GG-105); NFL calibration is already
  probit-Platt on a Gaussian margin, a different family.
- **PRF qualitative amplifier (EXP-009):** basketball player-role construct with no NFL
  counterpart and no demonstrated MLB benefit.
- **Park factor as a hit-rate table:** NFL has no per-park run environment of comparable size;
  roof/surface is the analogue and was already tested.
- **Weather as a feature:** no PIT forecast archive in nflverse; observed values leak.
- **Batter-level shrinkage and SP K/BB overlays:** the NFL model is team-level; the nearest
  analogue is the QB, covered above.
- **Anything claiming a proven MLB lift:** none of the player-stack mechanisms is demonstrated to lift
  the *deployed* MLB model (T-597), so "carry what worked" overstates the evidence.

## 5. Evaluation-data constraints for Part B

- 2025 held-out was already used by the frozen model and the W61.3 recalibration; 2019-2023 by the
  W61.3 rolling origin. 2024 is the frozen model's calibration season. Neither can be the sole test.
- 2025 Kalshi mids (exp_output/KALSHI_HISTORY, 2025-season tickers only) may be used for the market
  comparison. No 2026 rows, ever.
- Spec, feature list, model class and seasons are frozen in the Part B study README before fitting.
