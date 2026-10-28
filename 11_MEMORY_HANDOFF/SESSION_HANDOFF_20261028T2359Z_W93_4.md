<!-- session-meta
task_id: T-1400
tier: STANDARD
timestamp: 2026-10-28T23:59:00Z
commit: f88d455
one_line_summary: W93.4 NFL board v2 priced from the line with key numbers right, N15 interpreted; no edge vs Kalshi
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4, D5(b)
gap_delta: D4 NFL scaffold -> board priced, market-anchored, tested; D5(b) NFL N15 none->interpreted (results_W93_4.md, nfl.toml N15 @ f88d455)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

# SESSION HANDOFF — W93.4 NFL engine: the board from the line, then N15

Status: DONE | main @ f88d455 | PR #365 (CI green, merged) | Margin-3 mass within noise held-out; engine matches Kalshi's ladders, no edge | MEASURE MOVED: key-number 3 z vs held-out: Gaussian +23.8 -> engine -0.7 (heldout_keynumbers.json); D4 NFL -> board priced/market-anchored/tested; D5(b) N15 none -> interpreted (results_W93_4.md) | stage: board v2 applied (tested price path, no edge); N15 interpreted | operator decisions: none

vision_pillar: DEPTH
gap_measure: D4, D5(b)
gap_delta: see above
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no running component, runner, arm, order or registry cell)

## Results
- `12_EXPLORATORY/nfl_board_v2/results_W93_4.md`: method, held-out key-number table, Kalshi comparison (86 settled 2026 games, all intervals include 0), N15 study.
- Kalshi strike convention is "yes = value > N" (verified by Brier).

## Hand-back
- Limitations: k=1,2 under-modelled; bandwidths untuned; city-level miles; relocated teams use today's base; one in-progress season of Kalshi prices. Re-run `kalshi_compare.py` as the season settles.
- Fence: CI first failed on three exploratory scripts writing with open() instead of safe_out(); fixed in the same PR (pattern sweep of 12_EXPLORATORY/nfl_board_v2 done, no other instance).
- Merge run 40790384029 was Test Suite only (green); no Deploy job appeared. t4-mlb: no restart, no service-imported file changed.
- Claim T-1400..T-1402 / GG-1400..GG-1402: none used; not formally closed.
