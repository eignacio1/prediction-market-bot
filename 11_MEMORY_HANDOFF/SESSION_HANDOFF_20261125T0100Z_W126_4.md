# Session handoff — W126.4 Kalshi combo markets priced and logged
**Last reviewed:** 2026-11-25. Branch `session/20261125T002536Z-w126-4-combo-markets`. Common rules read: "# Wave 126 common rules".

**MEASURE MOVED:** B4 (parlay families logging) 0 -> 0 until activation; the writer is built and tested, registry entry PAUSED. D3: combo arm
pre-registered (EXP-COMBO-001, committed before any combo row). Gap-measure is PLUMBING-free: nothing live changed.

## Part A — mechanics (`12_EXPLORATORY/pot_of_gold/MECHANICS.md`, sample `combo/*.jsonl.gz`, 2026-11-25T00:27Z)
- **Brief correction:** per-game NBA collections (196) ended 2026-10-07; NBA same-game combos now live inside rolling KXMVECROSSCATEGORY-R.
  The registry cell maps NBA_SAME_GAME_COMBO to `KXMVENBASINGLEGAME` (stale): left untouched, window to decide.
- No standing book: 59,453 of 61,000 open combos have no quote; 6 two-sided. NBA same-game: 7,203 open, 2 two-sided, 70 ask-only (ask quartiles 0.14/0.39/0.56). Trades are RFQ-style.
- **T-2h / T-30m spreads are not measurable historically** (public API has no combo book history). The writer logs them forward.
- Combo fee multiplier not in `kalshi_fees.json`; default taker used, flagged unverified.

## Part B — price (`nba_engine/combo_price.py`, tests `tests/test_nba_combo_price.py`)
Kalshi leg -> engine draws for moneyline, spread, total, team total, player points/rebounds/assists/threes; NO side negated; any leg count.
Known answers: independent legs = product; correlated same-player pair > product. Unpriced with reason: steals, blocks, stocks, PRA, 2D/3D,
1H/1Q, precise total, `...PROT` variants (semantics unidentified). Same-player cross-stat is priced from joint.py but FLAGGED and kept out of scoring.
Spread strike convention checked live (`BOS19` = "wins by over 18.5").

## Part C — log
`scripts/nba_combo_shadow.py` (off unless PM_COMBO_SHADOW=on), `deploy/cron.nba_combo_shadow`, registry `cron|41 * * * *|scripts/nba_combo_shadow.py` status paused.
Not run live here (no box data in the worktree): first live run is the activation check. Activation proposal with surface check is the last section of COMBO_PREREG.md.

## Not done / next
- Activation needs your approval and a box task `nba_combo_shadow_install` (not in the allowlist). Cells stay NOT_IMPLEMENTED until rows land; then the window moves them.
- First pre-registered look is quote availability, not P&L: an ask shows on ~1% of combos, so most leaves stay under judged n (250 rows, 40 games) for months.

directive_conflicts: none found (OPERATOR_DIRECTIVES.md not re-read in full this session; D-09 cited from the queue)
surface_delta: 0 live (1 paused cron registered)
pattern_sweep: grep of src/ scripts/ tests/ deploy/ for combo pricing found only sgp_price.py (2-3 legs, no NO side); extended via combo_price.py, not edited
vision_pillar: BREADTH B4 / DEPTH D3 · gap_measure: B4 · gap_delta: 0 now, +1 family on activation
