# W64.3 — NBA player-points pre-game arm: results (updated per part)

## Part A (2026-10-09) — DONE
- **Survey (read-only GETs, `KXNBAPTS`):** 3 finalized events; two players per game, strikes 10/15/20/25; markets listed ~6.3h (two events) and ~14h (one) before tip. T1 (>=12h) will be thin; T2 is the natural band.
- **Model decision:** legacy model cannot be fit unchanged. Target is `pts >= own l10 mean`, not P(pts >= k); held-out AUC 0.577 / Brier 0.2476; qualitative snapshot stale; GG-037 legacy book Δ-Brier −0.044 (SD 0.153, n=114). Legacy artifact sha256 `2d9a869b…0b60a` (local-only). Decision: new frozen artifact (negative-binomial points distribution + Platt), trained once in Part B.
- **Pre-registration:** EXP-039 on main (PR #204, e08c226), before any row/model/cron. First look n=300/cell (MDE≈0.025), second look n=800 or 2027-01-31.
- **D1 manifest:** `nba_player_points_v1` entry added (personnel/team/venue); meta file absent until Part B, so the generator reports UNAVAILABLE, not a count.
- **Measure moved:** none (no cells flipped).

## Part B (2026-10-11) — IN PROGRESS
### Part A of 65.1: artifact + capacity
- Frozen artifact trained once; record in `EXP039_ADDENDUM_FROZEN_ARTIFACT_2026-10-11.md` (file sha `20d7d16a…2438`, 10 features, 0 qualitative; held-out Brier 0.1108-class vs climatology, see addendum).
- **VPS capacity (961 MB, 1 CPU, swap 2 GB):** at sample time 489 used / 472 available = 49% headroom (earlier sample 602 / 359 = 37%). Both above the 25% line, so no resize authorization. Heavy-window and dry-run peak RSS recorded below when measured.

### Remaining Part B plan
Train/freeze artifact + sha addendum, player-game store (ESPN box scores; stats.nba.com is 403 from VPS), forecaster/runner with separate preseason ledger, new staggered cron lines mirrored in `deploy/`, registry flip, calibration/silent-arm/dashboards, tests, VPS RAM check, deploy proof, generator B1/B4.

## Block 67.1 — landed and proven (2026-10-11)
- **Landed:** PR #223 (merge `45d4896`); branch baseline and main baseline both 0 failures in the same environment (the 66.3 "11 failures" were environmental). #217 closed as superseded. Deploy job green; t4-mlb restarted (no MLB game live), active 16:35:05Z.
- **VPS proof:** registry 107 cells, `NBA_NBA_PLAYER_POINTS_T1/T2/T3` = SHADOW (T4 DARK). Crons installed as additions only (backup `/root/crontab.pre_w67_1.bak`): box backfill `4 10`, T1 `21 4,10,16,22`, T2 `27 *`, T3 `14,24,44,54 *`, settle `35 10`, preseason smoke `37 *` (remove after opening night 2026-10-20).
- **Calibration engine:** lists all three cells, SEALED 0 of 300 ("no published schedule available for this sport").
- **Scoreboard (`distance_to_optimum.py`, VPS):** B1 `40 / 107` (was 37 / 104); B4 `2 · 0` (props families logging 1 -> 2).
- **Silent-arm check: NOT covered at first.** `silent_arms.py` had no points arm; its rows share the `NBA_*.jsonl` glob with the game-market arm, so a dead points arm would have been masked. Fixed in a follow-up PR (own arm `nba_player_points_shadow`, glob `NBA_NBA_PLAYER_POINTS_*.jsonl`, 12 silent-arm tests pass). Also fixed a stale Visual Dashboard note ("T1-T3 arrive with 65.1").
- **Honest gap:** the preseason dry run wrote **no rows** because Kalshi has 0 open KXNBAPTS markets; preseason-ledger isolation is proven by code/tests only, not by a row on disk. First row-level proof arrives when KXNBAPTS markets list.
- **Live Terminal dashboard:** not proven to list the arm (it has no registry/arm view for it); not verified, handed back.

## 10-20 rehearsal (W71.2, 2026-10-13, read on the box, `--dry-run` = throwaway ledger, no judged writes)

| Path | Command (VPS, `venv/bin/python`) | What it does on 10-20 |
|---|---|---|
| EXP-038 game runner | `run_nba_pregame_shadow.py --bands T1/T2/T3 --dry-run --now 2026-10-20T..` | Writes NBA_MONEYLINE rows only (T2 at 15:00Z wrote 2, T3 at 22:30Z wrote 2). NBA_SPREAD / NBA_GAME_TOTAL: 0 rows. NBA_TEAM_TOTAL: 0 markets listed. |
| EXP-039 + EXP-040 points runner | `run_nba_player_points_shadow.py --dry-run --now 2026-10-20T15:00Z / 23:20Z` | Runs clean, writes nothing: `KXNBAPTS` has 0 listed markets today (also KXNBAREB / KXNBAAST). |
| `nba_cell_autoflip` | `--ledger-dir <tmp> --out <tmp> --today 2026-10-21` | `0 new promotion(s)` (empty tmp ledger; flips only on the first valid regular-season row). |
| preseason retire | `remove_nba_preseason_cron.py --auto --crontab-file <copy>` | `--now 10-20T12:00Z`: no-op. `--now 10-21T11:00Z`: removes 3 blocks (backup written). Live crontab untouched (still 6 preseason lines). |

**Diagnosis of the spread/total `no_kickoff` skips: not a code bug.** Kalshi lists KXNBASPREAD / KXNBATOTAL only for the 5 same-day *preseason* games (10-13); the regular-season schedule index (`season_type=2`) correctly has no kickoff for them. KXNBAGAME already lists 10-20 (3 games resolve a kickoff). Spread, total and points markets are expected to list close to game day.

**Risk carried to opening night (cannot be fixed in code):** if Kalshi lists 10-20 spread/total/points markets late, they enter via the T2/T3 windows only (T1 is 12-48h). The T1 hourly-ish cron (`11 */6`) will not see them. Cells flip on the first valid row regardless of band; first look is the 10-20 evening scan (`silent_arms`).
