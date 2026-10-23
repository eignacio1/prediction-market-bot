# SESSION HANDOFF — W86.2 (quant A2: what the market's ladders imply, and where they contradict themselves)

<!-- session-meta
task_id: W86.2
tier: STANDARD
timestamp: 2026-10-23T00:45:00Z
commit: 33a1a39
one_line_summary: W86.2 DONE (measure only): market-implied margin/total distributions for 45 NFL / 28 NBA / 19 MLB games and ladder coherence over 2.0M strike-snapshots; only NFL TEAMTOTAL has net survivors, none with known size.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH + EXECUTION
gap_measure: DEPTH: games with a market-implied margin/total distribution (mean and spread); EXECUTION: ladder coherence violations per 1,000 strike-snapshots after fees and size
gap_delta: implied-distribution games 0 -> 45 NFL / 28 NBA / 19 MLB (shadow-arm ladders, T1-T3); net-of-fee violations ~0.07 per 1,000 overall (~150 of ~2.0M strike-snapshots), NFL TEAMTOTAL 0.404 [0.035, 0.96]; net-and-size-confirmed 0 (all unknown)
pattern_sweep: exploratory-fence defects (forbidden string fragment in a docstring; write-shaped .replace()) fixed in this block's own files; swept the rest of 12_EXPLORATORY via tests/test_exploratory_isolation.py, which passes.
surface_delta: 0 (no running component added)
-->

Status: DONE (measure only) | branch session/20261023T001531Z-w86-2-ladder-implied @ 33a1a39 | PR #331 (CI result recorded in final report)

Full results, quant-bar triples, caveats: `12_EXPLORATORY/ladder_implied/results_W86.md`.

## Result
- Market and our fixed width: the market uses nearly one width per sport too (between-game CV 2-5%). Our NFL margin 13.2 is a key-number-inclusive spread; the market's plain-normal fit reads 12.12 [12.07, 12.22]. Key-number-aware refit gives 13.20. MLB run line 3.49 vs our 4.4.
- Disagreement is mostly CENTER, except the MLB run line (61% width; ~100% of its summed edge disappears under the market's width).
- Coherence: same-contract test vacuous (feed derives NO from YES). Fees erase nearly all exclusive-set violations. NFL TEAMTOTAL is the only series with persistent net survivors (90, longest 15 runs); consistent with EXP-033 (0/24 cells survive, NFL TEAMTOTAL watch item). No size confirmable.

## Stage per factor
Implied width/center: interpreted. NFL key-number mass: interpreted. Ladder coherence: aggregated.
Granularity index: split done; rank vs history NOT done (archive starts 2026-08-01); matchup cross NOT done; market map done for ladders; application none.

## Helpers for the quant core next wave
parse_ticker, survival_points, fit_normal, fit_keynum, decompose, tolerant parse_ts, coherence.py checkers (fee, monotonic, exclusive_set, dominates, sized). Left in `12_EXPLORATORY/ladder_implied/`; 86.1 owns `quant/`.

## Caveats / owed
- PRICE_ARCHIVE has no start times (in-play contamination); depth is sampled; NBA preseason; NHL not covered; MLB run line ~6 strikes; buy->'no' depth mapping unverified.
- CLAUDE.md Steps 1-4 / Q1-Q7 were not run in full (cached governance scan only: stubs CLEAN, 199 open GGs, no duplicate ids).
- Q6 worry: size is the unanswered question. Every net survivor has unknown size because depth is sampled, so "tradeable" is unestablished; and in-play snapshots may be producing some of the NFL TEAMTOTAL violations.
- Operator decisions: none.
