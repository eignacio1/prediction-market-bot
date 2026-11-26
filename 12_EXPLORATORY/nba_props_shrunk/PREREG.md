# EXP-047-S — shrunk per-minute rates × shrunk minutes, carried through C2's usage shift, vs C2 as logged (PRE-REGISTRATION)

**Written:** 2026-11-25 (W129.2), committed and pushed before any judged row is read. **Status:** PRE-REGISTERED.
**Licence:** H-DEPTH-PAM-3 SUPPORTED (`12_EXPLORATORY/pam_stability/RESULT.md`, PREREG frozen at `16fcd204d5e41995c761d8e3d27b71c121024620`,
§7 "an EXP-047 challenger using the shrunk mu, with its own pre-registration"). This is that pre-registration. **Doctrine:**
HYPOTHESIS_DOCTRINE.md Part I binds. **Purpose (Hard Rule 12):** DEPTH D3 (a pre-registered challenger for the NBA props arm), D5(b) PAM
class 3 (interpreted → carried toward applied), PROOF P2.

## 1. Claim
Control is **C2 exactly as logged** (`nba_engine_props_c2_forecaster.py`, `MODEL_ID nba_engine_v2_props_c2_w126_2`, λ frozen: rebounds 0.26,
assists 0.31, threes 0.27 on a 3PA basis, points full absorption). The challenger changes **one thing**: the per-player base mean fed to
C2's usage shift. Control base = unweighted trailing mean of prior games on this team. Challenger base = shrunk per-minute rate × shrunk
minutes (PAM-3 §4), then the identical `c2_means(...)` usage shift, the identical engine draws (`nba_engine.props.player_draws`) and
the identical strike-probability code. The claim: the shrunk base prices P(stat ≥ k) better than the raw base **after** the usage shift,
i.e. PAM-3's gain survives the lineup adjustment instead of being absorbed by it.

**What this test can and cannot show (ADR-0077).** It scores the input against outcomes, not the market. A pass licenses the challenger
as a logged candidate beside C2; it is **applied** only when the router scores it as a split per leaf on net after costs per arm. It is
never the verdict on a cell.

## 2. The judged population, and the check that it is unread
**Judged: NBA 2025-26 regular season** (game dates 2025-08-01 .. 2026-07-31; previous season for the priors is 2024-25).
Check against every test that touched player-prop outcomes (read from the frozen files, not recalled):
| Test | Seasons judged | Touches 2025-26? |
|---|---|---|
| EXP-047-C2 (`nba_props_role/PREREG_C2.md`, `RESULT_C2.md`) | judged 2023-24; fit 2022-23 | No |
| H-DEPTH-PAM-3 (`pam_stability/PREREG.md` §2) | judged 2022-23, 2023-24, 2024-25 | No: **explicitly excluded** |
| EXP-047-C1 (`nba_props_role/PREREG.md`, `run_retro.py` `JUDGE_FROM = 2024-10-01`) | 2024-25 **and 2025-26** | **Yes, for a different challenger** |
**Disclosures.** (a) 2025-26 is the only season neither C2 nor PAM-3 judged; PAM-3 excluded it because it is the season behind the
operator's fantasy test that **motivated** the shrinkage design, so the idea was shaped by looking at this season at the level of a
human's figures (0.90 / 0.69 / 0.81 reliabilities), not at these rows. (b) C1's retro scored a different challenger (full-absorption
usage) on 2025-26 and C2 was designed afterwards; C2's λ were fitted on 2022-23 only, so 2025-26 outcomes did not set any number used
here. (c) The k values below were fitted on 2016-2022 and are not refit. A reader should weigh the result as one judged on a season that
is **not fresh to the program**, though unread by either parent test. Forward 2026-27 rows (§9) are the genuinely out-of-sample check.

## 3. Units, eligibility, injuries
- Games: 2025-26 regular season with a **usable pre-tip injury report** (the same `last_report_before_tip`, `LEAD_MIN` rule as C2's
  judge; injury coverage from `20261012_nba_points_minutes/inj` and `20261013_nba_games_availability/inj2026`). Games with no usable
  report are dropped for both arms alike and the count is reported.
- Roster per team-game: EXP-047's `roster()` (≥ 4 prior games on this team this season, mean minutes ≥ 10, top 10 by prior mpg), ranked
  on the **control's** mpg for both arms (the challenger does not re-rank). Players listed Out are not scored; a rostered player who did
  not play is dropped (a prop on him voids).
- Stats and ladder (as C2): points 10/15/20/25/30; rebounds 4/6/8/10/12; assists 2/4/6/8/10; threes 1/2/3/4.
  Unit (player-game, stat, threshold); **cluster = game**. Population is every such unit, with or without an Out player (C2 equals its base
  where nobody is Out). Secondary slice: games with at least one Out player, where the two arms differ in usage as well as in base.

