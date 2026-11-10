# SESSION HANDOFF — W106.3 (B-058 retail flow: props and thin markets, net of costs)

- Status: PARTIAL (MLB measured; NBA/NFL/NHL props not measurable — not archived)
- B-058 state: MLB prop+line look DONE, no net-positive held-out cell; non-MLB props BLOCKED on a new archiver task (ROLLING_BACKLOG.json not edited)
- Branch @ SHA: session/20261110T011417Z-w106-3-props-net @ bed41d9
- PR + CI: #450, CI pending at write time (merge only on green head; do not merge on this note)
- Result: KXMLBHIT held-out net −1.4c/contract [−2.7, +0.0] (214 games); MLB game lines −3.2c [−5.0, −1.4] (1,188 games); 0 of 49 held-out cells net positive after Holm (best raw +2.3c, Holm p 0.74). Thin-book cells lose 8–20c. Props-vs-lines raw gap +1.2c vs +1.1c: "larger where retail trades" NOT supported.
- MEASURE MOVED: prop families measured net: 1 of ~40 listed (KXMLBHIT); net-positive held-out cells: 0 of 49.
- Stage reached: interpreted (not applied).
- vision_pillar: PROOF
- gap_measure: P2 / D1 (prop families measured net of costs)
- gap_delta: prop families measured net 0 -> 1 (of ~40 listed); verdict-grade cells 0
- pattern_sweep: n/a (no defect fixed)
- surface_delta: +1 module quant/props_calib.py (+tests), +12_EXPLORATORY/quant_w106_props; no live component, no cron
- Operator decisions: none.

## Not done / needs a task (approval by task name)
1. **Archive prop series' pre-start prices** (KXNBAPTS, KXNFLPASSYDS, KXNHLGOAL, KXMLBHR/HRR/KS/RBI/TB, ...): archiver currently carries only KXMLBHIT among props. Task name suggestion: "price-archive: add prop series" — register a GG from the reserved GG-1833..1835 range if wanted. No data waited on.
2. Part C pre-registration NOT written: no cell net positive held out after multiplicity (condition not met).
3. Flag: a pre-registered NBA player-points shadow arm and a KXNFLPASSYDS thin-market pre-registration exist. This block read public Kalshi settled data only, no shadow ledgers.
4. Caveats: MLB only (~3 months); liquidity tier = quoted half-spread class; entry = first snapshot per tier (real fills likely worse); settlements via public /markets + /historical/markets GETs (fetcher lived in scratchpad, not committed).
5. Files: 12_EXPLORATORY/quant_w106_props/{RESULT.md,PART_A_INVENTORY.md,results.json,run_props.py}; src/.../quant/props_calib.py; tests/test_quant_props_calib.py (4 known-answer tests pass locally; isolation test passes).
