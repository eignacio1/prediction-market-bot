# Session handoff — W130.1 NFL in-play shadow (Part A)
**Rules read:** origin/main COMMON_RULES_W130.md, first line `# Wave 130 common rules`.
**Spec correction:** the spec's prereg path `12_EXPLORATORY/nfl_inplay/` is wrong; the real one is `05_RESEARCH_EXPERIMENTS/EXP048_NFL_INPLAY_ARITH_PREREGISTRATION_2026-11-25.md` (sha256-pinned, untouched; addendum added beside it).

## Built (Part A, shadow only, no orders, Kelly 0)
- `scripts/run_nfl_inplay_shadow.py`: behind `PM_NFL_INPLAY` (off and fetch-free by default); prices ML / spread / total / team total for every live game, both bands; writes `data/shadow/nfl_inplay/<market_type>_<band>.jsonl` + `pass_log.jsonl`; `--health`.
- `scripts/nfl_inplay_install.py`, `deploy/cron.nfl_inplay` (`*/2 17-23,0-6`), RUNTIME_REGISTRY entry (paused), box tasks `nfl_inplay_install / _readback / _uninstall` (writers set in test_box_tasks).
- Healthcheck item 14: no rows within 600 s while an NFL game is live = FAIL (GG-163).
- 8 T4NFL cells NOT_IMPLEMENTED -> SHADOW (EXP-NFLINPLAY-001); seat toml + NFL_SEAT.md re-rendered; CLAUDE.md Right-now regenerated (71 shadow).
- Addendum: frozen s2 (3.2717 / 3.2161, v2, 93 games wk 1-6, never committed before), FLOW = identity, team total = UNVALIDATED extension, pregame-line caching, judged-n rule.
- Doctrine row H-INPLAY-NFL-1 (COLLECTING).
- Tests: `test_nfl_inplay_shadow.py` (12), `test_nfl_shadow_safety.py` (3); precheck 107 passed; governance-adjacent 274 passed.

## Measures
B1 +8 cells (NFL 12 -> 20 shadow; registry 63 -> 71). B3 T4NFL 0 -> 1 band-family logging once the install runs (rows only exist after approval). Feed lag: first live number is Part B.

## Surface budget (Hard Rule 14)
surface_delta: +1 cron (paused until approved), +1 healthcheck item, 0 services. Install gate runs at install time; registry/runtime tests pass.
pattern_sweep: swept src/ scripts/ tests/ deploy/ for NHL in-play analogues (installer, cron, registry, healthcheck, box_tasks, safety test); all mirrored for NFL.

## Honest caveats
- Team-total prices have no replay; rows flagged `team_total_ext_unvalidated`.
- A game first seen in play has `line_pre_kickoff: false` and is excluded from judging.

## operator decisions:
> APPROVE nfl_inplay_install (run box task `nfl_inplay_install` by name). Must be approved before the first Thanksgiving kickoff, CHI @ DET 2026-11-26 18:00Z (1 pm ET); the cron starts 17:00Z and caches pregame lines in the hour before kickoff.

## Next
Part B (window, after approval): readback during first live game; rows/cell/min, staleness halts, feed lag vs replay 120 s. Part C: forward-look date. Estimate ~Mon 2026-12-14/15 (>= 40 games, >= 300 rows per cell; ~46 games by week 15), the rule wins over the date. Update H-INPLAY-NFL-1 forward-look column.