## 4. The two inputs
- **Control:** `NBAEnginePropsC2` as logged. Nothing changed, nothing refit.
- **Challenger** (per player, per stat s; PAM-3 §4):
  - `shrunk_rate = (M·r_obs + k_s·prior_s)/(M + k_s)`, M = prior minutes this team-season, r_obs = prior per-minute rate;
    `prior_s = (m_prev·r_prev + 500·r_league)/(m_prev + 500)`, r_prev = the player's 2024-25 per-minute rate (any team, matched on the
    normalised player name), r_league = 2024-25 league rate at his previous-season minutes band (cuts 15/22/29 mpg; no previous season →
    band from this season's mean minutes and league rate, no player term).
  - **k_s fixed from `pam_stability/trait_reliability_draft.json` (fitted 2016-2022 only): points 60.1, rebounds 27.3, assists 30.2,
    threes 66.7 (pseudo-minutes); k_min 0.821 games.** Not refit on 2023+ seasons.
  - `shrunk_minutes = (n·m̄ + k_min·m_prev_mean)/(n + k_min)` (no previous season → raw mean).
  - `mu = shrunk_rate × shrunk_minutes`, floored at the engine's `MU_FLOOR`. The vector is then passed through `c2_means(base, p_play,
    attempts, λ)` with C2's frozen λ. Threes use C2's 3PA-attempt weights, which stay the raw trailing mean of attempts (not shrunk;
    reported as a limitation).
- **Distribution layer:** identical engine draws for both arms (the logged arm's frozen layer). **No dispersion is fitted on this
  season or any other**; each arm is priced exactly as it would be live.

## 5. Outcome, metric, interval, rule (PAM-3's form)
- Outcome 1{actual ≥ k} from the box score. Probabilities clipped to [1e-4, 1 − 1e-4] as in C2.
- **Primary metric:** mean log-loss over all units; **D = LL(control) − LL(challenger)** (positive = challenger better). 90%
  game-clustered bootstrap, 2,000 resamples, seed 20261121. D is computed pooled and per stat.
- **SUPPORTED:** pooled D's interval wholly above zero **and** D > 0 in at least 3 of 4 stats.
- **NOT SUPPORTED:** pooled D ≤ 0, or fewer than 3 of 4 stats positive. Text: "hypothesis closed (EXP-047-S, parked for R&D)".
- **UNDERPOWERED:** pooled D > 0 with an interval that includes zero.
- Secondary, reported, never the verdict: per-stat D with BH at q 0.10 over the 4 stats (one-sided bootstrap p for D ≤ 0, floor
  1/2001); Brier per stat; D by prior-games stratum (4–10, 11–30, 31+); D in the Out-slice vs the rest; a decomposition (shrunk rate ×
  raw minutes; raw rate × shrunk minutes) through the same C2 shift; rows and games dropped.
- **Power (`quant/inference.mde_paired`).** PAM-3's per-game sd of D ≈ 0.0063 (from its 90% interval: half-width 0.000175 over 3,519
  games). With ≈ 1,150 usable games, `mde_paired(0.0063, 1150)` ≈ **0.00046**; PAM-3's pooled D was 0.00201, so the test can detect
  about a quarter of that effect. If usable games < 600 the MDE exceeds 0.00063 and an UNDERPOWERED reading is stated as such.
- **Pre-stated modal outcome (P3):** SUPPORTED, pooled D ≈ +0.0010 to +0.0020 (smaller than PAM-3's 0.00201 because the usage shift
  already moves part of the mean), gain concentrated in the 4–10 prior-games stratum, largest for threes and assists, near zero for
  points in 31+. The live alternative is NOT SUPPORTED if the shift absorbs the shrinkage gain (about one in five).

## 6. Leakage and integrity
- Every input for game G uses games dated strictly before G; 2024-25 totals are complete before 2025-26 starts. No 2025-26 outcome sets
  any constant here. The run happens **once**; a deviation is a dated addendum written before the result it would change.
- Known-answer test before the real run (`tests/test_w129_2_props_shrunk.py`): planted per-minute rates and planted reliability recovered
  within tolerance; a planted zero-noise case where the shrunk mean does **not** beat the raw mean; no-Out games where challenger and
  control differ only through the base; with k = 0 the challenger reproduces control's rate × raw minutes exactly.
- C2 and v1 stay byte-identical (§8 test). Reads are from `PredictionMarketEvidence`; no write outside the experiment directory.

## 7. Consequence
- **SUPPORTED:** class 3 is carried to the C2 chain; the challenger logs forward as a candidate beside C2 (§8) and the router scores it
  per leaf on net after costs per arm, the path to applied.
- **NOT SUPPORTED:** hypothesis closed (EXP-047-S, parked for R&D). The forward log still runs (shadow cost is nil) so the 2026-27 rows
  can reopen it; reopen triggers as PAM-3 §7 plus a threes model on 3PA shrinkage.

## 8. Part C — forward shadow
`PM_PROPS_SHRUNK` (default on, `off` is the off-switch, as C2) logs `NBAEnginePropsShrunk` rows to its own ledger beside C2. C2 and v1
output stay byte-identical; no orders; Kelly stays 0. The previous-season table is a frozen per-player file built from the event store
(2025-26 totals for the 2026-27 season). Hard Rule 14: the runner and timer already exist, so no new component; `surface_delta` is
stated in the handoff.

## 9. Forward check
2026-27 rows from §8 are scored by the same rule on a later read with a new pre-registered n from `mde_paired`; not part of this verdict.
