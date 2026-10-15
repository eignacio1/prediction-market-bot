# Session handoff — W75.5 The NFL book closes

Status: DONE | branch session/20261015T051115Z-w75-5-nfl-book-closes @ 7ab0c75 (PR #262, merged) | CI: PR green; post-merge run had one unrelated network-timeout failure, re-run queued | NFL book closed: 4 positions booked, recurring sweep on the 09:30 cron, typed settlement, OPE invariant
MEASURE MOVED: NFL positions open past game end + 24 h 4 -> 0 (box portfolio file, 2026-10-15)

vision_pillar: EXECUTION
gap_measure: E2 / PROOF — NFL positions open past game end + 24 h
gap_delta: 4 -> 0 (source: box logs/paper_portfolio_t1_nfl_game_market.json, 2026-10-15)
pattern_sweep: live books clean; late opens only in non-live artifacts (INVALIDATED_20260601: 3 NBA; manual_backup_20260923: 42 NFL); NHL/MLB postseason have no paper books
surface_delta: 0
stage per factor (ADR-0075): settlement/booking = verified on box; invariant = verified on box

Operator decisions: none. Optional follow-ups: type `nhl_shadow_settle.py` the same way; confirm the Deploy job summary / t4-mlb restart decision for 7ab0c75 (not observed).
Gaps: GG-746, GG-751 RESOLVED; GG-763 part (a) done, (b)-(d) open. Details: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W75_5_nfl_book_closes.md
