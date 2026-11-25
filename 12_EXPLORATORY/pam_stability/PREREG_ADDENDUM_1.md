# H-DEPTH-PAM-3 — PREREG addendum 1 (written 2026-11-24, before any judged season 2023-2025 is read or scored)

Binds with `PREREG.md` (frozen at 16fcd204; unchanged). Each item fills a gap the frozen text leaves open or states an arithmetic fact.
None is chosen after seeing a result: the judged seasons have not been loaded by any code at the time of writing.

- **A1 Minutes band (§4 prior_s).** "His minutes band" = the player's previous-season minutes per game, cut at 15 / 22 / 29 (four bands:
  <15, 15-22, 22-29, 29+). A player with no previous season is banded on his current prior minutes per game. League rate for a band =
  total stat / total minutes over all previous-season player-seasons in that band (all teams, regular season).
- **A2 Dispersion fit seasons (§4).** The challenger's prior needs a previous season, so 2016 has no challenger mu. Both arms' dispersions are
  fitted on the same units from **2017-2022** (training seasons with a previous season in the store). k_s and k_min still use 2016-2022.
- **A3 Reliability arithmetic (§4).** Split-half r = Pearson across players, computed per training season and pooled by Fisher z weighted by
  n-3; Spearman-Brown r_full = 2r / (1 + r); M̄ = mean total minutes of the qualifying player-seasons (n̄ = mean games for minutes per game);
  k = M̄(1 − r_full)/r_full, r_full clipped to [0.05, 0.999]. Games are ordered by date, odd / even by position. Year-to-year r (descriptive)
  = Pearson of full-season per-minute rates, player-seasons ≥ 1,000 minutes in both seasons t and t+1, t = 2016..2021, Fisher-pooled.
  Interval = 90% player bootstrap (500 resamples) on the split-half r, carried to k.
- **A4 Decomposition arm (§5).** "Raw rate × raw minutes" equals the control exactly: (Σstat/Σmin) × (Σmin/n) = Σstat/n. It is computed and
  reported as that identity (max abs difference), and does not separate structure from shrinkage. The separation is done by two partial arms,
  reported secondary only: **rate-only** (shrunk rate × raw mean minutes) and **minutes-only** (raw rate × shrunk minutes).
- **A5 Numerics.** mu floored at 0.02 for both arms; probabilities clipped to [1e-6, 1 − 1e-6] for log-loss and Brier. NB parametrisation
  var = mu + mu²/r; r fitted by maximum likelihood on training units. Top-10 ties broken by lower person_id.
- **A6 Eligibility mapping (§3).** "Played in G" = minutes > 0 in G's box row; DNP rows (blank minutes) are not games. "Prior games" =
  games with minutes > 0 for this team this season dated strictly before G. Regular season = `season_type_id == 2`. Season label = year
  the season ends (the store's own `season` column).
- **A7 Bootstrap.** `quant/inference.cluster_bootstrap` is a per-row Python loop (about 1e9 operations at this n). The run uses a local
  numpy version with the same algorithm (resample whole games, ratio of sums, percentile interval), named `game_bootstrap` in
  `run_pam3.py`, one set of resampled games shared by every statistic so the per-stat and stratum intervals are mutually consistent. The
  one-sided p for BH is the share of resamples with mean ≤ 0 (floor 1/(b+1)). MDE for UNDERPOWERED uses `inference.mde_paired` with the
  per-game sd of game-level mean differences and n = games.
- **A8 FT% reliability (§5, descriptive).** Per-attempt rate FTM/FTA, split-half by game parity, player-seasons with ≥ 200 FTA in the season (training seasons only); k in attempts. Blocks and steals follow the per-minute rule of A3.
- **A9 Judged-run guard.** `run_pam3.py` refuses to load 2023-2025 unless `--final` is passed, and `--final` is run once, after the
  known-answer test is green on CI-equivalent local run. Any development smoke test uses training seasons only (train 2016-2020, check
  2021-2022) and nothing is tuned from it.
