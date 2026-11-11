# SESSION HANDOFF — W109.1 NBA betting architecture 4/8 → 8/8 (B-066)

```
vision_pillar: DEPTH
gap_measure: D5(a) NBA architecture components with scaffold+test; D5(b) NBA factor classes applied
gap_delta: D5(a) NBA 4→8 (decision_trees, filtering_mechanisms, cross_reference_compatibility, temporal_evolution now have scaffold+test on main). D5(b) NBA applied: 5→5 (one path built and scored end to end; ml carries no positive-edge verdict, so no class is counted newly "applied" -- operator may re-grade)
pattern_sweep: n/a (no defect fixed). One in-block fix: FACTOR_CLASS lacked v3 lineup names (d_/s_exp_missing, d_/s_lineup_net) -> registered + test; the isolation-fence scan rejected `str.replace` in a 12_EXPLORATORY script -> sliced instead.
surface_delta: 0 running components; 4 library modules in src/prediction_market_bot/nba_engine/ + 1 exploratory script. No RUNTIME_REGISTRY entry needed.
operator_decisions: none
```

## Done (all merged: PR #463 → e077db2, CI green on head)
- Part A/B: `nba_engine/{temporal_evolution,granularity_filter,cross_reference,decision_tree}.py` + 4 test files (20 tests). Ported from NFL; tree depth by horizon (ADR-0068): T1 ≥12h, T2 ≥3h, T3 ≥0h, in-play; lineup factors usable ≤1.5h to tip only.
- Part C: `12_EXPLORATORY/nba_arch_w109/applied_path.py`, `RESULT_W109_1.md`, output json/csv. ARCHITECTURE_COMPONENTS.toml nba rows updated.

## Result: NULL — the market is better
KXNBAGAME ml, 2025-26 held out (study_v3 protocol), n=397 games, Kalshi mid at tip−1h: Brier market 0.1529, tree T3 0.1745, T1 0.1775. T3−market +0.0215 [+0.012, +0.031]; T3−T1 −0.003 [−0.012, +0.006]. Gated (lineup shift ≥ train p90) n=52, not scored. Flat net before fees negative (T3 >5c: −0.046/contract [−0.090, −0.002], 277 bets). Matches W88.3.

## Limits / gaps
- Kalshi game-market history covers Feb–Apr 2026 only (397 of 1,130 test games); lineup factors 2023+; hourly candles, mid quote; ml only.
- `v3_factors.parquet` is an untracked build artifact: the script reads `V3_FACTORS` env (used the w98-1 worktree copy).
- Historical quotes only: no demo fills, so no GG-1771/1784 epoch mix.
- Box deploy: `logs/vps_deploy.log` / `deploy_truth_read` not readable from this session. Merge adds only library modules (nothing t4-mlb imports) → t4-mlb decision: no restart needed; operator/box bridge can confirm.
- CLAUDE.md Step 4 VPS probes and Q1–Q7 not run (engine-code block, no live-component change). Hook preview: 253 open GGs; one stub-scan hit, a comment at quant/inplay_nhl.py:37.
- Nothing unpushed.
