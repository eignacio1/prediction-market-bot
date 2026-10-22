# SESSION HANDOFF — W84.3 NHL depth lane (20261022T0259Z)
vision_pillar: DEPTH
gap_measure: D5(b) NHL (stages of 12 seat rows); D5(a) NHL (components of 8)
gap_delta: D5(b) NHL aggregated 7 / interpreted 0 / applied 0 -> aggregated 2 / interpreted 2 / applied 3 (source SEATS/nhl.toml, 2026-10-21; "applied" = CLAUDE.md D5 meaning, a tested path to a price against the market; by the seat file's stricter header meaning applied is still 0). D5(a) NHL 0/8 -> 1/8 (cross_reference_compatibility; temporal_evolution NOT counted, no cross-season stability test).
pattern_sweep: n/a (no defect fixed)
surface_delta: 0 (offline exploratory scripts under 12_EXPLORATORY/nhl_engine/; no cron/service/workflow)

## Result
Three factor classes (shot-quality xG, goalie workload, special teams) built point-in-time from the event store, seasons 2021-2025 (2021 xG burn-in; 5,592 game rows). Part B on 2025 (n=1,306): verdict **too few to tell**. Factor coefficient on top of market 0.37, CI [-0.09, 0.80]; CV Brier blend minus market +0.0012 [-0.0006, +0.0030]. Full: 12_EXPLORATORY/nhl_engine/results_W84.md.

## For the strategic window
- Definition mismatch on "applied" (above) — decide which D5(b) uses going forward.
- Not built: same-point-in-season rank (n_prior spans seasons); 2018-2020 and 2026 not fetched; Kalshi NHL history covers 2025-26 only, so the single holdout equals the frozen model's holdout.
- SEATS/NHL_SEAT.md patched by hand: render_seat.py needs tomllib (py3.11+), local python is 3.9. Re-render on a newer python to confirm no drift.
- exp_output/KALSHI_HISTORY_NHL/ is untracked and not git-ignored; not committed. Worth an ignore rule (register if wanted).
- factor_frame.parquet is local only, not committed.
- No operator decisions pending.
