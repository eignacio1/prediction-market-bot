# SESSION_HANDOFF — W96.1 Part C (B-009) — 2026-10-30

Status: Part C DONE (negative result). Parts A (waits on tonight's tips) and B done earlier.
Backlog: B-009 NBA engine prices player points — done, result NO GAIN leak-free; B-001 Part A still pending readback; ticket state reported here, ROLLING_BACKLOG.json not edited.
Branch @ SHA: code merged to main as 3809802 (PR #387, squash). Docs on session/20261030-w96-1-partc-docs.
PR + CI: #387 CI green, merged.
One-line result: engine-priced player points looked better than the existing arm by −0.0034 Brier, but that came from normalising shares over the players who played (post-game); the leak-free arm is level with base (pooled ALL +0.00001 [−0.00029, +0.00032]), worse at strike 20, season sign flips.
MEASURE MOVED: DEPTH — markets priced from one NBA engine: 4 families unchanged for held-out value; player points built (module + tests) but NOT credited as applied. D5 stage: aggregated + interpreted, not applied. EXP-044d not frozen. Nothing installed.
Operator decisions: none.
Next: after tonight's tips (~02:00Z) request box task `nba_engine_cron_readback` for v1+v2 per-game rows, tip−60 quote, errors, v2 memory (GG-1450 stays OPEN). A pre-tip points arm needs an expected-minutes input (Part B availability factors) before retesting.
Observe-only, untouched: B-017, B-007.

session-meta:
vision_pillar: DEPTH
gap_measure: D5
gap_delta: no change (player points built, leak removed, not applied)
pattern_sweep: n/a (no defect fixed) — the leak was in this block's own new study and removed there; the same normalise-over-who-played pattern is noted for any EXP-039-style study
surface_delta: none (new module imported by no service; no restart)
