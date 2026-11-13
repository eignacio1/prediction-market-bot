# Session handoff - W114.3 (B-085): the router, not the model's edge, picks the arm

**Status:** DONE (both parts merged; one follow-up listed below)
**Backlog:** B-085, Parts A and B landed; the E09 / E14 arm tables and a src caller of `route=` remain (follow-up, not started)
**Branch @ SHA:** main @ 330fbd2 (docs) on e862d90 (Part B) on c5b97f4 (Part A)
**PR + CI:** #497 (Part A) test pass, merged c5b97f4 · #499 (Part B) test pass, merged e862d90
**Result:** The orchestrator takes the router's arm and keeps the model edge only as the FADE entry input and a logged field; the history scorers lead with held-out net per arm and put Brier vs the market last.

## What changed
- `execution_bands_orchestrator.py`: `decide(..., route=)` / `batch_decide(..., routes=)`. RIDE, POT_OF_GOLD and MOMENTUM proceed on the router's side whatever the sign of the model edge; NO_BET passes; FADE proceeds only on an actionable edge on the routed side. **Unchanged path:** with no route (e.g. idle MLB T4M-PROJ) the legacy edge-gated logic runs. No src module calls the orchestrator today, so there is no live behaviour change. 9 tests, including "a routed RIDE row is not overridden by a negative model edge".
- `quant/retro_route.py`: `game_rows` and `arm_report` score one-quote-per-game history joins per leaf, held out (latest 30% of games), net of the exact taker fee, 90% game-clustered interval. Known-answer tests: RIDE wins when a favourite is underpriced, loses when overpriced.
- `score_vs_market.py`, `nhl_engine/part_b.py`, `run_w84_3.py` docstring: `arms` first, Brier labelled last. **`part_b.py` was syntax-checked and not run: it needs the box's event store.**
- Edge map: E01 and E10 now carry held-out arm net from `retro_route/results.json` (NFL game total, 28 games; NHL, 66 games). E09 (NBA player points) and E14 (MLB) have no retro_route family, so those rows say "not yet scored" instead of quoting a number. Status enum RULED_OUT unchanged; wording is "hypothesis closed (EXP-id, parked for R&D)".
- `DOCTRINE_CONFORMANCE.md` rows 9, 27, 33, 34 marked with commits. `OPERATOR_DIRECTIVES.md`: D-04 text updated, D-22 BUILT (#480 caca65f), recount.

## Report
- **MEASURE MOVED:** D-04 CONTRADICTED -> PARTIAL. In the file it already read PARTIAL after the 111.2 audit; the code rows that contradicted it (conformance 9, 27, 33, 34) went 4 -> 0, so decision points contradicting DOCTRINE: 4 -> 0 among the rows this block owned. Directive recount from the table: CONTRADICTED 0 · NOT BUILT 0 · PARTIAL 14 · BUILT 12 (26 rows). The older header line "CONTRADICTED 2" was stale (D-02 BUILT in W111.1). Pillars: PLUMBING.
- **Stage reached per factor:** none moved (no new factor; scoring path only).
- **Operator decisions:** none.
- `vision_pillar`: PLUMBING (doctrine conformance) · `gap_measure`: DOCTRINE_CONFORMANCE rows contradicting D-04 · `gap_delta`: 4 -> 0
- `pattern_sweep:` swept `src/ scripts/ tests/ deploy/ .claude/` for model-edge-gated arm choice; the orchestrator was the only src hit, and `scripts/edge_map*` does not exist. Other Brier-only scorers under `12_EXPLORATORY/` outside the four files above were not swept.
- `surface_delta:` 0 (no cron, service or workflow added)
- `directive_conflicts:` none. One premise differed from the file: the block calls D-04 CONTRADICTED; the file said PARTIAL.

## Not done
- Box deploy read-back: not needed for runtime (no src consumer of the orchestrator), and no `deploy_truth_read` result was read for this block.
- Follow-up: retro_route families for NBA player points and MLB so E09 / E14 get arm tables; a production caller that passes the router's `Route` into the orchestrator.
