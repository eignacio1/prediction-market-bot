# W69.3 — NBA player points: projected-minutes challenger — PLAN (EXPLORATORY, frozen before fitting)

**Purpose (Hard Rule 12):** DEPTH D1 — first NBA model conditioning on availability (who plays, how many minutes); D3 +1 only if a pre-registration is earned.
**Status:** plan written and committed BEFORE any challenger is fit. Nothing here is evidence about EXP-039's sealed cells (CHARTER rules 1-8 apply; no shadow row, ledger or log is read).

## 1. What is challenged
EXP-039's frozen `nba_player_points_v1` (ridge λ=100 mean → one NB per player-game, dispersion MLE, Platt on logit, strikes 10/15/20/25; 10 box-score features; **no availability input**).
Points = minutes × rate. Minutes move with injuries, rest and rotation, which are reported before tip. EXP-039 §7 names availability its largest known weakness.

## 2. Data (all off-box, past seasons only)
* Box scores: ESPN, 4 seasons (2022-23 … 2025-26, labelled by ending year 2023…2026), custody copy `PM-worktrees/_w65_data/` (same files EXP-039 trained on). Regular season only.
* **Point-in-time injury reports — source named:** the league's own official NBA Injury Report PDFs, `https://ak-static.cms.nba.com/referee/injury/Injury-Report_<YYYY-MM-DD>_<HH><AM|PM>.pdf` (public, free, one file per hourly slot, internally stamped `HH:30`). Verified reachable for 2022-12, 2023-12, 2024-12 before this plan was written. Parsed with `pypdf` layout mode.
* **Point-in-time rule:** per game, the snapshot is the latest report on the **2-hourly grid 11:30/13:30/15:30/17:30/19:30 ET** (amended before fitting from hourly: fetch+parse compute budget) whose slot `H:30 ≤ tip − 4h` (T2 band's earliest edge; so it is knowable at every T2/T3 evaluation), same ET date as the game. A game tipping before 15:30 ET therefore has no report and is flagged; none found → `inj_missing=1`, injury features zero (coverage reported). A report is never read past its slot.
* **Not available point-in-time (stated, not hidden):** a true *starter* flag — the stored ESPN rows do not carry it and re-pulling 4 seasons is out of block. Proxy used instead: the player's rank in his team's rolling 10-game minutes (`min_rank`). Late scratches after the snapshot are, by construction, unseen — that is the realistic live condition.

## 3. Arms (fixed now)
| arm | inputs |
|---|---|
| `ctrl_refit` | frozen spec (10 features), refit per fold — the control, so a refit difference is not credited to minutes |
| `minutes_box` | ctrl + `min30`, `min_rank` (box-score-only minutes) |
| `minutes_inj` (**primary challenger**) | minutes_box + `out_min` (sum of recent `min10` of teammates listed Out/Doubtful), `out_fga` (their `fga10`), `own_quest` (self listed Questionable/Doubtful yet played), `own_prob`, `inj_missing` |
Same ridge λ=100, same NB mean-floor 0.5, dispersion MLE + Platt refit on each fold's calibration season (exactly the frozen recipe). The actual frozen artifact is also scored on the 2026 fold (sanity: must ≈ `ctrl_refit`).
Conditional on playing (DNP rows excluded, as Kalshi settles them to a fair price and EXP-039 excludes them). Rows need ≥10 prior games (same rule).

## 4. Rolling origin (seasons by ending year)
Fold A: train 2023 · calibrate 2024 · **test 2025**. Fold B: train 2023-24 · calibrate 2025 · **test 2026** (identical to the frozen split). Test seasons are never used for any choice.

## 5. Statistic, clustering, multiplicity
Δ = Brier(challenger) − Brier(`ctrl_refit`), per strike (10/15/20/25), negative = challenger better. **Cluster = the game**; bootstrap B=20000, seed 20261012, pooled over both test seasons.
**m = 8** = NBA challengers ever tested against the EXP-039 frozen model (none before this study) → 2 arms × 4 strikes. α = 0.05/8, **corrected CI = 99.375%**.
**Decision (fixed now):** a PROPOSED pre-registration is drafted only if `minutes_inj` has ≥1 strike whose corrected CI excludes zero in favour of the challenger, AND the point estimate is favourable in BOTH test seasons for that strike, AND the star subset (`pts10≥15`, the closer proxy for the live two-per-game board) point estimate is also favourable. Else NO.
Descriptive extras (not decisions): all-strike mean Δ, star-subset Δ per strike, RMSE of mean points, minutes-model fit.

## 6. Market comparison
Kalshi `KXNBAPTS` history: **none archived pre-2026** (`KALSHI_HISTORY_MANIFEST.md` covers KXNFLGAME only); live 2026-27 rows are sealed-cell data (CHARTER rule 2) and are not read. So the challenger cannot be measured vs the market here; a pre-registration, if earned, is judged against the MARKET on rows dated after acceptance.

## 7. Expected modal outcome (stated before fitting)
NO or negligible. Minutes are largely predicted by recent minutes already in the frozen `min10`; the injury report adds information on the few games where a rotation player is out. Expect a small gain concentrated at strikes 20/25 (usage) and not enough n to clear a 99.4% CI. Expected |Δ| < 0.002 Brier.
Scratch-timing caveat: the snapshot is ≥4h before tip; the market sees later news, so even a real gain here is an upper bound on what the model would add over the market.
