# SESSION_HANDOFF — W80.2 (NBA opens) — PARTIAL: Part B done, Part A pending the games

<!-- session-meta
task_id: W80.2
tier: STANDARD
commit: 17d4f14
one_line_summary: W80.2 Part B done (nba_totals_applied REAL-AND-PRICED; first NBA index entry; seat B9 applied); Part A (opening-night readback) not run because the 10-20 games were unplayed at 2026-10-20T00:36Z
gg_touched: GG-891 (stale premise annotated); GG-940..945 claimed, none registered
adr_touched: none
vision_pillar: DEPTH
gap_measure: D5(b) NBA; B1 NBA
gap_delta: D5(b) NBA applied 4 -> 5 of 9 (scripts/distance_to_optimum.py, 2026-10-20); B1 NBA unchanged (Part A pending); verdict REAL-AND-PRICED, a rigorous NO for pace-only totals
pattern_sweep: Python 3.9 fromisoformat rejects Kalshi 5-digit fractional seconds: fixed at 3 sites in nba_totals_applied.py via parse_ts; board_survey_sports_store.iso_ts already tolerant; one remaining call parses a date-only string; full src/ sweep not done
surface_delta: 0
-->

**Result.** `nba_totals_applied`: real 0.96 (CI 0.47-1.48), priced 1.05 (0.80-1.29), residual -0.05 (-0.47 to +0.41), n=299 → REAL-AND-PRICED. No pre-registration drafted. Entry: `02_ARCHITECTURE_DESIGN/NBA_ENGINE/INDEX_ENTRY_PACE.md`. Next factor: game-level availability, then travel.
**Open items.** #289 post-merge Deploy job summary / t4-mlb decision not yet read (scripts/tests/docs only; no restart expected). GG-891 premise is stale (KXNBATEAMTOTAL listed, 374 valid rows; ceiling 12 of 12).

**One thing pending.** After the 10-20 games and the 12:40Z autoflip, run Part A (flips, registry readback, T2/T3 rows, points cells, silent arms) and close GG-570/890/892/891 on that evidence.
