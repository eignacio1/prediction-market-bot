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
