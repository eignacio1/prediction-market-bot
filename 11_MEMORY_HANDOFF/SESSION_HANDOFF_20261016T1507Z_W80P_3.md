# SESSION_HANDOFF — W80P.3 NBA pace/efficiency vs Kalshi NBA totals (STANDARD)

<!-- session-meta
task_id: W80P.3
tier: STANDARD
timestamp: 2026-10-16
one_line_summary: BLOCKED - needs KXNBATOTAL 2025-26 pre-game prices (Task 2's NBA sample, VPS raw store) and the NBA store; VPS unreachable and Kalshi API refused in this cloud session; factor stays at "interpreted"
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA applied 0 -> 1 (or a priced/invisible verdict)
gap_delta: none (0 -> 0) - BLOCKED before the join
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

**Status: BLOCKED** (same root as W80P.2). The join needs (a) KXNBATOTAL 2025-26 pre-game prices — only in the VPS raw store `exp_output/KALSHI_HISTORY/thin/raw_2026-10-16.jsonl` (W79.2 sampled 100 NBATOTAL markets) or from the Kalshi public API, and (b) the point-in-time pace/efficiency totals from the NBA store. This session: no ssh client (`timeout: failed to run command 'ssh'`), Kalshi `CONNECT tunnel failed, response 403`. No KXNBATOTAL price row exists in git.

Stage reached per factor (ADR-0075): **pace + efficiency — interpreted** (W79.3: team trait, moves game totals, MSE gain 11.2, CI 8.4-14.2; `02_ARCHITECTURE_DESIGN/NBA_ENGINE/FACTORS_FIRST_READ.md`); not applied. Rest — interpreted as schedule, not a trait (unchanged).
No verdict (REAL-NOT-PRICED / REAL-AND-PRICED / INVISIBLE / NOT REAL) issued; no pre-registration drafted; SEATS/nba.toml and the D5 line unchanged.
**Time pressure:** NBA opens 2026-10-20. Run from a box-access session, or allow `api.elections.kalshi.com` in this environment's network settings.
Operator decisions: none.
