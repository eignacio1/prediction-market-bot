# W125.4 handoff — PARKED mid-Part C (session limit)
branch: session/20261124T011335Z-w125-4-lineup-cross-props (pushed). No PR yet. Nothing merged. No outcome has been read.

## Done
- Part A: EXP-047-C1 PREREG committed before any outcome read (437975c) — 12_EXPLORATORY/nba_props_role/PREREG.md
- Part B: 33770e5 — usage_redistribution.py (shared rule), factors_applied.py uses it (bit-identical, tested),
  nba_engine_props_c1_forecaster.py (own MODEL_SHA256), runner switch PM_PROPS_C1 / --c1 default OFF,
  RUNTIME_REGISTRY writes list +exp_output/PREGAME_SHADOW_EXP047_C1/ (HR14: no new cron/service), 6 known-answer tests.
- Premise gap to state in the report: no redistribution rule existed in the game path; this block defined it.

## Part C state
- 12_EXPLORATORY/nba_props_role/run_retro.py written, imports OK, NOT yet run successfully/validated.
- Run with: PYTHONPATH=../../src:.. python3 run_retro.py <NBA_EVENTS root> .   (from nba_props_role dir)
- Data: NBA_EVENTS is not in this worktree. Use ../20261124T002142Z-w124-5-pam3/exp_output/NBA_EVENTS (has player_box, schedule, team_box?).
  It has NO raw/espn_schedule dir — load() calls W.rd(root,"espn_schedule") and tip_table needs it; find where espn_schedule lives
  (other worktree, e.g. PM-worktrees/20261016T054636Z-w78-4-nba-data-layer) or point root there. Injury json is tracked in-repo (12_EXPLORATORY/20261012_nba_points_minutes/inj).
- Unvalidated assumptions in run_retro.py: P.strike_probs name/signature, fc0.roster(team,date) return shape (_,name,mu-dict),
  fc._game_draws, P.TeamRoster signature, A.ET, norm_name import path, P.STATS. Check each against props.py / the forecaster; sanity-check pricing vs fc.forecast on the synthetic store.
- Note: `timeout` is not on this macOS; do not use it.

## Remaining
1. Fix/run run_retro.py -> RESULT.md + RESULT.json (verdict by PREREG rule, by stat, by V bucket; closed-hypothesis wording if it loses, never "no edge"). Don't commit rows.csv.gz if large.
2. HYPOTHESIS_DOCTRINE Part II.4 registry row; SEATS/nba.toml NBA-10 props-consumer note.
3. ACTIVE_QUEUE.md dated proposal line for PM_PROPS_C1 activation (operator decision).
4. PR (body ends with Claude Code line), CI green on current head, merge, read box deploy.
5. Final handoff (≤60 lines): pattern_sweep (usage_missing/creator_out consumers), surface_delta, directive_conflicts, measure moved (D1; D5(b) NBA-10 consumers).
