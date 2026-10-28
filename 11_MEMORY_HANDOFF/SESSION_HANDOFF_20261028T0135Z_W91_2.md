# SESSION_HANDOFF — W91.2 (ride tree as code + ladder ride)

Status: DONE | Part A #353 merged (6175da7), Part B #356 merged (55362dc), CI green both.
One line: ride tree is code (RIDE 3,838 -> 0 of 164,354 on replay); ladder ride measured: strike converges toward ladder gross, net +0.007 [-0.002, 0.017]; 2 of 36 cells HELD_OUT (KXMLBTOTAL T0-2h tight).

vision_pillar: DEPTH (+PROOF)
gap_measure: D5(a) decision_trees; ride kinds with measured basis; ladder cells tested OOS
gap_delta: D5(a) ride tree stub -> tested code (ACTIVE_QUEUE, #353); ride kinds 1 -> 2 (results_W91_2.md); ladder cells tested OOS 0 -> 36 tested, 2 HELD_OUT
Stage per factor: ladder gap = interpreted; applied only for the 2 HELD_OUT cells (one OOS time split, not FORWARD_PASSED).
pattern_sweep: n/a (no defect fixed; one lint hit in my own new file fixed in Part A; safe_out prefixes 12_EXPLORATORY so outdir must be relative to it - noted, not a repo defect)
surface_delta: none (nothing wired, no new running component; fetch_settle is read-only public GETs)

Deploy: post-merge run 40611123158 (#353) only a test job, success; no Deploy job, no t4-mlb restart (decision_trees only, nothing wired). #356 touched quant/exploratory/tests only: no t4-mlb change.

Not covered: NBA/NHL (no price archive, GG-1330). Caveats: fills at quoted price assumed; 5c+ cell has 30 OOS games; ride_cells.toml unchanged.
Operator decisions: none. Window at wave close: consider adding the 2 KXMLBTOTAL LADDER cells as HELD_OUT to ride_cells.toml and forward-test them.
Discovery (unregistered; no GG filed this session): PRICE_ARCHIVE rows carry no settlement result, so totals/spreads need a Kalshi fetch (fetch_settle.py).
