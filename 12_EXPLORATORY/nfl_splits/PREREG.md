# EXP-NFLSPLITS-001 — NFL factor splits on team totals and alternate ladders (pre-registration)

**Last reviewed:** 2026-11-24 (W126.5, B-013). **Status:** pre-registered, committed before any outcome (score, margin, total) is joined to any
leaf. Docs-only commit. Doctrine: DOCTRINE.md §1 (ADR-0077), W117 stump rule, COMMON_RULES_W126.

**Measure moved:** DEPTH D5(b), NFL factor classes by stage (aggregated / interpreted / applied). A factor is *applied* when it is a tested
split scored per leaf on net after costs, held out, per arm. A tested null counts as applied: it is a routing result.

## 1. What is tested
Five NFL factor classes as layer-3 splits, each a **market-anchored adjustment**: the price is the consensus-anchored `board_v2` pmf, and the
split asks whether a leaf's realised outcomes sit away from that price by more than costs. Never "model_p vs market" as the verdict.

| Split | Seat factor | Leaf definition (fixed now) | Inputs, point-in-time |
|---|---|---|---|
| S1 QB | N1-class availability | team starts a QB different from its previous regular-season game's starter = `qb_new`; else `qb_same`. Game level: `any_new` / `none`. | nflverse `home_qb_id` / `away_qb_id` (the starter is known pre-kick; a late scratch is not modelled) |
| S2 rest | rest / travel | team rest days: `short` ≤5, `normal` 6-8, `long` ≥9. Game level: rest differential home-away `≥+3`, `≤-3`, else `even`. | nflverse `home_rest`, `away_rest` |
| S3 officials | N12 | referee prior = mean (total − total_line) over the referee's games in **earlier seasons and earlier weeks only**, shrunk to zero with k=20 games; terciles fixed on the fit seasons: `ref_high`, `ref_mid`, `ref_low`. No prior games → `unknown`. | nflverse `referee` |
| S4 weather | N-weather | forecast-only temp / wind buckets from `weather_factor` (dome = `dome`; `wind≥15` or `temp≤32` = `adverse`; else `benign`). `assert_priceable` refuses realised weather. No forecast snapshot → `unknown`. | `filter_data/nfl_*.csv` forecast snapshots (2022+) |
| S5 matchup | scheme / matchup | `MatchupBook` cross score terciles, fit-season cut points: `mu_high`, `mu_mid`, `mu_low`. Available 2022+ only; earlier seasons → `unknown`. | `matchup_cross.MatchupBook`, pre-game plays only |

`unknown` leaves are never scored as a split leaf. They are reported as a count.

## 2. Markets, prices, arms
- **Markets (per game, rungs fixed):** TT team total (both teams; consensus = (total ± spread)/2 from the closing line only), AS alternate spread
  (home side; away is the complement, not double-counted), AT alternate total. Rungs = round(consensus) + {−6, −3, 0, +3, +6} for TT and
  {−7, −3, 0, +3, +7} for AS and AT. Kalshi strike convention "gt": YES = value strictly above the strike (`board_v2.p_team_ge`, `p_margin_ge`, `p_total_ge` at k+1).
- **Proxy prices (declared plainly).** No Kalshi history exists for 2019-2025 NFL spread, total or team-total series (KALSHI_HISTORY holds
  KXNFLGAME only). The 2019-2025 prices are the `board_v2` pmf anchored to the nflverse closing spread and total, built from earlier seasons
  only (expanding library via `build_library(before_season=s)`). They are **proxy prices, not tradable quotes.** Rungs priced <0.02 or >0.98 are dropped.
- **Arms per leaf:** RIDE = buy the side priced ≥ 0.50; FADE = buy the other side; NO BET. (FADE on a wing rung is the longshot / pot-of-gold arm.)
- **Payoff:** buy YES at p: gross = y − p; buy NO: gross = p − y. Cost = `quant.costs.fee_per_contract(series, price)` + half-spread. Net = gross − cost.
- **Half-spread constant, measured not assumed:** median interior-price (0.10-0.90) half-spread in `PRICE_ARCHIVE/prices_2026-*.jsonl`, 2026-11-24:
  KXNFLSPREAD 0.005 (n 376,580), KXNFLTOTAL 0.010 (n 269,488), KXNFLTEAMTOTAL 0.015 (n 235,480). Headline uses these medians for AS, AT, TT.
  Sensitivity row at the archive means (0.0155, 0.0248, 0.0222). Gross, cost and net are reported side by side in every row.
