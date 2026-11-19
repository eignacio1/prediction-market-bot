# Box task `disk_retention_dryrun` — 20261119T0522Z_disk_retention_dryrun

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0522Z_disk_retention_dryrun.toml`
- note: W120.3: after the 3 readers moved to io_jsonl (#531); held bytes should be 0 for verified targets
- ran: 2026-11-19T05:22:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/run_disk_retention.py --dry-run`

```
# disk_retention dry run (changes nothing)

## would compress (readers verified): 1139 files, ~2684.6 MB freed
   52.6 MB -> saves ~   49.9 MB  age  14.2d  exp_output/PRICE_ARCHIVE/prices_2026-11-04.jsonl
   45.5 MB -> saves ~   43.2 MB  age  16.2d  exp_output/PRICE_ARCHIVE/prices_2026-11-02.jsonl
   40.0 MB -> saves ~   37.7 MB  age  19.2d  exp_output/PRICE_ARCHIVE/prices_2026-10-30.jsonl
   38.3 MB -> saves ~   35.9 MB  age  18.2d  exp_output/PRICE_ARCHIVE/prices_2026-10-31.jsonl
   37.4 MB -> saves ~   35.3 MB  age  15.2d  exp_output/PRICE_ARCHIVE/prices_2026-11-03.jsonl
   36.7 MB -> saves ~   34.4 MB  age  20.2d  exp_output/PRICE_ARCHIVE/prices_2026-10-29.jsonl
   36.5 MB -> saves ~   34.6 MB  age  21.2d  exp_output/PRICE_ARCHIVE/prices_2026-10-28.jsonl
   32.1 MB -> saves ~   30.1 MB  age  60.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-19.jsonl
   31.0 MB -> saves ~   29.0 MB  age  56.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-23.jsonl
   29.9 MB -> saves ~   28.1 MB  age  63.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-16.jsonl
   28.7 MB -> saves ~   26.8 MB  age  17.2d  exp_output/PRICE_ARCHIVE/prices_2026-11-01.jsonl
   28.0 MB -> saves ~   26.3 MB  age  53.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-26.jsonl
   27.1 MB -> saves ~   25.5 MB  age  70.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-09.jsonl
   25.6 MB -> saves ~   24.2 MB  age  64.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-15.jsonl
   24.2 MB -> saves ~   22.8 MB  age  73.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-06.jsonl
   23.5 MB -> saves ~   22.1 MB  age  54.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-25.jsonl
   23.2 MB -> saves ~   21.8 MB  age  61.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-18.jsonl
   22.7 MB -> saves ~   21.5 MB  age  57.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-22.jsonl
   22.4 MB -> saves ~   21.0 MB  age  55.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-24.jsonl
   21.9 MB -> saves ~   20.6 MB  age 102.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-08.jsonl
   21.8 MB -> saves ~   20.5 MB  age  59.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-20.jsonl
   21.4 MB -> saves ~   20.1 MB  age  74.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-05.jsonl
   21.3 MB -> saves ~   20.0 MB  age  71.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-08.jsonl
   21.1 MB -> saves ~   19.9 MB  age  68.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-11.jsonl
   20.3 MB -> saves ~   19.1 MB  age  88.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-22.jsonl
   19.8 MB -> saves ~   18.5 MB  age  62.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-17.jsonl
   19.6 MB -> saves ~   18.5 MB  age  99.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-11.jsonl
   19.4 MB -> saves ~   18.3 MB  age  66.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-13.jsonl
   19.1 MB -> saves ~   18.0 MB  age  85.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-25.jsonl
   19.0 MB -> saves ~   17.8 MB  age  78.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-01.jsonl
   18.9 MB -> saves ~   17.8 MB  age  52.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-27.jsonl
   18.8 MB -> saves ~   17.7 MB  age  84.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-26.jsonl
   18.6 MB -> saves ~   17.5 MB  age 105.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-05.jsonl
   18.5 MB -> saves ~   17.4 MB  age  95.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-15.jsonl
   18.4 MB -> saves ~   17.4 MB  age  75.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-04.jsonl
   18.3 MB -> saves ~   17.2 MB  age  92.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-18.jsonl
   18.1 MB -> saves ~   17.0 MB  age  77.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-02.jsonl
   18.0 MB -> saves ~   16.9 MB  age  98.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-12.jsonl
   17.8 MB -> saves ~   16.7 MB  age  67.2d  exp_output/PRICE_ARCHIVE/prices_2026-09-12.jsonl
   17.4 MB -> saves ~   16.3 MB  age 106.2d  exp_output/PRICE_ARCHIVE/prices_2026-08-04.jsonl

## held (readers not taught yet): 13 files, ~366.8 MB would free once they are
  341.6 MB -> ~  322.0 MB  kalshi_history_rebuilt   exp_output/KALSHI_HISTORY/rebuilt_2026-10-09/candles/KXNFLGAME.jsonl
   11.8 MB -> ~   11.1 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T1.jsonl
    9.9 MB -> ~    9.3 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T1.jsonl
    9.0 MB -> ~    8.3 MB  audit_ledgers            logs/audit_t4.jsonl
    4.8 MB -> ~    4.7 MB  audit_ledgers            logs/audit_t1_nfl_game_market.jsonl
    4.4 MB -> ~    4.1 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T2.jsonl
    3.7 MB -> ~    3.5 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T2.jsonl
    2.9 MB -> ~    2.8 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T1.jsonl
    0.4 MB -> ~    0.3 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T2.jsonl
    0.3 MB -> ~    0.3 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_SPREAD_T3.jsonl
    0.3 MB -> ~    0.3 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_GAME_TOTAL_T3.jsonl
    0.0 MB -> ~    0.0 MB  pregame_shadow_ledgers   exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T3.jsonl
    0.0 MB -> ~    0.0 MB  audit_ledgers            logs/audit_nfl.jsonl

## journald: 190.8 MB used, cap 200M -> frees ~0.0 MB

TOTAL if applied now: ~2684.6 MB (compress 2684.6 MB + journald 0.0 MB); held adds ~366.8 MB

```
