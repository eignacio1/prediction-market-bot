# SESSION HANDOFF - W97.4 (NHL engine, B-012) - COMPLETE

Status: DONE | ticket B-012: engine scaffold built and scored (EXP-046 not earned; ticket stays open for the forward test, state change is the strategic window's) | branch session/20261030T184514Z-w97-4-nhl-engine | PRs #390, #394 merged (#394 squash 90889dd), CI green
vision_pillar: DEPTH (+PROOF)
gap_measure: D4 NHL; D5(b) NHL factor classes; engine held-out Brier vs results and vs Kalshi
gap_delta: D4 NHL data layer -> whole board priced from one engine (scaffold, tested; src nhl_engine/model.py, tests/test_nhl_engine_*.py, 154 passed). D5(b) NHL: 0 -> 3 factor classes applied (5v5 xG matchup cross, special teams, rest), 1 interpreted (goalie). Held-out Brier beats climatology on ML and team totals every season 2023-25, totals at climatology (results_W97_4.md). Vs Kalshi (n=33 games, 726 rows): engine .1849 vs market .1792, paired adv -0.0057, 95% CI [-0.0126, +0.0013], skill weight 0.0.
pattern_sweep: defect fixed = flat first-season league baseline (league_rate_prior 2.20 vs ~2.7 real). Swept src/, scripts/, 12_EXPLORATORY/ for fixed league baselines: only `c2_feature_store/nhl_features.py:23-24` (LEAGUE_GF=3.05, LEAGUE_SVP=0.905) - the NHL shadow arm's prior, out of scope this wave (not edited), commented as re-fit from training data. No hits in NFL/NBA engines or MLB. Also fixed in-wave: three exploratory scripts wrote outside safe_out() (fence test); no other exploratory dir with the same pattern failed CI.
surface_delta: 0 (no running component installed)

## Result
One fitted model gives two regulation-goal rates per game; one simulated joint score prices every family coherently. Poisson chosen over NB (dispersion infinite; regulation score correlation negative, -0.08 to -0.12). Tie inflation implemented, barely moves totals level; totals under-predicted ~2-4 pts (late/empty-net scoring not modeled) - a registered limitation. Stages: 5v5, special teams, rest applied; goalie interpreted (unstable coefficients; probable starter not in store pre-drop, GG-1010); venue, officials, scratches, injuries, qualitative not built.

## EXP-046: not earned
Engine trails the market on all four families at 33 games, none significant; no held-out market prices for 2023-25 exist locally. Re-open at >= ~200 finished games with archive quotes (per-game sd 0.020 measured). No runner installed; nothing for next wave to install.

## Deploy / t4-mlb
Merge 90889dd. At last read the box was mid-deploy (5ec8ff5f -> 3843413c, started 00:58Z; previous deploy logged "t4-mlb restart decision: not_needed"). Nothing running imports nhl_engine (grep), so no restart is expected; confirm the final log line for the 90889dd deploy.

## Not done
- Real-data point-in-time truncation test (synthetic leakage tests only); calibration bins and clustered intervals for held-out table.
- 131 empty-shift fetch failures remain in exp_output/NHL_EVENTS.
- Muse cards R-047/R-067/R-080 not found in repo.

## Operator decisions
None.
