# EXP-036 / T-607 — NHL pregame shadow pipeline: results (Wave 47 block fly-nhl-pregame)
Date 2026-10-02. One STANDARD deliverable. SHADOW = evaluate-and-log only; no order, position, fill, sizing or kelly path (enforced by `tests/test_nhl_shadow_safety.py`).

## Status
| Deliverable | State |
|---|---|
| D0 base SHA / reuse / live ticker + settlement-rule verification | done |
| D1 NHL C1/C2 (cutoff enforced, missing-goalie + postponed tests) | landed on main |
| D2 frozen model `nhl_pregame_v1` (artifact hashed, held-out reliability) | landed on main |
| D3 pre-registration, 9 cells | pushed ALONE (`0902d32`, branch `exp036-prereg-2026-10-02`) BEFORE any scoring. **Not on main yet.** |
| D4 shadow runner + settle + cron | landed; **cron INSTALLED and verified live** |
| D5 this summary | done |

## Data / goalie / model
- Source: public NHL web API (`api-web.nhle.com/v1`), 2021–2025 regular seasons backfilled (6,576 boxscores, 5 x 1,312-game seasons + 2026 schedule). Raw store gitignored; synced to VPS by rsync.
- Cutoff: a game is usable at `as_of_utc` only if `start_time_utc + 3h <= as_of_utc` (event time, not fetch time). `assert_cutoff` raises.
- Goalie: T3 uses confirmed starter when passed; T1/T2 project last starter (`starter_source=projected_last_start`); unknown goalie falls back to league prior (`goalie_known=0`). The NHL landing endpoint has no projected-starter field — real projected-starter source is a gap.
- Model: one bivariate correlated-Poisson goals distribution incl. OT/SO as Kalshi settles; moneyline, every puck-line and total strike derived coherently. Train 2021–23, Platt-calibrate 2024, held-out 2025-26. **Deviation from ADR-0004 (LR+Platt): documented-equivalent used; needs an operator decision.**
- Held-out honest read: moneyline beats climatology by only ~0.002 Brier and the LR benchmark is better (0.2456 vs 0.2473); totals under-predicted 5–10 pts; away 2.5 puck line and both totals are slightly WORSE than climatology. Not suppressed; pre-registration expects ΔBrier vs market ≤ 0.

## Backtest
Climatology-only (no 47.1 market history exists, so no ΔBrier-vs-market or E_net backtest is possible). Stated in the pre-registration.

## Live rows (VPS, real model, first scheduled firing 2026-10-02 23:30 UTC)
| Cell | rows | scored (n) |
|---|---|---|
| NHL_MONEYLINE_T3 | 2 | 0 |
| NHL_PUCK_LINE_T3 | 4 | 0 |
| NHL_GAME_TOTAL_T3 | 9 | 0 |
| all T1/T2 cells | 0 on cron so far (T1 fires 14:00 UTC; T2 window was empty at 23:30) | 0 |
Dry-run (no write) before install: T1 evaluated 180 rows, T3 15, T2 0. T1 abstained on some markets (real model 195 vs 240 stub rows in an earlier dry run) — cause NOT yet investigated.
**Scored n = 0 for every cell versus judged n = 2,500 games/cell.** Nothing here is evidence of edge or its absence; first scored rows arrive after tonight's games end (hourly settle cron at :15). Any early score is PRELIMINARY.
Cells with valid rows for 47.2 to flip registry status: NHL_MONEYLINE_T3, NHL_PUCK_LINE_T3, NHL_GAME_TOTAL_T3 only. The six T1/T2 cells have none yet.

## Cron (installed under the 2026-10-02 operator authorization)
Lines are committed in `deploy/cron.nhl_shadow` (`6a44430`), same commit as install. Dry-run by hand per line on the VPS first; safety test green. Existing crontab untouched (diff vs backup: 0 removed lines; backup `/root/crontab.bak.*`). Live `crontab -l` shows the 7 NHL lines (backfill 09:00; T1 14:00; T2 */30 15-23,0-1; T3 */10 17-23,0-2; settle :15). First firing 23:30 UTC wrote 15 rows to `data/shadow/nhl/` and logged to `logs/nhl_shadow_cron.log`. No service restarted. No `.env` sourced.

## GAPS FOUND (for 47.1 / wave 48)
1. `pregame_shadow/contract.py` and 47.2 runner not on origin/main; my runner + local protocol fallback in use; retire when it lands.
2. ADR-0004 deviation (model class) needs operator sign-off.
3. No projected-starter source for T1/T2.
4. `fee_multiplier=1` was verified 2026-10-02 but is hardcoded; re-read from the series endpoint before any CANDIDATE call.
5. Kalshi OT/SO treatment for ML/puck line assumed to follow the official final result; `TEAM_ALIASES` empty (Kalshi code assumed = NHL abbrev, unverified).
6. Wide live quotes (e.g. bid 0.01 / ask 0.35): scoring must filter on `half_spread`.
7. T1 abstentions uninvestigated; T3 cron window coverage and the 2026 schedule match unverified; travel distance not modelled.
8. Pre-registration branch not merged to main. VPS is not auto-pulled on later pushes.
9. Many T3 firings per game produce correlated rows; judged n must stay game-clustered (as pre-registered).

## Session-start Step 4 / Q6 (adversarial)
- Step 4 ran at session start; the Q7 invariant script reported SOURCE_UNAVAILABLE in the worktree (alarm-only, expected).
- Q6 worries: (a) the model barely beats climatology, so the likely outcome is RULED_OUT or SHADOW-continue, which is the expected and informative result for the most efficient markets; (b) first live rows were produced minutes ago and are a pipeline check, not a result; (c) a shallow T1/T2 starter assumption could bias early-band rows.

---

## Dated note 2026-10-03 (wave 51.2) — coverage boundary: Kalshi 2-letter team codes (GG-403)

The frozen pre-registration is NOT edited. This note records a change in which markets the shadow arm can see.

**Finding.** A read-only Kalshi pull (KXNHLGAME/SPREAD/TOTAL, open + settled; 333 events, 1,595 markets) shows Kalshi uses **2-letter codes for four teams — SJ, TB, LA, NJ** — where the NHL data side uses SJS, TBL, LAK, NJD. The other 28 codes are identical on both sides. The old parsers required exactly 3+3 letters, so every event involving those four teams (**364 of 1,595 markets with a 5-letter team block and 15 with a 4-letter block = 379 markets, ~24%**) returned None with no log. Even a successful parse would not have matched the schedule, which is keyed on SJS/TBL/LAK/NJD.

**Boundary.** Rows written by code before the fix SHA (see 51.2 handoff) contain **no** game involving SJ, TB, LA or NJ; rows after contain them. They are different populations (different team mix, and the first set is a non-random subset of the league). Do not pool them unannounced and do not read the earlier abstentions (195 rows vs 240 expected) as random. The ~45-row shortfall is *consistent with* this drop but the cause was never logged, so it is not proven.

**Counters.** `nhl_shadow_eval.py` now emits per-reason abstention counters (`ticker_unparsed_or_team_unmapped`, `start_unknown`, `no_valid_quote`, `forecast_none:<reason>`, `out_of_band` as a normal exclusion) in its stdout summary and in `data/shadow/nhl/run_log.jsonl`. Runs before the fix have none.

**Status.** Fix is on branch `session/20261003T201919Z-w51-nhl-team-codes`, **not merged** (a main push auto-deploys and restarts t4-mlb during live games, GG-432). Until it is merged and deployed, the VPS arm keeps dropping those games.