- **Leaf = split bucket × market × price band.** Price bands: `mid` (side price 0.25-0.75) and `wing` (outside). One row per leaf × arm.

## 3. Fit, judge, pooling, multiplicity
- **Fit seasons 2019-2024** (S4 and S5: only seasons where the input exists). Per leaf, per arm: clustered mean net (cluster = game,
  `variance.clustered_mean`). **Partial pooling** across the leaves of one (split, market, arm) via `quant.variance.partial_pool`.
  Arm per leaf = the arm with the larger shrunk fit mean if its 90% shrunk interval lower bound > 0; otherwise NO BET. Fixed before 2025 is read.
- **Judge set 2025 regular season** (held out, never touched in the fit). Judged rows = leaf × arm where the fit routed to an arm. The
  judged statistic is the 2025 mean net per bet, game-clustered bootstrap (`quant.inference.cluster_bootstrap`, B=2000, seed 20261002), 90% interval.
  One-sided p from `pooled_cluster_test`. **BH q = 0.10** over all judged rows (family size reported). A leaf is *judged* only with ≥ **MIN_N = 40
  games** in 2025; below that it prints "not judged: n below MIN_N" with its n.
- **Both arms are always printed** for every leaf on 2025 (descriptive), so a fit-routed NO BET leaf still shows whether either arm would have cleared. Only fit-routed rows enter BH.
- **2026 look (separate, descriptive, no BH):** games that have real Kalshi ladders in the price archive and a settled outcome at the run time,
  scored at the archive's own bid / ask. Reported next to the 2025 rows, never pooled with them.
- **2026 shadow rows "from this commit forward":** none exist yet (Part B ships default off). The forward look is pre-registered here for when
  `variance.games_needed` (from the 2025 SD and ICC) is met. It is not read before then.

## 4. Verdict words (routing words only)
- **arm earned in this leaf** — 2025 net > 0, interval excludes 0, BH-significant at q 0.10.
- **routed to ride / no bet in this leaf** — judged, none of the above.
- **not judged: n below MIN_N** or **not judged: inputs unknown**.
- A losing look closes only this hypothesis ("hypothesis closed, EXP-NFLSPLITS-001, parked for R&D"). No cell, market or arm closes.

## 5. Overlap with earlier looks (stated, not hidden)
W110.1 scored 82 weather / matchup leaves on sides and totals at the book's own price over 2013-2025: 0 earned an arm. W93.4 found board_v2
matches Kalshi on 86 settled 2026 games, and N15 null. W85.1 / W94.2 scored the earlier NFL engines. This test is new on **team totals and
alternate ladders at proxy prices**, and S1-S3 have not been scored per leaf on these markets. S4 and S5 largely repeat W110.1's inputs on new
markets; expect the same answer.

## 6. Modal outcome, and what each result does
**Expected: no arm earned.** Most leaves routed to ride / no bet; several not judged for n (2025 has 272 games, so rare leaves such as `qb_new` fall under MIN_N).
Proxy prices carry the consensus's own information, so a null here is the modal case and is not a failure. If any leaf earns an arm it is
reported as "arm earned on proxy prices", not as tradable: the 2026 archive look and the forward look decide whether it survives real quotes.

## 7. Part B contract (code, default off)
`decision_trees/filters/nfl_splits.py` returns the leaf name for each split from pre-game inputs only (PITViolation guard, `unknown` for
unjoined inputs; template `filters/nba_props.py`). Registered as an `nfl_splits` entry in `shadow_route.CANDIDATES` behind `PM_CANDIDATE_ARMS`;
shadow only, orders follow v1, kelly_fraction untouched. Seat-file stages move to `applied` only for splits with ≥ 1 judged leaf in RESULT.md.
