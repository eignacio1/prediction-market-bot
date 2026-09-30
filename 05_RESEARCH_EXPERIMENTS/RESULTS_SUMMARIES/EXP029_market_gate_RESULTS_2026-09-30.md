# EXP-029 (T-596) — RESULTS: frozen EXP-028 model vs Kalshi KXMLBHIT market

Pre-registration: `EXP029_market_gate_PREREGISTRATION_2026-09-30.md` (pushed before scoring, commit d5ec974).
Priced window scored ONCE (lock file `PRICED_WINDOW_SCORED.lock`). EXP-028 documents are unedited.

## Verdict
**HARMFUL: the market is better than the frozen model on this sample.** Test = 1,316 rows / 215 games
(2026-09-01..). Game-clustered paired ΔBrier (market − model; positive = model better) = **−0.00393**,
95% CI [−0.00629, −0.00152]; Δlog-loss −0.00845, CI [−0.01367, −0.00337]. Brier: market 0.2238, model 0.2277.
Model mean p 0.613, market 0.624, realised base rate 0.650 (both under-forecast; the market less so).
The frozen model cannot be shown to beat the market; on this sample it measurably loses to it.
Scope: only tickers the live T4 process evaluated (~20% of threshold-1 archive tickers), ab>=1 population.

## D0 — predecessors landed
origin/main 524c845 → a9c66a9; fb0587c is an ancestor. (Branch tip was 039b6bc; `git diff fb0587c tip -- src tests exp_output` empty.)

## D1 — extended matrix
Original 132,184×45 sha256 `b2a845a6fb35cfc8c0ec7589524313aeabd20e2140a353409e984f44979114a4`;
extended 152,987×45 sha256 `13249f5459ccf29beb4a28a3bb4ef1df4d4bfb32da3488181bbfcc0416239bcc`, through 2026-09-27
(regular season end; nothing exists for 09-28..30 in the source). Columns and dtypes identical.
Extension rows 2026-07-18..09-27 (20,804 rows / 970 games). Missingness is LOWER than baseline on every column
that differs (ba_l10 family 0.9% vs 4.3%; opp_sp_* 5.9% vs 15.3%): early-season warm-up NaNs are absent late
in the season. Nothing worsens, so the join is not invalidated.
Overlap rows re-fetched from the source differ slightly (≤96 rows/column; 6 of 7 `ab` changes are 2026-07-17 box
scores that were partial when the original was built; `park_factor_hits` drifts on 15,447 rows and is not a model
feature). Original file is untouched; scored features come from the extended file for 2026-08+ rows only.

## D2 — join (real tickers; `join_yield.json`)
Attempted 36,760 KXMLBHIT tickers (2026-08-01..09-30). Kept 2,006 rows / 404 games / 53 of 60 dates.
Dropped: threshold≠1 25,310; no authoritative ticker→player_id 8,400; snapshot >60 min stale 421;
T-577 forbidden manifest 406; no pre-first-pitch snapshot 189; no matrix row 19; doubleheader/dup 9.
Bridge = live pipeline (T4 cycle log ∪ T-421 outcome store), never inferred. Outcomes cross-check 291/291 vs T-421.

## D4 — corrected controls (new id EXP-029; EXP-028 not relabelled)
Train→validation 2024→2025, holdout/priced data untouched. (`controls_results.json`)
- Placebo drawn post-filter: backward ΔBrier +0.00494 vs forward +0.00484 (ratio 1.02) ⇒ the pre-game skill is
  time-symmetric persistent skill, the component a market already prices (same conclusion as EXP-028 P4).
- Permutation null: ΔBrier −0.000045, CI [−0.000133, +0.000044] contains 0 under BOTH the literal and the one-sided
  criterion; no leak. EXP-028's −0.00030 was a negative-side artefact of fitting noise; under the one-sided
  criterion its P5 would also not have declared a leak (statement about the criterion; EXP-028's record stands).

## D5 — required n
No positive edge was observed, so there is no observed delta to power. Clustered SE at n=215 games is 0.00123.
Games needed to detect a hypothetical model edge (one-sided α=.05; 80% / 95% power): Δ=+0.004: ~126 / ~221;
+0.002: ~505 / ~884; +0.001: ~2,021 / ~3,539. Capture rate 404 games/58 in-season days ≈ 7.0/day ⇒ the rest of
2026 adds ≈0 (regular season over 09-27), a full 2027 season ≈ 1,290 games at this capture rate: enough for
Δ≥+0.002 (80%), not for +0.001. Since the observed sign is negative and the persistent-skill placebo says the
signal is already priced, a pre-game cell on this feature set is not worth activating; a different information
source (lineup/pitcher news timing, weather) would be needed before an APR-0035 case exists.

## GAPS FOUND -- FOR REGISTRATION
1. Bridge coverage: ~80% of archived KXMLBHIT threshold-1 tickers have no authoritative ticker→player_id map
   (only T4-evaluated ones do). A settled ticker→player table would allow a full-market test.
2. The archive holds quotes only (no settlement field); outcomes are box-score re-derived.
3. `generate_mlb_features.py` re-fetch changes prior rows (partial box scores on last day; `park_factor_hits`
   drift), so the matrix is not append-only reproducible.
4. Step-4 concerns: one 0-player T1 MLB run in the last six; `SemanticFloorViolation` count 1.
5. Governance hook: Compass Health line >3000 chars; hook open-GG count 106 vs 113 grep-anchored.
6. Q1–Q7 not answered formally this session (time).
