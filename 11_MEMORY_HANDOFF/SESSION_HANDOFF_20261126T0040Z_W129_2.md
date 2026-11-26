# Session handoff — W129.2 (EXP-047-S, the shrunk-mean props challenger) — 2026-11-26T00:40Z

**Deliverable:** pre-register, build, judge once, and log forward the PAM-3-licensed challenger against C2. **Branch:** `w129-2-props-shrunk`.

## What happened
- **Part A:** `12_EXPLORATORY/nba_props_shrunk/PREREG.md` pushed at `8d6b97e6223cac434ad150d8897c52d56821609e` before any judged row was read.
- **Part B:** judged once on NBA 2025-26 (1,131 usable games, 315,191 rows; 43 games had no usable report). **SUPPORTED.** Pooled D = +0.00172
  log-loss, 90% [+0.00140, +0.00204]; 4 of 4 stats positive and BH-passing (points +0.00149, rebounds +0.00090, assists +0.00115, threes
  +0.00372). Gain +0.0088 at 4-10 prior games, ~0 at 31+. Holds with and without an Out player (+0.00147 / +0.00209). Nearly all of it is the
  rate shrinkage (rate-only +0.00166, minutes-only +0.00019). MDE 0.00053, so the effect is about 3.2× the MDE. `RESULT.md`, `results.json`.
- **Modal outcome (P3):** stated SUPPORTED, +0.0010 to +0.0020, 4-10 concentration, threes largest: all matched. "Assists second" did not (points was).
- **Disclosure carried:** 2025-26 is unread by C2 and PAM-3 but not fresh to the program (PREREG §2). The 2026-27 forward rows are the real out-of-sample check.
- **Part C:** `NBAEnginePropsShrunk` (MODEL_ID `nba_engine_v2_props_shrunk_w129_2`) logs beside C2 via `PM_PROPS_SHRUNK` (default on, `off` disables)
  to `exp_output/PREGAME_SHADOW_EXP047_S/`. Reads a frozen 2025-26 per-player table, `data/reference/nba_prev_season_2025_26.json` (582 players,
  1,230 games, data through 2026-07-31). No orders, Kelly 0. C2 and v1 take no shrunk input (signature test).
- Docs: H-DEPTH-PAM-3 row now points to its use; new EXP-047-S row in `HYPOTHESIS_DOCTRINE.md`; queue row updated.

## Known flaws (not hidden)
- `players_without_prev` in `results.json` is never incremented, so the share of rookies/new players in the judged rows is unreported.
- Threes use C2's raw 3PA weights, not shrunk. Scores are log-loss against outcomes, not net after costs: nothing here is "applied".
- `run_shrunk.py` read the PREREG SHA via `subprocess` at run time; the isolation test forbids that, so it is now the constant
  `PREREG_SHA` (same value as `results.json`). Outputs unchanged.

## Measures moved
`vision_pillar:` DEPTH D3 (NBA props +1 pre-registered challenger ready), PROOF P2 (+1 verdict), D5(b) NBA PAM class 3 interpreted → logged challenger (not applied).
`gap_measure:` none. `gap_delta:` 0.
`pattern_sweep:` ledger-dir references swept (`scripts/ src/ deploy/ tests/ .claude/`): `props_c2_read.py` reads C2 only; registry `writes` list lacked C2 and now lists C2 and S.
`surface_delta:` 0 components. The existing cron `nba_engine_props_shadow.py` gains one logged ledger, `exp_output/PREGAME_SHADOW_EXP047_S/`, added to its `writes`.
Registry check: 111 entries, 0 unreviewed. Health signals not made worse by this block (shadow only, no new job).
`directive_conflicts:` none found in OPERATOR_DIRECTIVES.md.

## operator decisions:
- The cron `scripts/run_nba_engine_props_shadow.py` is still **paused** pending your approval of `nba_engine_props_shadow_install`. Until then neither C2 nor
  the shrunk arm logs on the box. No new install line is added by this block.

## Next
Router scoring of the S arm per leaf on net after costs, once forward rows exist; a 2026-27 forward read needs a new n from `mde_paired`.
Refresh the frozen prev-season table each autumn from the event store.
