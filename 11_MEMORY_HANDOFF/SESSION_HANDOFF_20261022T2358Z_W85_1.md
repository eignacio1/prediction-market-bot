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

**Result:** market-anchored price built offline; held-out (2022-25, n=1,087 games) pooled paired dBrier price−anchor +0.00002 [−0.00014, +0.00017]; at the all-seasons w=1 view +0.00010 [−0.00023, +0.00042]. 0 of 1,087 ML, 5,435 spread, 5,435 total, 6,522 team-total strikes clear fee + measured error. Frozen w: ML 1.0, SPREAD 0.4, TOTAL 0.0, TEAMTOTAL 0.2.
**Anchor timing:** T1 mid is 1.5-2.6 points from the close (SD 0.026), larger than the whole adjustment; moneyline 2025 only (GG-1090).
**Stage per factor:** F8 (N10) applied against the market, no measurable unpriced gain. F5/F6 (N7, N8) interpreted; applied-from-line shows no signal (share priced unidentified).
**Pre-registration:** 05_RESEARCH_EXPERIMENTS/EXP041_NFL_MARKET_ANCHORED_PREREGISTRATION_2026-10-22.md, frozen at the docs commit; code sha256 11fa9cf4…6aab, params sha256 070cd8e4…515e. Pooled judged n ≈ 500 games.
**CI:** PR #326 failed once on the exploratory write-fence lint (a `.replace()` call, no behaviour change); fixed, re-run green, merged. Deploy: my merge run was cancelled by a newer main push (#327's); no t4-mlb decision from my run; the change is under 12_EXPLORATORY/ only.
**Operator line:** recommend NOT wiring EXP-041 next wave; the cheapest EDGE move is a factor with a larger unpriced share than F8 (W77.2 MDE ~0.0014-0.0017 vs F8's ~0.0007).
**Not done / not in scope:** no runner, cron or registry cell; the ADR-0072 gate amendment is 85.2's.
**Resume:** wire only if the operator says so; otherwise next DEPTH factor.
