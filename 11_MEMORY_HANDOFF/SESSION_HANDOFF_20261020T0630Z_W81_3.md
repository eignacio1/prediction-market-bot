# SESSION_HANDOFF W81.3 — PARTIAL (Part A merged; Part B parked on a branch)
vision_pillar: BREADTH + EXECUTION
gap_measure: B1 40/107 -> not yet moved (cell lands NOT_IMPLEMENTED on merge: 108 cells, 40 logging); B4 2 -> 2 until SHADOW flip
gap_delta: none yet
pattern_sweep: n/a (no defect fixed)
surface_delta: +1 cron block (passyds_prekickoff, merged #298, NOT yet installed on box)

## State
- Part A merged: #298, #300, #301 (CI green). Box dry run OK (listed=18, errors=0). Install not yet run: gate was RED on this job's own items; #301 fixes that.
- Part B parked: branch `session/20261020T045139Z-w81-3-partb` @ 65bca71, pushed, NO PR yet. Frozen artifact sha256 1053c8433715baf1d732a3a773077755aa6b0895bd099b7d3856559595d4e0db. Held-out Brier 0.20021 vs baseline 0.21886 (reported, not a verdict).

## Remaining (in order)
1. Regenerate `02_ARCHITECTURE_DESIGN/SEATS/NFL_SEAT.md` with `python3 scripts/render_seat.py 02_ARCHITECTURE_DESIGN/SEATS/nfl.toml` on Python >=3.11 (local Mac 3.9 lacks tomllib; test_rendered_md_is_current will fail otherwise). Add `[[factor]]` rows (QB availability = aggregated; QB-vs-defense matchup = interpreted) with evidence paths, and point the new cell's `factors` at them.
2. Write tests/test_passyds_model.py (sha mismatch refusal, point-in-time features, cold start, QB out -> None, p_ge monotone, no network).
3. Open PR, read CI green, check `gh pr diff --name-only`, merge; confirm box deploy.
4. On box: `PYTHONPATH=src:. venv/bin/python scripts/passyds_install.py install` then `readback`; dry run should show model_status=ok.
5. After the first valid row (first game: Thu 10-22 TNF NE @ CHI, `KXNFLPASSYDS-26OCT22NECHI`, kickoff ~2026-10-23T00:15Z), flip the cell with promote_cell_status(..., SHADOW, superseding_reference="W81.3"), update seat status, read rows back on the box, fill results.md.
6. Update the 81.3 row in ACTIVE_QUEUE.md, append DECISION_LOG (heredoc), closing claim row. Candidate GG: install-gate catch-22 (new registered component turns budget RED before install; workaround in #301).
