# Session handoff - W112.2 (B-082) - sizing rule per arm; a losing look closes a hypothesis, not an arm

vision_pillar: DEPTH (D6 layer 6) + PROOF wording (P2)
gap_measure: D6 layer 6 cells; directive D-03
gap_delta: layer 6 code BUILT (arm_sizing.size_for); layer-6 cell count 0 -> N is counted by 112.1's coverage.py once the wiring step below lands (no routed row carries a size_for decision until then, so today's evidence count is still 0). D-03 PARTIAL -> BUILT in code (closed hypotheses recorded: 2, NFL game total T1 and T2). OPERATOR_DIRECTIVES.md not edited (not in this block's file list): window flips the D-03 row.
pattern_sweep: grep `closed_arm|ClosedArm|arm_is_closed|FADE ARM CLOSED|fade arm closed` over src/ scripts/ tests/ dashboards/ .claude/. Fixed: market_type_registry.py, calibration_engine.py, proof_calendar.py, distance_to_optimum.py + 5 tests. Left (not owned): see directive_conflicts.
surface_delta: 0 running components (a pure module + a read-only script; no cron, service or workflow; nothing for RUNTIME_REGISTRY)
directive_conflicts: scripts/claude_md_now.py:36 and :42 still print "fade arm closed (routed...)" for the RULED_OUT status label, and scripts/web_dashboard.py:2240 still has the legend text 'fade arm closed (routed)'. No registry cell is RULED_OUT any more, so neither fires on today's data, but the words contradict D-03. Neither file is in 112.2's list: window to reword to "hypothesis closed (EXP-id, parked for R&D)" (tests/test_doctrine_label_words.py guards the dashboard words).

## What was built (and which arm each leaf goes to: unchanged; this block routes nothing)
- Part A. `ClosedHypothesis` (exp_id, model, comparison, look, frozen_label, measured_date, citing_decision, revisit="R&D (operator call)") and `MarketTypeCell.closed_hypotheses`. NFL game total T1 and T2 migrated: `closed_arms=()`, one `ClosedHypothesis` EXP-037 each (delta -0.0161 / -0.0157, n=60). Every arm stays open (`arm_is_closed` is False for all six). `ClosedArm` and `closed_arms` kept only so old imports work. `calibration_engine.routing_for` reports `closed_arms: []`, `closed_hypotheses: [EXP-id]`, reading "hypothesis closed (EXP-037, parked for R&D)"; the frozen label (`verdict` == `verdict_preregistered`, RULED_OUT) is unchanged and tested. `proof_calendar.py` rows read HYPOTHESIS CLOSED; `distance_to_optimum.py` P2 reads "N closed hypotheses, 0 closed arms, M closed cells".
- Part B. `c4_risk_engine/arm_sizing.py`: `size_for(arm, cell, context) -> SizeDecision(stake_usd, reason, binding_caps, kelly_shaped_usd, ...)`. Live rule: Kelly 0 (reads the band's `kelly_fraction`), placed stake = flat demo stake (default $1.00, ADR-0059), cut by per-event, per-day and per-arm-budget caps and by a same-game cluster cap using 110.4's `quant/sgp.phi` (open legs with phi >= 0.90 merge into one exposure: two perfectly correlated legs total one leg's stake). The Kelly-shaped stake ((p-c)/(1-c) x 0.25 x $1000) is returned and logged, `kelly_placed` is always False. Cap defaults ($5 event, $50 day, $25 per-arm per-day) are DEMO-scale placeholders chosen in this block, not derived numbers: the operator/window should confirm or replace them before they bind real orders. 15 known-answer tests (`tests/test_arm_sizing.py`).
- Part C. `scripts/arm_sizing_replay.py` (+ test): replays the last N days of routed shadow rows through `size_for` ledger-ordered, stake and Kelly-shaped per arm, caps that bound, pre-epoch YES-only vs post-epoch all-sides kept apart.

## NOT done - read this
- The 14-day replay was NOT run on real rows. Shadow rows (`exp_output/PREGAME_SHADOW`) live on the box only; this window has no copy and `box_tasks.py` is not in this block's file list. To run it: add an allowlist entry `arm_sizing_replay_read` = `{PY} scripts/arm_sizing_replay.py --days 14` (read-only), request it, and file the result. The script is tested on synthetic rows only. The same-game cluster cap is not exercised by shadow rows (no shared draws); it is covered by tests only.
- The claim in SESSION_CLAIMS carries ID range "T-TBD GG-reserve" (the rules ask for real numbers). No GG was opened by this block.

## Layer-6 evidence rule for coverage.py (112.1)
A cell has layer 6 when at least one of its arm's routed rows (shadow or order) carries `size_for` (`SizeDecision.as_row_fields()`): `{arm, stake_usd, reason, basis, binding_caps, kelly_fraction_live, kelly_shaped_usd, kelly_placed: false, correlated_exposure_usd, merged_legs}`. Count per (cell, arm); a row with `kelly_placed: true` is a violation, not evidence.

## Wiring step for the window (next wave)
112.3's `size_for(arm, cell, context)` hook (default: today's flat stake and caps) -> `prediction_market_bot.c4_risk_engine.arm_sizing.size_for`, passing `SizingContext(price, p_win, open_event_usd, open_day_usd, open_arm_usd, new_leg_draws, same_game_open)`. Then write `decision.as_row_fields()` onto each routed row. Same signature; no order-path file was touched here.

## Operator decisions
None. Kelly stays 0 (his call, at G6). Confirming the demo cap defaults above is a window call before wiring.
