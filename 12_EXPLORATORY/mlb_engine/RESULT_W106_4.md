# W106.4 result — the MLB engine's second step: a lineup-aware game model (B-018)

**Status: PARTIAL-DONE.** Parts A, B and C done. Descriptive only; no pre-registration (per block). Measure: **D4 MLB**, factor classes point-in-time **0 → 4 built** (starter, bullpen, lineup vs handedness, park), scored held out against naive **and against Kalshi's closing line**.

> "The market is the real bar (operator 21:09 PT)." — the market wins. Plainly below.

## The short answer
- **Does lineup awareness move the model?** A little, in the right direction, against a constant. 2024→2025 held out (n = 2,430 games): the all-features model beats "always the base rate" on moneyline by **+0.0016 Brier** [95% +0.0000, +0.0032] — the interval's lower edge sits on zero; on totals by **+0.0024** [+0.0008, +0.0041]; on the run line by **+0.0028** [+0.0017, +0.0039]. The W105.3 baseline was +0.0004 on moneyline with an interval spanning 0. So: totals and run line are real small gains; moneyline is borderline.
- **Does it beat the market?** **No.** 2026 games the Kalshi archive priced (Aug–Sep, last mid at least 10 minutes before first pitch, overround removed):

| Market | n | Brier: model / **market** / naive | Model minus market (positive = model better), 95% CI | Blend w (linear), 95% CI |
|---|---|---|---|---|
| Moneyline (all features) | 753 | 0.2447 / **0.2372** / 0.2484 | **−0.0075** [−0.0121, −0.0029] | **0.00** [0.00, 0.30] |
| Moneyline (W105.3 base) | 753 | 0.2462 / **0.2372** / 0.2484 | −0.0090 [−0.0142, −0.0038] | 0.00 [0.00, 0.22] |
| Total, rung nearest 50% (all) | 735 | 0.2525 / **0.2493** / 0.2549 | −0.0031 [−0.0075, +0.0011] | 0.09 [0.00, 0.58] |
| Total (base) | 735 | 0.2538 / **0.2493** / 0.2549 | −0.0045 [−0.0098, +0.0006] | 0.07 [0.00, 0.50] |

  Log loss, moneyline: model 0.6825, market 0.6668, naive 0.6900. The market itself beats naive by +0.0112 Brier [0.0052, 0.0173], so the price carries real information the model does not have. Lineup awareness closed about 17% of the base-to-market Brier gap on moneyline (−0.0090 → −0.0075); it is nowhere near closing it.
- **Blend.** `quant/blend.py`, game-date clusters (58 dates — thin, the interval caveat applies). Moneyline w = 0: the best use of this model next to the market is none. Total w ≈ 0.07–0.09 but the cross-validated out-of-sample gain is **negative** (−0.0013 to −0.0019 log loss per row, interval excludes 0 from below), and a small positive w is what shrinkage alone would give. **w ≈ 0 is a result.**

## What was built (all point-in-time, tests prove no row sees a later game)
| Factor | Stage (ADR-0075) | What it is |
|---|---|---|
| Starter | aggregated + interpreted | Platoon-split wOBA allowed to date, shrunk; share of the game he is expected to cover (learned from his prior starts) |
| Bullpen | aggregated + interpreted | Quality allowed to date + pitches thrown in the previous 1 and 3 days |
| Lineup vs handedness | aggregated + interpreted | The nine actually played, each batter's wOBA against the opposing starter's hand, shrunk to league |
| Park | aggregated + interpreted | Shrunk log run factor from prior games at the venue |
| Any of the four **applied** | **applied** (a tested path from fact to price) | Run expectancy per team → negative-binomial joint → moneyline, total (any rung) and run line from one distribution |

None of them is applied *against the market* as a bettable rule — the market comparison says it would lose money. Granularity-index parts (split / rank vs history / matchup cross / market map / application): split ✔, matchup cross ✔ (platoon), application ✔, **rank vs history at the same point in a season ✘** and **market map ✘** (not built).

Ablations (2025, moneyline Brier gain vs naive): platoon +0.0006, bullpen +0.0014, park +0.0003, all +0.0016. Bullpen and starter share carry most of the moneyline gain; park carries totals (+0.0024 alone).

## Caveats (read these before quoting a number)
1. **As-played lineups.** The nine are taken from who batted. A late scratch or a lineup change forced by the game itself leaks a small amount of information a pre-game forecast would not have. A real pre-game lineup feed does not exist in the store yet. This flatters the model; the market still wins.
2. **Doubleheader game 2 does not see game 1's relievers** (conservative); 50 doubleheader games were dropped from the market join as ambiguous.
3. **Multiple comparisons:** 5 arms × 3 markets in 2025. One lower bound (moneyline, +0.0000) is borderline; do not read it as a finding.
4. Home and away runs are modelled as independent; a correlation would fatten the tie/blowout shapes and could move the run line and totals.
5. **Market side:** Aug–Sep only (58 game dates), mid of bid/ask, not a fill. Wide-spread contracts were kept; a tight-spread cut (half-spread ≤ 0.03) kept all 753 games, so the result is not a liquidity artefact. KXMLBSPREAD was not scored (contract semantics unverified). No weather, umpire, injury or posted-lineup inputs.
6. 2026 coverage: Savant regular season complete (2,429 games, 195 day-files, none capped).

## Next three steps
1. **Pre-game lineups and availability.** Replace as-played with posted lineups and an injury/availability feed (free sources only; a paid-only factor is a registered gap). This is the cleanest test of whether the nine matter beyond what the line already knows.
2. **Add what the market is likely to price better than we do:** weather and wind (park-conditioned), umpire zone, and a rank-vs-history split so a factor is read against the same point in past seasons (granularity index parts 2 and 4).
3. **Fit to the market, not to the constant.** Predict the residual `outcome − market` with a regularised model on ≥ 2 seasons of archive (the archive holds Aug 2026 onward only, so this needs the 2027 season to accrue), score with `quant/blend.py` at ≥ 15 clusters per fold.

## When could the MLB engine start logging?
Opening Day 2027 (expected late March 2027 — confirm against the schedule). **A pre-registration must be committed before the first logged row**: which model arm, which markets (moneyline, total rung nearest 50%, run line), the scoring look at a judged n, and the pre-stated modal outcome ("w ≈ 0 against the closing line"). Target to commit it: the first week of March 2027, shadow only — evaluate and log, no orders. Nothing here changes any order, stake, `kelly_fraction` or ledger.

Files: `src/prediction_market_bot/mlb_engine/{lineup_aware,model_lineup,market_line}.py`, drivers `12_EXPLORATORY/mlb_engine/run_w106_4.py` and `run_w106_4_market.py`, results `RESULTS_W106_4.json` and `RESULTS_W106_4_MARKET.json`.
