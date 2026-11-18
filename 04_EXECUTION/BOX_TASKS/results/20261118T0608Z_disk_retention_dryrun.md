# Box task `disk_retention_dryrun` — 20261118T0608Z_disk_retention_dryrun

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T0608Z_disk_retention_dryrun.toml`
- note: W118.4 Part B: re-request after box deploy
- ran: 2026-11-18T06:09:10Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/run_disk_retention.py --dry-run`

```
# disk_retention dry run (changes nothing)

## would compress (readers verified): 9 files, ~1880.2 MB freed
 1050.1 MB -> saves ~ 1009.6 MB  age  32.7d  exp_output/KALSHI_HISTORY/thin/raw_2026-10-16.jsonl
  424.3 MB -> saves ~  404.8 MB  age  40.2d  exp_output/KALSHI_HISTORY/raw/raw_2026-10-09.jsonl
  368.1 MB -> saves ~  350.8 MB  age  40.2d  exp_output/KALSHI_HISTORY/raw/raw_2026-10-02.jsonl
   37.5 MB -> saves ~   34.1 MB  age  67.5d  logs/paper_portfolio_mlb_t4.pre_gg271_migration.20260911T191230Z.json.bak
   37.5 MB -> saves ~   34.1 MB  age  67.5d  logs/paper_portfolio_mlb_t4.pre_gg271_migration.20260911T191216Z.json.bak
   37.5 MB -> saves ~   34.1 MB  age  67.5d  logs/paper_portfolio_mlb_t4.pre_gg271_migration.20260911T190938Z.json.bak
    7.0 MB -> saves ~    6.4 MB  age  64.0d  logs/paper_portfolio_mlb_t4.gg279_verify.20260915T045755Z.json.bak
    7.0 MB -> saves ~    6.4 MB  age  64.0d  logs/paper_portfolio_mlb_t4.gg279_verify.20260915T045745Z.json.bak
    0.0 MB -> saves ~    0.0 MB  age 144.2d  logs/paper_portfolio_mlb.json.bak

## held (readers not taught yet): 99 files, ~1819.1 MB would free once they are
  341.6 MB -> ~  322.0 MB  kalshi_history_rebuilt   exp_output/KALSHI_HISTORY/rebuilt_2026-10-09/candles/KXNFLGAME.jsonl
   45.5 MB -> ~   43.2 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-11-02.jsonl
   40.0 MB -> ~   37.7 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-10-30.jsonl
   38.3 MB -> ~   35.9 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-10-31.jsonl
   37.4 MB -> ~   35.3 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-11-03.jsonl
   36.7 MB -> ~   34.4 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-10-29.jsonl
   36.5 MB -> ~   34.6 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-10-28.jsonl
   32.1 MB -> ~   30.1 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-19.jsonl
   31.0 MB -> ~   29.0 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-23.jsonl
   29.9 MB -> ~   28.1 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-16.jsonl
   28.7 MB -> ~   26.8 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-11-01.jsonl
   28.0 MB -> ~   26.3 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-26.jsonl
   27.1 MB -> ~   25.5 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-09.jsonl
   25.6 MB -> ~   24.2 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-15.jsonl
   24.2 MB -> ~   22.8 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-09-06.jsonl

## journald: 1681.0 MB used, cap 200M -> frees ~1481.0 MB

TOTAL if applied now: ~3361.2 MB (compress 1880.2 MB + journald 1481.0 MB); held adds ~1819.1 MB

```
