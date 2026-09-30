# EXP-029 (T-596) — Frozen EXP-028 model vs Kalshi KXMLBHIT market: PRE-REGISTRATION

Written and pushed BEFORE any model prediction on the priced window is scored. Only row/game counts and
join yield were computed (no outcome-vs-prediction comparison). No outcome-based number has been examined.

## Relationship to EXP-028
EXP-028's pre-registration, results and verdict are NOT edited or relabelled. EXP-028 recorded P5 as failed
(literal two-sided criterion) and void-flagged its results; B2 (market) was untestable (0 overlap rows).
EXP-029 is a NEW experiment that (a) tests the frozen model against the market on a priced window, and
(b) re-specifies the controls (D4). Whether EXP-028's numbers leave void-flag is reported in EXP-029's
results as a statement about the corrected control, not as an edit to EXP-028.

## Frozen model
Exactly as at fb0587c: `PregameHitsModel(C=10.0)`, 16 FEATURES, fit on 2024-01-01..2025-12-31 (train+validation)
from the original matrix (sha256 b2a845a6…9114a4). No refit, retune, re-selected features or C. Features for
priced rows come from the extended matrix (sha256 13249f54…6bcc), population filter `ab>=1 & ba_l10 notna`.
Fixed files: joined.jsonl sha256 4429556c…3a3e29; build_join.py sha256 038d1dc7…bb91.

## Population / join (D2, real tickers only; yield in exp_output/EXP-029/join_yield.json)
KXMLBHIT threshold==1, 2026-08-01..09-30. Bridge = live-pipeline ticker→player_id (T4 cycle log ∪ T-421
outcome store); no heuristic matching. 36,760 tickers attempted; 2,006 rows / 404 games kept.
Selection caveat (binding on interpretation): kept tickers are those the live T4 process evaluated
(~20% of threshold-1 archive tickers); the result speaks to that sample, not all KXMLBHIT markets.
Outcome = matrix `h>=1` (resolution_source `boxscore_rederived`); 291/291 overlap rows agree with T-421.
`p_incumbent` = mid of (yes_bid, yes_ask) of the last archive snapshot strictly before scheduled first pitch
(ticker HHMM, US Eastern = UTC-4), required within 60 min, two-sided quote with 0<bid<=ask<1.

## D3 primary test
Run T-583 `run_gate` (imported, unmodified), candidate = frozen model, incumbent = market `p_incumbent`.
Cutoff = 2026-09-01: gate "train" segment 189 games (ignored by the frozen candidate; exists only to satisfy
the harness), TEST = 1,316 rows / 215 games. Metric: game-clustered paired ΔBrier (market − model; positive =
model better), N_BOOT=5000, seed 17, plus Δlog-loss. Rule (harness): DEFENSIBLE_IMPROVEMENT if Brier CI_low>0
and Δlog-loss mean>0; HARMFUL if Brier CI_high<0; otherwise the verdict is reported as
**NO DETECTABLE DIFFERENCE** (CI spans 0). No other threshold. The extended window is scored ONCE.
Conditioning caveat: model is scored on `ab>=1` rows (its frozen population); market prices near first pitch
already reflect lineups, so no DNP adjustment is applied.

## D4 corrected controls (run on train→validation 2024→2025 only; holdout/priced window untouched)
1. Placebo `y_backward` drawn from the SAME filtered (`ab>=1 & ba_l10 notna`) population: shift(11) within
   player over the filtered sequence (EXP-028 shifted before the filter, mixing populations). Interpretation
   rule unchanged from EXP-028 §8.1 (≥50% of forward gain ⇒ persistent skill, not a forward-specific edge).
2. Within-date label permutation null, seed 2028, model retrained on permuted train labels, scored vs B0
   (climatology) on permuted validation labels. **One-sided criterion:** the machinery is declared leaking
   (results void) only if the ΔBrier CI lies entirely ABOVE 0 (model beats climatology on noise). A CI below 0
   is the expected cost of fitting noise (16 params + C=10) and is not a leak. Additionally |mean ΔBrier| must
   be < 0.001. This choice is made AFTER seeing EXP-028's Δ=−0.00030 (CI excluding 0 from below); that is
   disclosed, and the reason is the sign argument above, not the outcome.

## D5
Required n for a market edge from the observed ΔBrier mean and game-clustered variance: n_games =
(1.645+0.842)² · σ²_game / Δ² (one-sided α=0.05, 80% power; and the 95%-power variant), converted to calendar
time at the observed priced-game rate (~7 usable games/day in-season, 404 games/53 dates), 2026 remainder and 2027.
