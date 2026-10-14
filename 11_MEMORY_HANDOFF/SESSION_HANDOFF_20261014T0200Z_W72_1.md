<!-- session-meta
task_id: T-930
tier: STANDARD
timestamp: 2026-10-14T02:00:00Z
commit: 8b1fb3b
one_line_summary: W72.1: forward-test read-back done (cancels work, control arm placing, nothing settled); GG-646 fixed; order-path guards GG-665/666/667 merged, t4-mlb restart pending idle window.
gg_touched: GG-586, GG-570, GG-571, GG-623, GG-645, GG-646, GG-564, GG-665, GG-666, GG-667
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E1/E2/E3
gap_delta: E1 not readable (0 post-re-arm orders settled) -> first per-arm counts recorded; E2/E3 unchanged. Source: logs/demo_fill_policy.jsonl on VPS since 2026-10-13T23:58Z, read 2026-10-14T00:44Z.
-->

# SESSION HANDOFF W72.1 (2026-10-14)

Status: PARTIAL | branch session/20261014T004119Z-w72-1-readback-guards | PRs #246 (GG-646), #252 (Part B + docs) merged, CI green.

Read-back (since re-arm 23:58Z, 320 events): paper/MLB treatment 4 orders, 4 cancel_ok; shadow/MLB treatment 9 (8 ok, 1 already_terminal), control 13; shadow/NHL treatment 21 (20 ok, 1 already_terminal), control 23. Fills: 0 / 1 / 3 / 1 / 1; none settled. 0 cancel failures. `not_listed_on_demo` skips: paper/MLB 138, shadow/MLB 2, shadow/NHL 46. No turn-off tripped. NFL +0.40 rests on about 4 correlated games (GG-624), not E2.
Closed on this read-back: GG-586, 623, 645, 571, 646 (checkout carries the fix). GG-570 left OPEN (operator call on NBA); GG-564 OPEN (listing split recorded).
Part B: GG-666 host refusal on `_post`/`_delete` (live needs `LIVE_CAPITAL_ADR` set by an accepted ADR AND matching env; none exists). GG-665 kelly from `BAND_CONFIGS` via `_band_kelly_fraction`; an unresolved band falls back to the engine's constructor fraction, never the forecast dict. GG-667 shared `kill_switch_state.halt_reason` checked before shadow stake orders. Tests both ways; one existing risk test updated.
Deploy: VPS checkout contains 8b1fb3b. t4-mlb (started 23:58:11Z) still holds OLD code in memory: game live at 01:49Z, so NO restart. Restart decision: restart in the next idle window, then flip GG-665/666/667 to RESOLVED.
Caveat: GG-667 covers flag files and cell state, not C4's daily-loss/drawdown computation (C4 recomputes those per call; the shadow path has no bankroll feed).
Next undone: t4-mlb idle-window restart and read-back; settle data for E2/E3.
Operator decisions: should the skip-rate turn-off (>90% for three days) discount `not_listed_on_demo` skips? Recommend yes; it changes a pre-registered scope.
