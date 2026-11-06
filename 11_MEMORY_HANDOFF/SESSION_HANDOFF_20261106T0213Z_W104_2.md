# SESSION_HANDOFF 20261106T0213Z - W104.2 (B-049 market-anchored blend weight)

<!-- session-meta
task_id: W104.2
tier: STANDARD
timestamp: 2026-11-06T02:13:00Z
commit: 2e60e3f
one_line_summary: W104.2 B-049 blend weight: NBA w~0 on all 12 engine x family cells, 0 beat Kalshi; NFL/NHL/MLB open (sealed).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: P1/D5 engine x family cells with a fitted out-of-sample blend weight
gap_delta: 0 -> 12 of 12 NBA cells fitted, 0 with w>0 beating market (nba_blend_result.json, 2026-11-06)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->


```
vision_pillar: PROOF (descriptive instrument; D5 stage "interpreted")
gap_measure: P1/D5 - engine x family cells with a fitted out-of-sample blend weight w
gap_delta: 0 -> 12 of 12 NBA engine cells fitted (8 with >=15 games); cells where w>0 beats the market: 0 (source: 12_EXPLORATORY/quant_w104_blend/nba_blend_result.json, 2026-11-06). NFL/NHL/MLB sealed shadow cells: not attempted.
pattern_sweep: n/a (no defect fixed)
surface_delta: +0 live components (1 library module quant/blend.py, 1 exploratory script; nothing scheduled)
```

**Status:** Part A, B (NBA only), C done. **B-049 state:** NBA answered descriptively; NFL/NHL/MLB open.
**branch@SHA:** main@b78cc2b (PR #437 squash-merged, CI run 42148190193 green, read).
**Result:** NBA v1/v2/v3 are worth ~0% of a move off Kalshi's line on every family (best w 0.22, v2 team totals, CI 0-1,
negative OOS gain); 0 of 8 testable cells reject at Holm/BH. Intervals wide (~30 games). v3 has 9-11 games: too few.
**Not done / why:** NFL EXP-045, NHL engine and MLB arms: the logged shadow rows (`PREGAME_SHADOW/`, `data/shadow/nhl/`)
are sealed pre-registered cells with no outcome in-file; I did not join finals for them. Follow-up block.
**Findings for next window:** a market that is over-confident gives a skill-free model a small positive w by shrinkage
(documented in the blend.py docstring); read small w as "shrinkage or skill". Recommend future pre-registrations use w=0 as default arm.
**Stage per factor:** blend weight = interpreted (not applied to any price). Operator decisions: none.
Data epoch: forecasts only; no fills or P&L read.
