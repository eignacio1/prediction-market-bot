# Handoff W112.4 - NHL factor classes point-in-time, applied as router filters (B-012)

Status: PARTIAL | B-012: Parts A and C DONE (PR #489, squash 74d0527, CI green); Part B NOT DONE.

## Result
- NHL schedule/travel/venue (H6, H7, H8), shot quality (H1) and line deployment (H3) built point-in-time (`nhl_engine/factors_w112.py`), exported as `nhl_filters(home, away)` (`nhl_engine/filters.py`), scored per leaf held out (`12_EXPLORATORY/nhl_factors_w112/`, see RESULTS.md).
- 271 games, 44,979 settled shadow rows, 72 leaves; 1 BH survivor: deployment@side moneyline away_edge -> MOMENTUM, held-out +0.133 [+0.085, +0.179], 15 games (a lead for replication, not a verdict). Puck line: no positive-interval leaf; routed to ride / no bet in these leaves.
- Stages: SEATS/nhl.toml applied 3 -> 8 of 12. Still none: H9 officials, H10 coaches/scratches, H11 injuries, H12 qualitative/PAM.

## Part B (not done)
- Muse's goalie/referee snapshots live in his archive commit 8812c8d, which is not in this repo or its object store (`git cat-file` fails). They could not be recomputed or graded: they stay REPORTED. Needs read-only access to that archive.
- Goalie confirmation timing vs Kalshi price moves not measured. Known: store has the starter only post-game (GG-1010, W52.D "cannot tell"); `.github/workflows/nhl_goalie_probe.yml` is the existing probe.
- Officials/coaches/scratches: free right-rail endpoint, no assignment timestamp, so not strictly pre-tip (GG-1012). Injuries: no free history (GG-1013). Qualitative/PAM: GG-1014. No paid-only item bought; existing GGs cover them, none new registered.

## Interface for 112.1
`nhl_filters(home, away)`; per-team dict keys: rest_days, back_to_back, games_last_7d, travel_km, tz_shift_h, neutral_site, hd_for, hd_against, top_share (last three as league percentiles at puck drop). Labels: rest/travel/density/venue/shot_quality/deployment at side or total; "unknown" when a fact is missing. The router does not call it yet.

## Fields
- pattern_sweep: n/a (no defect fixed)
- surface_delta: +2 modules, +1 test file, +1 exploratory script; no live component, no cron, no box task (no install needed)
- vision_pillar: DEPTH (D5(b) NHL, D1 NHL, D6 layer 3 filters exported)
- gap_measure / gap_delta: D5(b) NHL applied 3 -> 8 of 12 (source: SEATS/nhl.toml, PR #489)
- directive_conflicts: old scorers `score_vs_market.py` and `nhl_engine/run_w84_3.py` still report Brier vs market (D-04). H2 goalie quality is previous-game starter only (GG-1010). The router does not yet call the NHL filters (D-06).
- Not run: CLAUDE.md Steps 1-4 / Q1-Q7 in full (scoped engine task); cached scan: 1 stub (comment in quant/inplay_nhl.py:37), doctrine 0 RED.
- Operator decisions: none.
