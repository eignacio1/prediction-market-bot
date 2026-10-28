# Box task `archive_cron_install` — 20261028T050324Z_w921_archive_cron_install

- request: `04_EXECUTION/BOX_TASKS/requests/20261028T050324Z_w921_archive_cron_install.toml`
- note: W92.1 install NBA/NHL archive lines
- ran: 2026-10-28T05:03:46Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_cron_install.py install`

```
SURFACE BUDGET: GREEN (box HEAD 4631932d, as of 2026-10-28T05:03:42Z)
BACKUP: /opt/prediction-market-bot/logs/crontab_backups/crontab_20261028T050346Z.bak
  + 8,28,48 17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_ma
  + 8,28,48 0-5   * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_ma
  + 18 12-16 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_
  + 11,31,51 17-23 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_m
  + 11,31,51 0-5   * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_m
  + 21 12-16 * * * cd $PROJ && export $(grep -v '^#' .env | xargs) && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_
INSTALLED: 6 archiver line(s) appended; every prior crontab line preserved

[stderr]
/opt/prediction-market-bot/scripts/archive_cron_install.py:111: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  p = BACKUP_DIR / ("crontab_%s.bak" % dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))

```
