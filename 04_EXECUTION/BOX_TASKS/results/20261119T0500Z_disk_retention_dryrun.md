# Box task `disk_retention_dryrun` — 20261119T0500Z_disk_retention_dryrun

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0500Z_disk_retention_dryrun.toml`
- note: W119.4 post-merge (#529): bytes the extended policy (price_archive, depth, frozen_evidence_check) would free; read-only
- ran: 2026-11-19T04:53:32Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/run_disk_retention.py --dry-run`

```
# disk_retention dry run (changes nothing)

## would compress (readers verified): 0 files, ~0.0 MB freed

## held (readers not taught yet): 100 files, ~1869.0 MB would free once they are
  341.6 MB -> ~  322.0 MB  kalshi_history_rebuilt   exp_output/KALSHI_HISTORY/rebuilt_2026-10-09/candles/KXNFLGAME.jsonl
   52.6 MB -> ~   49.9 MB  price_archive            exp_output/PRICE_ARCHIVE/prices_2026-11-04.jsonl
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

## journald: 190.8 MB used, cap 200M -> frees ~0.0 MB

TOTAL if applied now: ~0.0 MB (compress 0.0 MB + journald 0.0 MB); held adds ~1869.0 MB

```
