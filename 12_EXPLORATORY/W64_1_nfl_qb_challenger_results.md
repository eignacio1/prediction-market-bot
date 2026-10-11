# W64.1 — NFL deep challenger: QB-shrunk performance (EXPLORATORY)

Status: PART A + PART B DONE. Label: EXPLORATORY. No sizing change.

## Part A
- Step 0 (read-only): VPS checkout (e3353ad4, ancestor of main) now has `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md` and `NFL_TRANSLATION_MAP.md`. 63.3's UNAVAILABLE was a deploy-timing artifact; no gap registered.
- Plan frozen BEFORE fitting: `12_EXPLORATORY/20261009_nfl_qb_challenger/README.md` (M1 QB-shrunk EPA k=6, M2 EB-shrunk team rates K=2, M3 excluded: injury `date_modified` not in cache; m=8, alpha=0.00625, seed 20261009, B=2000).
- Features: `qb_features.py`; tests: `test_qb_features.py` (6 pass; K=0 reproduces the frozen builder on 2723 rows, 0 mismatches; poisoned-future and same-day rows never leak).
- Isolation tests + new tests: 24 passed.

## Part B — result (EXPLORATORY, scoped to this feature set and 2019-2025)
Rolling origin 2019-2025 (n=1852); frozen arm reproduces W61.3's 2025 Brier: 0.2185 (check passed).

| Arm | Brier | vs frozen (mean, 99.375% CI) | seasons better |
|---|---|---|---|
| frozen | 0.2260 | - | - |
| **full** (challenger) | 0.2233 | -0.0027 [-0.0050, -0.0006] | 6/7 |
| qb_only | 0.2233 | -0.0027 [-0.0050, -0.0005] | 6/7 |
| eb_only | 0.2260 | -0.00001 (CI spans 0) | 2/7 |
| full_oracle (flagged upper bound) | 0.2215 | -0.0045 | 6/7 |

- **Pre-registered rule met:** upper CI limit < 0 and 6/7 seasons better -> `full` beats the frozen model in backtest. The whole gain is mechanism 1 (QB); mechanism 2 (EB) does nothing (delta ~1e-5).
- **Caveats, stated plainly:** (1) 2025, the frozen model's held-out season, is the one season where the challenger is WORSE (+0.0038). (2) On the 182 2025 games with a Kalshi mid, Brier: mid 0.2115, frozen 0.2182, challenger 0.2221; challenger minus frozen +0.0039 (95% CI -0.0031..+0.0115); neither model beats the mid. (3) Gain is concentrated in weeks 1-4 and, via the oracle arm, in games where the starter changed; the QB-changed subset alone is not significant.
- **Effect size:** -0.0027 Brier vs frozen is a calibration improvement, not market edge. Judged live n ~984 games (~3.6 seasons).
- **Draft pre-registration:** `NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md` (Status PROPOSED, awaiting operator).
- **Next mechanism if this is rejected or fails live:** injury-report QB-only (mechanism 3), needing a point-in-time snapshot source.
- Added after the plan froze (descriptive only): `per_game_sd` per arm in results.json, used to size n.

## Live (W65.3, 2026-10-10)

**Shipped (PR #211, merged d0352246; follow-up PR #213):** frozen challenger `models/nfl_qb_challenger_v1.json` (13 features: the 11 frozen features with EB shrinkage K=2, plus `qb_epa_h`/`qb_epa_a`; ridge lambda=100; train 2015-2024, cal 2025; QB term = projected starter, i.e. the prior game's starter, flagged `qb_source="projected_prior_game_starter"`). Runner `scripts/run_nfl_qb_challenger_shadow.py` writes `exp_output/PREGAME_SHADOW_NFLQB/NFLQB_NFL_MONEYLINE_T1.jsonl`, a separate ledger tagged challenger, never touching frozen rows. New cron block `W65.3 NFLQB` (T1 at :14 of the 6-hourly hours, settle 09:44Z), installed on the VPS, mirrored in `deploy/cron_exp037_pregame_shadow.conf`. No existing cron line edited. No sizing, order or stake path touched.

**VPS dry run:** 26 challenger rows, 24 markets paired to frozen first rows (12 games); the one unpaired game was just entering the T1 window. Calibration engine (`PREREG`, `discover_cells`, `EXPECTED_CELLS`) and `silent_arms.SPECS` list the challenger; the cell shows at n=0 before its first row.

**Judgment rule (addendum):** the "~984 games" gate is withdrawn. Judged comparison is C2 (challenger vs Kalshi mid, EXP-037 rule, looks 60/150, ~2026-11-02). C1 (vs frozen) is descriptive only. Expect "keep accruing" or "no edge": on 2025's 182 priced games challenger 0.2221 vs frozen 0.2182 vs mid 0.2115.

**D1:** `distance_to_optimum.py` now reads `nfl_qb_challenger_v1: personnel, team` (the `qb_` keyword classifies as personnel). The frozen `nfl_pregame_v1` is still `team`. D3 stays 1.

**Step 6 — injury reports (QB-only), not built.** T-601 (`deploy/cron.drafts.conf`, still commented out and not authorized) runs `scripts/nfl_prekickoff_capture.py`, which snapshots nflverse schedule and team-stats extended fields (roof, surface, home/away QB id, coaches, plus referee/temp/wind) 80-120 min before each kickoff cluster, append-only and hash-idempotent. The captured `home_qb_id`/`away_qb_id` are the announced starters, not injury-report status, so it gives no questionable/doubtful/out designations and no practice-participation history. Missing: a point-in-time injury-report source (nflverse `injuries` table) captured on the same cadence. Smallest block: the T-601 cron lines uncommented under an operator authorization, plus one added `capture_injuries` call in `nfl_prekickoff_capture.py` filtered to `position == "QB"`, appended to the same store with the same hash idempotency.

## Injury snapshots (Block 67.1, 2026-10-11)
Cron `22,52 * * * *` is installed on the VPS (new line only). Real snapshot proven by a manual run at 16:38:21Z on 2026-10-11: 13 games, 228 rows (46 QB), `min_minutes_to_kickoff=21`, written to `exp_output/NFL/INJURY_SNAPSHOTS/snapshots.jsonl` (+`checks.jsonl`). The script writes only strictly pre-kickoff, so this is a pre-kickoff capture for Sunday's slate. The Thu 2026-10-15 game is not yet capturable; the cron will take it, and `minutes_to_kickoff` in the row is the proof to read then. The cron log file does not exist yet (first cron fire at :22/:52).

**What the ESPN feed lacks.** Each row carries only status (Out/Doubtful/Questionable), body part, a `status_updated` stamp and a return date. It has no practice participation (DNP/limited/full by day) and no game-day inactive list. Cheapest source for practice participation: the NFL's official weekly injury report (nfl.com injuries page, Wed-Fri), free to scrape. Cheapest source for inactives: the ~90-minute pre-kickoff inactives list, also free from ESPN's game summary endpoint or nfl.com. Nothing built.
