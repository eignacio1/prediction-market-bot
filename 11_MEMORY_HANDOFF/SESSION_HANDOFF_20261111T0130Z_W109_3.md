# SESSION_HANDOFF — W109.3 NBA player props from the NBA engine (B-070)

Status: DONE | PR #466 merged (57fee5a), CI green on head 7dac6f3 | branch session/20261111T003828Z-w109-3-nba-props

vision_pillar: BREADTH
gap_measure: B4 props families with a registered cell; B1 registered cells; backtest Brier per family
gap_delta: props families with a registered cell 1 (points) -> 4 (+rebounds, assists, threes); +9 SHADOW cells registered (SHADOW 37 -> 46). Source: market_type_registry.py / PR #466. None LOGGING until the install is approved, so logging-B4 is unchanged until then.
pattern_sweep: n/a (no defect fixed in existing code); own-PR fixes: exploratory fence in 12_EXPLORATORY scripts, cron-minute collision, shadow-count test, NBA seat toml/md.
surface_delta: +1 prepared runner (paused registry entry, cron minute 39, flocked), nothing installed.

## Results
Backtest (15,364 settled props, 96 games), Brier engine minus market mid, game-clustered 95% CI: points +0.0156 [+0.0106,+0.0210]; rebounds +0.0103 [+0.0069,+0.0141]; assists +0.0072 [+0.0029,+0.0114]; threes +0.0068 [+0.0030,+0.0108]. Null in the market's favour; cells proceed as pre-registered (EXP-047, modal outcome = engine worse).

## Operator decision
Approve by name: `nba_engine_props_shadow_install` (readback: `nba_engine_props_shadow_readback`; undo: `nba_engine_props_shadow_uninstall`). NOT run.

## Open / not built
- Settlement join for the new shadow ledgers (out of scope; register a GG if wanted).
- Pre-reg id EXP-047 chosen because EXP-041 was taken.
- `precheck_changed.py` missed 3 CI failures; run related suites before PR.
