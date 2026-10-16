# SESSION_HANDOFF W78.3 — NBA opening night (10-20) ready — PARTIAL, cut short by operator for time

vision_pillar: BREADTH
gap_measure: B1 (NBA cells logging: 12 registered game cells + points cells) 
gap_delta: no measured change yet. Before: 0 of 12 NBA game cells can flip (sha bug). After PR #274 merges: 9 of 12 can flip on 10-21 (3 team-total cells blocked: Kalshi has never listed KXNBATEAMTOTAL). Source: dry run on preseason ledger, VPS, 2026-10-15 (NO-ROWS / 0 valid for all 12 before the fix).
pattern_sweep: file-bytes model-hash pattern searched in scripts/ src/ tests/ 12_EXPLORATORY/ — no other instance. Glob-masking pattern (NBA_*.jsonl) NOT yet swept for other sports' silent-arm loaders (see TODO 5).
surface_delta: 0
stage per factor: n/a (plumbing for B1; no factor classes touched)

## Done
- Found + fixed the blocker: `scripts/nba_cell_autoflip.py:38` and `scripts/w59_3_nba_flip_check.py:32` hashed the model FILE BYTES (`b05130b0…`); rows carry the artifact's internal `sha256` (`c351680aff9b6d6a83b2fb9c802c295730f9e27f5feaff91ecb17a6dc816e18e`). Every row was invalid -> no game cell could ever flip. Fix: `frozen_model_sha()` in `w59_3_nba_flip_check.py`; 3 tests corrected; regression test added (`tests/test_w69_2_nba_opening_night.py`). 17 tests pass locally.
- PR: https://github.com/eignacio1/prediction-market-bot/pull/274 (branch `session/20261016T053532Z-w78-3-nba-opening-night`). CI was pending at handoff. NOT MERGED.
- NBA-T1 premise corrected: "registry NOT_IMPLEMENTED while code dispatches" is by design (evidence-gated flip via `nba_promotions.jsonl`, applied by `_apply_nba_game_promotions()`); the real defect was the sha. Points cells (EXP-039) are already SHADOW. The judged `PREGAME_SHADOW` dir has no NBA files, so nothing can flip early; autoflip refuses before 2026-10-20 (`NOT_BEFORE`).
- The "no NBA silent-arm coverage" premise is stale: 4 NBA specs exist in `silent_arms.py` SPECS.

## TODO for the next terminal (in order)
1. Merge #274 once CI is green (own PR only). Read the Deploy job summary; record the t4-mlb decision. Read back on the box (`ssh prediction-market-vps`, /opt/prediction-market-bot): `python3 scripts/w59_3_nba_flip_check.py --ledger-dir exp_output/PREGAME_SHADOW_PRESEASON` should now show valid rows (preseason rows carry `excluded_from_judged_n`, so for a true dry run copy the ledgers to a mktemp dir with the preseason flags stripped and pass `--ledger-dir/--out/--today`; remove the dir after). Expect 9 cells flip, 3 team-total cells NO-ROWS.
2. Read-only Kalshi DEMO GETs: confirm KXNBAGAME / KXNBASPREAD / KXNBATOTAL / KXNBAPTS list opening-night (10-20) markets and tickers match `_NBA_GRAMMAR` (`<YY><MON><DD><AWAY3><HOME3>`). KXNBATEAMTOTAL: confirm still unlisted.
3. Verify W68.2 NBA staked runner: `scripts/run_nba_pregame_shadow.py` `on_row=None if (a.preseason or a.dry_run) else make_on_row(ad)`; check DEMO-only creds (`deploy/demo_fill.env`), `SHADOW_FLAT_STAKE`, that no order precedes the first valid rows. Not checked this session. Do not change stakes/kelly.
4. Part B code (PR + CI, no new running component): in `silent_arms.py` `load_inputs`, the `nba_shadow` arm uses `led.glob("NBA_*.jsonl")`, which also matches `NBA_NBA_PLAYER_POINTS_*` and masks a silent game arm. Restrict to the game families (MONEYLINE/SPREAD/GAME_TOTAL/TEAM_TOTAL), add a points arm if absent, add tests (silent / ok / idle / unknown). Confirm silent_arms is in the light governance scan or note GG-758.
5. Sweep the same glob-masking pattern in other sports' arms in `load_inputs`.
6. Write `02_ARCHITECTURE_DESIGN/NBA_OPENING_NIGHT_RUNBOOK.md`: 10-20 evening and 10-21 morning read-back (files: `exp_output/PREGAME_SHADOW/NBA_*.jsonl`, `nba_promotions.jsonl`; counts of valid rows per cell; "healthy" = rows with sha `c351680a…`, 0<p<1, mid set; what to do if a cell did not flip: run flip_check, inspect invalid reasons, `[CORRUPT_READ]`, the SILENT ARMS block). Cron cadence: T1 every 6h, T2 hourly, T3 every 10 min. GG-570 closes on that read-back.
7. Register GGs (use GG-890..894; verify unused first, GG-885 is the last seen): (a) sha identity bug (fixed in #274); (b) KXNBATEAMTOTAL never listed -> 3 team-total cells cannot flip, B1 ceiling is 9; (c) silent-arm glob masking. Also: GG-759 says the registry comment near L945 wrongly claims SHADOW means no orders. Update NBA-T1 status in `02_ARCHITECTURE_DESIGN/TENSIONS/nba.toml` (check ownership). Append to DECISION_LOG (append-only).
8. Flip `04_EXECUTION/ACTIVE_QUEUE.md` row 78.3 to DONE only after steps 1–7 and read-back.

## Operator decisions
None. (Pre-registrations untouched.)
