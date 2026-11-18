# SESSION HANDOFF - W104.1 (B-048) why fills lose: fill probability and price impact

<!-- session-meta
task_id: W104.1
tier: STANDARD
timestamp: 2026-11-06T02:15:00Z
commit: a147151
one_line_summary: W104.1 B-048 fills quant merged (PR #439, CI green); E3 gap not explained by observed covariates; fills carry -1.2c 1m markout, worse at high price
gg_touched: GG-1793, GG-1794 (registered, not fixed)
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E3 (win rate on fills vs non-fills); fill-model calibration
gap_delta: E3 gap explained -74% held-out (90% CI -365% to +191%; indistinguishable from 0; raw gap only -1.5pp, NFL/NBA/NHL demo population, not MLB); fill model ECE 0.021, AUC 0.62
pattern_sweep: exploratory runner wrote json without safe_out and used .replace() (isolation lint, tests/test_exploratory_isolation.py) -> fixed in run_w104_fills.py; swept 12_EXPLORATORY/quant_w104_fills only, other scripts not re-audited (W103.2 already recorded recompute.py:35)
surface_delta: 0
-->

Status: DONE. Operator decisions: none.
Merged: PR #439 (quant/fills.py, tests/test_quant_fills.py 7 pass, runner, RESULT.md, result.json). Branch deleted remotely; local worktree branch left in place.

## Result
Full write-up: 12_EXPLORATORY/quant_w104_fills/RESULT.md (operator paragraph at top).
- Population: NFL/NBA/NHL demo shadow orders, n=99,864, pre-epoch YES-side only; post-epoch n=0. NOT the MLB paper book behind the 25.4% vs 48.3% / 28.9% vs 52.1% headline figures; those were not reproduced and nothing here explains them.
- Fill model (held-out): AUC 0.62, ECE 0.021, Brier 0.1283 vs 0.1312 base; fill rate drifted 17.5% train to 15.5% test.
- Markout: 1m -1.23c (n=13,164), worse with price (-0.5c below 20c, -4.1c at 80c+).
- E3 decomposition: indistinguishable from zero.
Stage reached: aggregated + interpreted. NOT applied. Candidate rules in RESULT.md are not pre-registered.

## Defects registered (not fixed, Rule 11)
- GG-1793: forward cache holds side='yes' for all orders (GG-1770 pattern); non-fill side unrecoverable, so E3 non-fills are scored as YES contracts.
- GG-1794: no per-order log of intended side, pre-order mid, book depth or fill time; blocks a real information-vs-noise test (needed before any MLB or post-epoch rerun).
