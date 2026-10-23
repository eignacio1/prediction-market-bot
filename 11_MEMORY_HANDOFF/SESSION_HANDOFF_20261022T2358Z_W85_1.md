<!-- session-meta
task_id: W85.1
tier: STANDARD
timestamp: 2026-10-22T23:58:00Z
commit: 67697f3 (code, PR #326); pre-reg commit = this docs push (SHA in DECISION_LOG)
one_line_summary: W85.1: NFL market-anchored price built offline and pre-registered (EXP-041, not wired); pooled dBrier vs anchor +0.00002 [-0.00014,+0.00017]; 0 of 18,479 strikes clear the gate.
gg_touched: GG-1090
adr_touched: none (ADR-0072 amendment text is 85.2's)
plan_deliverable_moved: yes
vision_pillar: DEPTH, PROOF
gap_measure: D3 NFL challengers; D5(b) NFL factors priced from the line; P3
gap_delta: D3 NFL 1 -> 2 (source: EXP-041 pre-reg); D5(b) NFL 0 -> 2 built (F8; F5/F6), neither with a measurable gain (source: results_W85.md); P3: EXP-041 scored look at >=500 games, ~Jan 2028, modal NOT DISTINGUISHABLE ~85%
pattern_sweep: n/a (one lint false-positive fixed in anchor_gap.py; the other 12_EXPLORATORY files were already clean under tests/test_exploratory_isolation.py, 65 passed)
surface_delta: none (no runner, cron line or registry cell)
-->

# SESSION HANDOFF — W85.1

**Strategic decisions:** EXP-041 pre-registered and frozen, NOT wired (operator: "sit on it for now").
**Result:** held-out 2022-25 (n=1,087) pooled dBrier price−anchor +0.00002 [−0.00014, +0.00017]; 0 of 18,479 strikes clear the gate. Frozen w: ML 1.0, SPREAD 0.4, TOTAL 0.0, TEAMTOTAL 0.2.
**Anchor timing:** T1 mid-to-close gap SD 0.026, larger than the adjustment; ML 2025 only (GG-1090).
**Stage:** F8 applied, no measurable gain; F5/F6 interpreted.
**Pre-reg:** 05_RESEARCH_EXPERIMENTS/EXP041_NFL_MARKET_ANCHORED_PREREGISTRATION_2026-10-22.md; judged n ≈ 500 games.
**CI:** PR #326 merged after one lint fix; deploy run cancelled by newer push, change under 12_EXPLORATORY only.
**Pending:** recommend not wiring EXP-041; next DEPTH factor with larger unpriced share than F8.
**Resume:** wire only if the operator says so.
