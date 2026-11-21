# H-DEPTH-PAM-3 — stability-weighted shrinkage vs unweighted means for the NBA props arm (PRE-REGISTRATION)

**Written:** 2026-11-21 (SW-9), committed before any data for this test is read or scored. **Status:** PRE-REGISTERED.
**Design note:** `02_ARCHITECTURE_DESIGN/PAM_ATTRIBUTE_CLASSES.md` class 3. **Doctrine:** HYPOTHESIS_DOCTRINE.md Part I binds.
**Purpose (Hard Rule 12):** DEPTH D5(b) (class 3, player level: absent → interpreted if supported) and D3 (a pre-registered challenger for
EXP-047).

## 1. Claim
For the live pre-game NBA props arm (EXP-047, `pregame_shadow/nba_engine_props_forecaster.py`), a player's expected stat built from
**per-minute rates shrunk toward his own prior by stat-specific reliability**, times **shrunk expected minutes**, gives better-calibrated
P(stat ≥ k) out of sample than the arm's own input: the **unweighted mean of every prior game on this team** (`roster()`, eligibility
`MIN_PRIOR_GAMES = 4`, `MIN_MPG = 10`, top 10 by minutes).

Mechanism: noisy traits (threes, assists early in a season) carry full weight after four games in the control; stable traits gain little
from shrinkage, noisy ones gain most.

**What this test can and cannot show (ADR-0077).** It scores the input against outcomes, not against the market. A pass makes class 3 a
stronger *interpreted* factor and licenses a challenger. The factor is **applied** only when that challenger is scored by the router as a
split per leaf on net after costs per arm. A Brier or log-loss result here is never the verdict on a cell.

## 2. Data
- NBA event store (`c1_signal_ingestion/nba_event_store.py`, free sportsdataverse releases): player box scores with minutes, points,
  rebounds, assists, threes made; team and game ids; game dates. Regular season only.
- **Training seasons (fit everything): 2016–2022** (season label = year the season ends; 2015-16 .. 2021-22).
- **Judged seasons: 2023, 2024, 2025** (2022-23 .. 2024-25), read once, after this file is committed.
- **Excluded: 2026** (2025-26, the season behind the operator's fantasy test that motivated this) and 2027 (in progress).
- Not used: PAM records (all `recorded_at` 2026-05-28: look-ahead for every judged season), injury reports, market prices.

## 3. Units and eligibility (replicates EXP-047, built from the box scores)
For each team-game G in a judged season and each player P on that team: eligible if, counting only P's games **on that team, in that season,
strictly before G's date**, P has ≥ 4 games and mean minutes ≥ 10, and P is in the team's top 10 by that mean. A player who did not play in
G is dropped (a prop on him voids). Stats: points, rebounds, assists, threes. Thresholds (synthetic ladder, both arms identical):
points 10 / 15 / 20 / 25 / 30; rebounds 4 / 6 / 8 / 10 / 12; assists 2 / 4 / 6 / 8 / 10; threes 1 / 2 / 3 / 4 / 5.
Unit of scoring: (player-game, stat, threshold); **clustering unit: game**.

## 4. The two inputs
- **Control (EXP-047 as frozen):** mu = mean of the stat over the eligible prior games.
- **Challenger (shrinkage):** mu = shrunk_rate × shrunk_minutes, where for each stat s, rate = stat per minute:
  - `shrunk_rate = (M · r_obs + k_s · prior_s) / (M + k_s)`, M = prior minutes this season on this team, r_obs = their per-minute rate.
  - `prior_s` = the player's previous-season per-minute rate (any team), blended to the league rate at his minutes band with 500
    pseudo-minutes: `(m_prev · r_prev + 500 · r_league) / (m_prev + 500)`; no previous season → league rate at his minutes band. League
    rates from the previous season only.
  - `k_s` (pseudo-minutes) from **split-half reliability on training seasons**: within each training player-season with ≥ 1,000 minutes,
    split games odd / even, correlate per-minute rates across players, Spearman-Brown correct to the full sample size M̄, then
    `k_s = M̄ · (1 − r) / r`. One k per stat; fixed before any judged season is read.
  - `shrunk_minutes = (n · m̄ + k_min · m_prev_mean) / (n + k_min)`, n = prior games, m_prev_mean = previous-season minutes per game (no
    previous season → this season's raw mean, no shrinkage); k_min from the same split-half rule on minutes per game.
- **Distribution layer, same form for both arms:** P(stat ≥ k) from a negative binomial with mean mu and dispersion r_s fitted **per arm,
  per stat, on training seasons only** (each arm gets its own best dispersion, so the challenger is not helped by a shared one).

## 5. Outcome, metric and rule
- Outcome: 1{actual stat ≥ k} from the box score.
- **Primary metric:** mean log-loss over all judged (player-game, stat, threshold) units; effect D = log-loss(control) − log-loss(challenger)
  (positive = challenger better). Interval: 90%, game-clustered bootstrap, 2,000 resamples, seed 20261121.
- **SUPPORTED:** D's interval wholly above zero **and** D's point estimate above zero in at least 3 of the 4 stats.
- **NOT SUPPORTED:** D's point estimate ≤ 0, or fewer than 3 of 4 stats positive.
- **UNDERPOWERED:** D > 0 with an interval that includes zero (state the n needed with `quant/inference.mde_paired`).
- Secondary, reported, never the verdict: Brier per stat; per-stat D with BH at q 0.10 over 4 stats; D by prior-games stratum
  (4–10, 11–30, 31+); reliability table (r_split_half, r_year_to_year, k) for the four stats **and** for blocks, steals, FT% (descriptive,
  set beside the operator's test figures 0.90 / 0.69 / 0.81); a decomposition arm (raw rate × raw minutes) so structure and shrinkage
  are separated.
- **Pre-stated modal outcome (P3):** SUPPORTED, with the gain concentrated in the 4–10 prior-games stratum and largest for threes and
  assists, near zero for points by the 31+ stratum.

## 6. Leakage and integrity rules
- Every input for game G uses only games dated strictly before G; previous-season quantities are complete before the judged season starts.
- k_s, k_min, dispersions and league rates are fitted on training seasons only; nothing is tuned after a judged season is read.
- Known-answer test before the real run: simulated players with planted true per-minute rates and planted reliability; the code must
  recover k within its interval and the challenger must beat the raw mean on the simulation; on a planted zero-noise case it must not.
- A deviation from this file is a dated addendum written before the result it would change.

## 7. Consequence
- **SUPPORTED:** class 3 at player level moves absent → interpreted (NBA). Next: an EXP-047 challenger using the shrunk mu, with its own
  pre-registration, logged beside the live map as a candidate and scored by the router per leaf on net after costs — the path to applied.
  `trait_reliability` (design note §3 C) gets its first rows.
- **NOT SUPPORTED:** hypothesis closed (H-DEPTH-PAM-3, parked for R&D). Reopen triggers: possession-based rates, archetype priors once PAM
  is point-in-time, or a different arm (NFL props) with noisier short samples.

## 8. Run
Code to be written as `12_EXPLORATORY/pam_stability/run_pam3.py` with its known-answer test, landing through a PR with CI green; output
`RESULT.md` + `results.json` quoting this file's commit SHA. Read-only; no live path, model, runner or leaf map is touched.
