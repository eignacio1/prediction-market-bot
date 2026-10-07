# W57.2 - MLB shadow settlement (GG-472) + GG-477 / GG-482 reads

Outcome join only. No Brier, log-loss, score or any result metric was computed or read (EXP-037 pre-registration).

## Built
- `src/prediction_market_bot/pregame_shadow/mlb_settlement.py`, `scripts/run_pregame_shadow_settle.py --sport mlb` (PR #170, CI green, merged as bec2a75).
- Source: MLB games cache (kept fresh by the GitHub Actions sync). A game settles only if status == Final and both scores present, matched on teams + start time (doubleheader-safe). Writes only `exp_output/PREGAME_SHADOW/settled/MLB_*.jsonl`; raw ledgers never touched. Idempotent per (market_ticker, band), first row per market.
- Deploy: t4-mlb restart decision `not_needed` (no file imported by t4-mlb changed). NRestarts=0.

## First VPS run (2026-10-07 ~00:30 UTC): settled rows per cell
| cell | T1 | T2 | T3 |
|---|---|---|---|
| MLB_MONEYLINE | 0 | 4 | 4 |
| MLB_RUN_LINE | 0 | 12 | 12 |
| MLB_GAME_TOTAL | 0 | 20 | 20 |
| MLB_TEAM_TOTAL | 0 | 28 | 28 |
Total 128. Raw rows per cell: T1 58-237, T2 32-224, T3 30-210. T1 settled 0: the T1 first-rows are for games not yet final in the cache (cache `last_final` 2026-10-05) - they should settle on later runs; **Investigated (2026-10-07):** all 58 moneyline T1 first-rows are for games on 10-06/07/08; none was final in the cache as of its stamp (2026-10-06T18:38Z, max final start 10-06 00:00Z). Not a defect; they settle as games finish and the cache refreshes. T2/T3 settled rows are games from 10-05/06.

## Cron
One new line appended (backup `/root/crontab.bak.w57_2.20261007T003146Z`; diff = 1 comment + 1 line): `41 11 * * *` -> `run_pregame_shadow_settle.py --sport mlb`. Mirrored in `deploy/cron_exp037_pregame_shadow.conf`.

## GG-477
01:25-01:40 UTC 2026-10-06 (first window after stagger): 0 oom lines. t4-mlb NRestarts=0, up since 2026-10-05 07:57. Last OOM 2026-10-05 01:30. RESOLVED, n=1 night.

## GG-482
Scheduled sync ran 2026-10-06 06:50 and 18:37 UTC (both success); VPS meta `refreshed_at` 2026-10-06T18:38:18Z matches. The 12:43 UTC run the block mentioned did not occur (schedule drift); gap 12h, inside the 26h limit.

## Note
GG-472 text said to use Kalshi's own settlement (GG-440); block directed cache final scores. Followed the block.

## Follow-up
Operator chose a Kalshi-settlement cross-check: registered as GG-487 (not built).
