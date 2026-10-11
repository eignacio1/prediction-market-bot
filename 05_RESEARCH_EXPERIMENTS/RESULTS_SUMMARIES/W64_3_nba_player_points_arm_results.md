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
