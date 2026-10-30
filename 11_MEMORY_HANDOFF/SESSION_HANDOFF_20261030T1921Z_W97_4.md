# SESSION HANDOFF - W97.4 (NHL engine, B-012) - PARKED after Part A

Status: PARTIAL (parked at a pushed boundary on operator request)
vision_pillar: DEPTH
gap_measure: D4 NHL (data layer -> whole board priced from one engine); D5(b) NHL factors
gap_delta: scaffold built and tested (PR #390 merged, CI green); no real-data fit or score yet, so no measured movement
pattern_sweep: n/a (no defect fixed)
surface_delta: 0 (no running component; nothing installed)

## Done
- `src/prediction_market_bot/nhl_engine/` (inputs.py, goals.py) + 12 tests (leakage, known-answer, known-correlation). Merged as #390.
- Queue row updated (Part A).
- Deploy read / t4-mlb decision after merge NOT done; nothing running imports the package, so no restart expected. Confirm on resume.

## Not done (resume here)
1. Store rebuild: `nhl_event_store fetch --from-season 2021 --to-season 2026 --rps 8 --threads 8` into `exp_output/NHL_EVENTS` (main tree, untracked). Was at ~4,600/7,206 games when parked; if the process is gone, re-run the same command (cached files are skipped), then `compile --root <ROOT>`.
2. Real-data PIT assert via `c1_signal_ingestion/nhl_point_in_time.py`; walk-forward Poisson GLM + dispersion `fit_dispersion`; Poisson vs NB on held-out 2023-2025 seasons (Part B).
3. Part C: Brier per family vs results; vs Kalshi (archive rows since 2026-10-28 05:03Z; 89.7 NHL candles; public GETs for settlements); `quant/bayes_skill.py` skill weight. Freeze EXP-046 only if earned, else "not earned".
4. `12_EXPLORATORY/nhl_engine/results_W97_4.md`, NHL `[[engine]]` entry in ARCHITECTURE_COMPONENTS.toml, `python3.11 scripts/render_seat.py`.
- Muse cards R-047/R-067/R-080 were not found by repo grep; say so in results.
- Claim: T-1590..T-1592, GG-1590..GG-1592. Worktree: PM-worktrees/20261030T184514Z-w97-4-nhl-engine.
