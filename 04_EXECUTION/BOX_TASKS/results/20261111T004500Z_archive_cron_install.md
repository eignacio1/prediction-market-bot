# Box task `archive_cron_install` — 20261111T004500Z_archive_cron_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T004500Z_archive_cron_install.toml`
- note: operator-approved install sequence 2026-11-10 16:27 PT (SW-9)
- ran: 2026-11-11T00:45:21Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_cron_install.py install`

```
SURFACE BUDGET: RED (box HEAD fb84178a, as of 2026-11-11T00:45:14Z)
  exempt (own first-run state): NOT INSTALLED cron|14,44 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNBAPTS
  exempt (own first-run state): NOT INSTALLED cron|17,47 0-5,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNHLGOAL
  exempt (own first-run state): NOT INSTALLED cron|23,53 0-3,17-23 * * *|scripts/archive_market_prices.py --out exp_output/PRICE_ARCHIVE --series KXNFLPASSYDS
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261111T004521Z.bak
  + 14,44 0-5,17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_
  + 17,47 0-5,17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_
  + 23,53 0-3,17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_
INSTALLED: 3 archiver line(s) appended; every prior crontab line preserved

[stderr]
/opt/prediction-market-bot/scripts/archive_cron_install.py:118: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  p = BACKUP_DIR / ("crontab_%s.bak" % dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))

```
