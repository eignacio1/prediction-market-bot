# NBA opening night (2026-10-20) — read-back runbook (W78.3)

Purpose: BREADTH B1. A cold reader can run this on the evening of 10-20 and the morning of 10-21 and say whether the NBA arms logged and the cells flipped. Closes GG-570 on a clean read-back.

Box: `ssh prediction-market-vps`, repo `/opt/prediction-market-bot`. Everything below is read-only except the autoflip, which is idempotent and refuses to run before 2026-10-20.

## Facts to hold
- Frozen model identity = the artifact's internal `sha256` (`c351680aff9b6d6a83b2fb9c802c295730f9e27f5feaff91ecb17a6dc816e18e`), NOT the file-bytes hash. Fixed in W78.3 (GG-890); `frozen_model_sha()` in `scripts/w59_3_nba_flip_check.py`.
- A valid row: `model_sha256` == frozen sha, `0<p_yes<1`, `mid` set, `start_time_source` set, not `excluded_from_judged_n`.
- Preseason rows live in `exp_output/PREGAME_SHADOW_PRESEASON` (flagged `excluded_from_judged_n`); regular-season rows in `exp_output/PREGAME_SHADOW/NBA_*.jsonl` (game cells) and `NBA_NBA_PLAYER_POINTS_*.jsonl` (EXP-039); EXP-040 in `exp_output/PREGAME_SHADOW_EXP040/NBAMIN_*.jsonl`.
- Crons: T1 every 6h, T2 hourly, T3 every 10 min. Preseason smoke cron at :57.
- Flip record: `exp_output/PREGAME_SHADOW/nba_promotions.jsonl`, applied at import by `_apply_nba_game_promotions()` in `market_type_registry.py`.
- Realistic ceiling: 9 of 12 game cells. `KXNBATEAMTOTAL` has never been listed on Kalshi, so the 3 NBA_TEAM_TOTAL cells cannot get rows (GG-891). Points cells are already SHADOW.

## 10-20 evening (after first tip, ~T3 window)
1. Rows exist: `ls -l exp_output/PREGAME_SHADOW/NBA_*.jsonl` — expect MONEYLINE, SPREAD, GAME_TOTAL files (T1/T2/T3) modified today; points files too. Healthy: mtimes within the last cadence interval.
2. Row validity: `python3 scripts/w59_3_nba_flip_check.py --ledger-dir exp_output/PREGAME_SHADOW` — expect valid rows > 0 for moneyline/spread/total cells. 0 valid with rows present = identity or field problem: inspect one row's `model_sha256`, `mid`, `start_time_source`.
3. Silent arms: the `SILENT ARMS` block in the governance scan, or `python3 -c "from prediction_market_bot.pregame_shadow.silent_arms import *"` helpers. Healthy: `nba_shadow` and `nba_player_points_shadow` ok/idle, none SILENT while games were in window.
4. No orders from the shadow arm before valid rows; DEMO only. Check `deploy/demo_fill.env` is demo and the W68.2 hook (`make_on_row`) only fires on valid rows (still to be verified — see handoff).
5. Torn rows: grep run logs for `[CORRUPT_READ]`.

## 10-21 morning
1. Run the autoflip (it appends only for cells with valid rows): `python3 scripts/nba_cell_autoflip.py` — expect up to 9 promotions across the three T-bands; idempotent on re-run.
2. `cat exp_output/PREGAME_SHADOW/nba_promotions.jsonl` — one record per flipped cell with `superseding_reference: EXP-038`.
3. Registry read-back: import `MARKET_TYPE_REGISTRY` and confirm the flipped (NBA_MONEYLINE / NBA_SPREAD / NBA_GAME_TOTAL, T1/T2/T3) cells read SHADOW; team-total cells stay NOT_IMPLEMENTED.
4. Record B1 before -> after (cells logging / registered) in the RUNNING SITREP; close GG-570.

## A cell did not flip — decision list
- No rows for the cell: check the matching cron ran (cron log), the series is listed on Kalshi (read-only DEMO GET: `KXNBAGAME`, `KXNBASPREAD`, `KXNBATOTAL`), ticker grammar `<YY><MON><DD><AWAY3><HOME3>`, and ESPN `season_type` is 2 (regular). Team totals: expected, GG-891.
- Rows but 0 valid: run step 2 above; compare `model_sha256` to the frozen sha; look for `excluded_from_judged_n` or missing `mid`/`start_time_source`.
- Valid rows but no promotion: autoflip refuses before `NOT_BEFORE` (2026-10-20); re-run it; check it reports `[CORRUPT_READ]`.
- Promoted but registry still NOT_IMPLEMENTED: the registry import-time application is fail-safe and silent on garbage — validate the JSONL lines.
Do not change stakes, kelly_fraction, or any pre-registration; a wrong-looking pre-registration is a one-line operator item.
