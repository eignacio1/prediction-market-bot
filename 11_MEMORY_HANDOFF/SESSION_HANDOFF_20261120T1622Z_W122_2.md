# Session handoff — W122.2 · pot-of-gold arm re-scored on all data and logged beside v1 as a candidate (B-024)
Common rules first line quoted: "# Wave 122 common rules". PR #545 merged (Test Suite + Docs Guard green on its head; Docs Guard's gaps-by-arm index was stale on main, regenerated in the PR).

## MEASURE MOVED
- **Arms with a candidate on box rows 3 -> 4 once deployed** (`pot_of_gold`, a new key in `router_candidates`; v1 `router` block untouched; shadow only; kelly 0). Not yet on the box: box HEAD at 16:21Z is ce63a82, one commit before the merge (c334dbf). The deploy workflow ships it from main.
- **Pot-of-gold cells (the 11-05 pre-registration): 0 earned · 17 IN_SAMPLE · 0 closed (hypothesis closed, parked for R&D).** Premise correction: the 17 are 15 MLB + 2 NFL, not NBA/NHL. MLB has 0 forward rows (idle). NFL KXNFLSPREAD/D1/1-5c has 31 contracts / 13 games, KXNFLTOTAL/D1/95-99c 25 / 23, against judged n 150 / 30 games. No score read. Holm 0 of 36.
- Re-score (descriptive, not a look; looks stay 2026-12-10 and 2027-01-14): 51,624 joined rows, MLB 5,325 · NFL 591 · NBA 466 · NHL 411 games. Props measured, mostly UNTESTED (thin). Full table and non-MLB leads for a new pre-registration: `12_EXPLORATORY/pot_of_gold/RESULT_W122.md`. Addendum written before reading: `POT_OF_GOLD_ADDENDUM_2026-11-20.md`.
- Candidate table `src/.../decision_trees/longshot_cells_w122.toml`: 234 cells, **0 orderable** (only the 17 may carry an orderable status; the rest are IN_SAMPLE with `measured_status` kept). So every pot_of_gold entry today is `NO_BET`, reason "cell status IN_SAMPLE is not orderable", with leaf id and reason on every pregame row it applies to (price buckets 1-15c / 85-99c). Routing result: no bet in these leaves, logged so each leaf accrues forward rows.

## Part C (24 h read-back) — not possible at paste time
Box read 16:21Z (`20261120T1621Z_a_deploy_truth_read`, `_b_candidate_arms_read`): OK, box = origin/main at ce63a82, but that predates this merge; candidates present are nba_depth, router_v2 (NBA, NFL, NHL), nhl_v2. Zero `pot_of_gold` rows. Per the no-future-data rule nothing waited on. Next: rerun `candidate_arms_read` ~24 h after the deploy stamp and report rows per sport. Check it lists the `pot_of_gold` key (it groups by map_version; the map version string is `pot_of_gold`).
- t4-mlb decision: MLB idle until 2027; the shadow runner restarts on deploy. No restart of t4-mlb needed for this change.

## Part C update (box read 17:03Z)
Deployed: box HEAD 3e469a3 = origin/main, includes c334dbf. `pot_of_gold` rows so far: **NBA 13**, NFL 0, NHL 0 (the shadow cycle had not yet covered a pot-of-gold price bucket in NFL/NHL; MLB idle). This is the first minutes after deploy, not the full 24 h; a final 24 h count is a re-run of `candidate_arms_read` after 2026-11-21 ~17:00Z. Not waited on.

## Tests
`tests/test_w122_2_pot_of_gold.py` (9): v1 router block byte-identical with and without the candidate; only a new key; no look-ahead (tier from row clock, table from frozen file); generator promotes nothing outside the 17; plus the W120.2 / W121.2 candidate tests (28 pass) and `test_exploratory_isolation` (the rescore script uses no subprocess, writes only via safe_out; the table is copied to decision_trees by hand).

surface_delta: 0 (no cron, service or workflow; one candidate key in the existing shadow writer)
pattern_sweep: `src/ scripts/ tests/` for other `router_candidates` consumers: `candidate_arms_read.py` groups by map_version and handles a new key; the shadow row writers append the dict whole. Fence violations in 12_EXPLORATORY scripts (subprocess, writes outside the fence) swept: only this script had them.
directive_conflicts: none (D-03 wording kept: "hypothesis closed, parked for R&D"; D-08 the pot of gold is an arm of the same tree)
vision_pillar: BREADTH (B1/B4 arms logging) + PROOF (P1)
Pushback: do not read 0 earned as an answer about the arm. The forward sample is 56 contracts; the next look is 2026-12-10.
Surface: box HEALTHY per queue; no installs run. Dependencies: deploy of c334dbf; NFL forward weeks to reach judged n.
