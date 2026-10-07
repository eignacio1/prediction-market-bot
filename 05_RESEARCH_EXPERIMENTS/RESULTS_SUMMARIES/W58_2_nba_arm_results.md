# W58.2 — NBA game-market arm (shadow only): results

Branch `session/20261007T011627Z-w58-2-nba-arm`. Shadow only: no order, stake or kelly.

## Part A — Kalshi discovery (2026-10-06, public GET, `scripts/nba_kalshi_discovery.py`)

Raw output: `exp_output/NBA/discovery.json` (open + unopened states).

| Series | Fee type | Open markets / events | Event dates |
|---|---|---|---|
| KXNBAGAME (moneyline) | quadratic_with_maker_fees | 76 / 38 | 2026-10-06 to 2026-10-20 |
| KXNBASPREAD | quadratic_with_maker_fees | 186 / 7 | 2026-10-06 to 2026-10-07 |
| KXNBATOTAL | quadratic_with_maker_fees | 147 / 7 | 2026-10-06 to 2026-10-07 |
| KXNBATEAMTOTAL | quadratic | 0 / 0 (not yet listed) | none |
| KXNBAGAMES, KXNBASUMMERGAME | quadratic | 0 / 0 | none |

Ticker grammar (event = `<SERIES>-<YY><MON><DD><AWAY><HOME>`, all team codes 3 letters, all 30 teams seen, no drops):
- moneyline `KXNBAGAME-26OCT13INDOKC-OKC`
- spread `KXNBASPREAD-26OCT06BKNCHA-BKN38` (floor_strike 37.5)
- total `KXNBATOTAL-26OCT07MININD-256` (floor_strike 255.5)

Findings: preseason games are listed (2026-27 regular season not yet). Team total has zero listings, so its cells can only be registered NOT_IMPLEMENTED. Spread and total only list the next day or two, moneyline lists about two weeks ahead.

## Data source reachability (2026-10-06)
- ESPN NBA scoreboard: HTTP 200 from Mac and from VPS. Chosen source for schedule, start times and scores.
- stats.nba.com and cdn.nba.com: 403 from the VPS.

Date convention: the ticker date is the ET game date (KXNBAGAME-26OCT13INDOKC expires 2026-10-14T03:00Z, i.e. the evening of 10-13 ET). Kalshi gives no start time, so tip-off comes from the ESPN schedule.

## Part B — registry (this PR)
`NBA_MONEYLINE/SPREAD/GAME_TOTAL/TEAM_TOTAL` added with series KXNBAGAME/KXNBASPREAD/KXNBATOTAL/KXNBATEAMTOTAL, sport `nba`, existing `_NBA_GRAMMAR`; T1/T2/T3 cells NOT_IMPLEMENTED (12 cells). `tests/test_nba_game_registry.py` parses the three real sample tickers and all 30 team codes in both positions for every series.

## Part C/D — pre-registration and frozen model
Pre-registration `EXP038_NBA_PREGAME_SHADOW_PREREGISTRATION_2026-10-06.md` with Addendum D1. Frozen model `models/nba_pregame_v1.json`, sha256 `c351680aff9b6d6a83b2fb9c802c295730f9e27f5feaff91ecb17a6dc816e18e` (canonical_sha verified at load); held-out metrics in `models/nba_pregame_v1_heldout.json`. Trained off-box; no production retraining. ADR-0070 is PROPOSED and NFL-scoped, so NBA use under it is an operator decision.

## Part E — wiring
- Runner `scripts/run_nba_pregame_shadow.py`, settle `scripts/run_nba_pregame_shadow_settle.py`; ESPN schedule backfill gained `--lookahead` (default 21) because future dates were never fetched.
- Cron block (BEGIN/END EXP-038 NBA, mirrored in `deploy/cron.nba_shadow`): backfill 09:47Z, T1 `11 */6`, T2 `16 *`, T3 `9,19,29,39,49,59 *`, settle 10:23Z. Backup `/root/crontab.pre_w58_2.20261007T021506.bak`; 20 lines added, 0 removed, pre-existing lines byte-identical.
- By-hand VPS run logged NOTHING, as expected: the 10-06..10-20 markets are preseason and the schedule index holds regular season only (by design). A simulated-clock dry run (`--now 2026-10-19T20:00Z`, throwaway dir) wrote valid rows, proving the path.
- First real T1 rows expected ~2026-10-18/19. Registry cells NOT flipped to SHADOW (rule: only when valid rows exist). Team-total series had zero listings.
- Deploys: PR #174 t4-mlb `skip_live_game`; PR #176 `not_needed`.

## Part F — dashboards
Live Terminal shadow panel globs `exp_output/PREGAME_SHADOW/**/*.jsonl` and picks up NBA ledgers automatically. Visual Dashboard: NBA EVIDENCE clock plus cron-arm health rows added (PR #176, deployed); currently "NBA (no ledgers)".
Unverified, not changed: `web_dashboard._shadow` settled-copy count reads `outcome` while settle writes `y` (also affects NFL); `_season_state` has no NBA entry.
