# Session handoff — W92.3 NBA engine B7 lineups and on/off (point-in-time from PBP)

```
vision_pillar: DEPTH
gap_measure: D5(b) NBA B7 none -> interpreted (total side); D4 NBA first factor class built point-in-time from event-level data
gap_delta: B7 none -> interpreted; D5(b) NBA interpreted count +1 (re-read the SITREP for the n of 15); applied unchanged
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no running component; module + tests + exploratory driver + results + seat row)
```

**Result** (full numbers `12_EXPLORATORY/nba_lineups/results_W92_3.md`): lineup layer lowers held-out total MSE by 4.04 (95% CI 1.92 to 6.10, n=2008 games, 2024-25 and 2025-26), survives the prior-season-carry control (3.99, 1.89 to 6.23); 2025-26 alone CI includes 0. Margin: no gain beyond prior-season carry (0.060, -0.067 to 0.187); on/off swing adds nothing. Availability delta adds to margin (0.267, 0.105 to 0.445) but needs who actually played, so it is an upper bound until an availability feed exists (GG-985).

**Stage per factor:** B7 lineup/on-off: aggregated -> interpreted (total). Not applied: NBA pre-game prices are not captured (cron lines registered, not installed); settled Kalshi NBA markets since 2026-10-20: 55 moneyline events, 31 spread, 36 total, no pre-game prices, effect ~1% MSE, so underpowered by construction.

**Merged:** PR #359 (squash). CI green on the PR (first run failed on two fences, both fixed: exploratory writes routed through `safe_out()`, NBA seat md regenerated with python3.11 because the box/CI render needs `tomllib`). Local python3 is 3.9: render seats with `python3.11 scripts/render_seat.py <toml>`.

**Caveats:** K=1000 and decay 0.5 not tuned, no sensitivity run; 3-9% of games dropped for bad player rows. GG-1370..1372 unused.

**Next:** install NBA/NHL price capture (92.1), then re-run the applied test once pre-game prices exist; availability feed (GG-985) for the margin-side signal.
