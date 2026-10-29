<!-- session-meta
task_id: T-1460
tier: STANDARD
timestamp: 2026-10-29T01:30:00Z
commit: ec92612
one_line_summary: W94.2: EXP-045 NFL engine forward test frozen; temporal evolution built (8/8); N11 play callers interpreted, null on totals
gg_touched: GG-1460, GG-1461, GG-1462
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, DEPTH
gap_measure: P3 (EXP-045 look dated); D5(a) NFL; D5(b) N11
gap_delta: P3 NFL engine look 0->1 dated (2027-01-12, UNDERPOWERED, MDE ~0.032, EXP-045 sha256 d0df8a49 frozen 2026-10-29T00:23:54Z); D5(a) NFL 7/8->8/8 (temporal_evolution, 4 known-answer tests); D5(b) N11 none->interpreted (results_W94_2.md @ ec92612)
pattern_sweep: safe_out nested-path defect also in nfl_board_v2/heldout_keynumbers.py, kalshi_compare.py, n15_interpret.py (registered GG-1460, not fixed); fence-scan .rename/.replace false positive, no other instance in 12_EXPLORATORY/*.py today (GG-1461); "Deploy job" premise stale since W67.3 (GG-1462)
surface_delta: 0
-->

# SESSION_HANDOFF W94.2 (proof lane)

```
vision_pillar: PROOF, DEPTH
gap_measure: P3, D5(a), D5(b)
gap_delta: see session-meta
pattern_sweep: see session-meta
surface_delta: 0 (no running component added; EXP-045 scores from the archive, no runner)
stage per factor: temporal evolution = interpreted; N11 play callers = interpreted (not applied); NFL engine forward test = pre-registered, look 1 2027-01-12
```

## What landed (all merged, CI green)
- Part A #367 `f252ac8`: EXP-045 pre-registration + sha256, `nfl_engine/forward_test.py`, `score_exp045.py`. Judged n at MDE 0.02: 429/442/337 games (spread/total/team total); only 165 post-freeze 2026 games, so look 1 reads "NOT DISTINGUISHABLE at MDE ~0.032" on a non-pass; modal outcome ~85%. In-sample replay net P&L/contract: spread -0.003 [-0.039,+0.032], total +0.009 [-0.029,+0.045], team total -0.021 [-0.052,+0.008].
- Part B #369 `00b3c13`: `nfl_engine/temporal_evolution.py`, drift measure on 2016-2025 REG (320 team-seasons). Only neutral pass rate drifts team against team: reliability gap +0.157 [+0.071,+0.242]. League slope per week: off EPA/play -0.0011 [-0.0020,-0.0001]; neutral pass rate -0.0015 [-0.0022,-0.0007]. Other gaps span 0.
- Part C #371 `ec92612`: `c1_signal_ingestion/nfl_play_callers.py` (point-in-time, OC-of-record with HC fallback 6.8%). Held-out 2020-25 trait corr: pass_oe 0.381 [0.350,0.413], go4_oe 0.150, pace 0.451, lead_oe 0.299. Game total MSE gain vs line: baseline +0.14 [-0.93,+1.20], callers added -0.92 [-2.98,+1.04]; team totals baseline -0.10 [-0.31,+0.11], callers added -0.24 [-0.56,+0.09]. Rigorous null: real traits, no priced strike moved. Kalshi look (n=147) descriptive only, all correlations span 0. Caveat: OC of record is not a confirmed play caller.

## Premise corrected
The block said to read the post-merge Deploy job summary. `deploy.yml` is `workflow_dispatch` only since W67.3; the box deploys itself by cron behind the approval-path tests (5-20 min). Read-back is `logs/vps_deploy.log` on the box. At 01:20Z the box was mid-deploy `03e7163 -> ec92612` (started 01:08:18Z); read-back of the merged code on the box is therefore PENDING at handoff time, not confirmed. GG-1462.

## Session-start protocol (run late, after the work)
Step 1 none. Step 2 CLEAN. Step 3 OPEN count 230, headers=status=277, no duplicate ids. Q1 kelly_fraction 0.0 on the three zeroed bands (ADR-0048); MAX_DAILY_LOSS_PCT 0.15; max_drawdown_pct 0.20. Q4 interfaces unchanged. Q7 0 violations. Step 4: t4-mlb active, dashboard NRestarts=0, 0 oom-kills, 0 recent game_state_fresh, T4 cycle log last row 01:09:55Z.

## Q6 concern, unregistered here (no GG number claimed for it)
`SemanticFloorViolation` in the last 500 T1 MLB cron lines: "games_fetched=1 but matched_players=0". T1 also shows 0 bets placed on the last two runs with 11 players matched. Probably a postseason one-game day with no player markets, but not diagnosed. For the window.

## Observed, not fixed
GG-1460: three nfl_board_v2 scripts write to `12_EXPLORATORY/12_EXPLORATORY/…`; their committed JSONs may be stale. Main tree also holds the untracked nested dir.

## Strategic Decisions This Session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| None | Part C stays "interpreted"; null is the result, not a failure | results_W94_2.md | window |
