# Box task `evidence_weekly_run` — 20261120T1511Z_evidence_weekly_run

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1511Z_evidence_weekly_run.toml`
- note: W121.1: first weekly look on box rows (after box pull)
- ran: 2026-11-20T15:24:39Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/run_evidence_weekly.py`

```
# Weekly look, cut 2026-11-17T10:00:00Z

Looks scored: [38, 39, 40, 41, 42, 43, 44]
Rows loaded: 140223. Prior: root N(0, 0.1^2); no sportsbook prior; bar 0.9; alpha 0.1; min_inc_games 5.

| series | games | leaves | with an arm | late rows | soonest to arm (weeks) |
|---|---|---|---|---|---|
| MLB|board | 25 | 81 | 0 | 0 | None |
| NBA|board | 205 | 103 | 0 | 0 | None |
| NBA|nba_depth | 0 | 0 | 0 | 0 | None |
| NBA|router_v2 | 0 | 0 | 0 | 0 | None |
| NBA|v1 | 36 | 3 | 0 | 0 | None |
| NFL|board | 101 | 87 | 0 | 0 | None |
| NFL|router_v2 | 0 | 0 | 0 | 0 | None |
| NFL|v1 | 14 | 4 | 0 | 0 | None |
| NHL|board | 311 | 99 | 0 | 0 | 45 |
| NHL|nhl_v2 | 0 | 0 | 0 | 0 | None |
| NHL|router_v2 | 0 | 0 | 0 | 0 | None |
| NHL|v1 | 0 | 0 | 0 | 0 | None |

Earned an arm this look: 0. Routed back to no bet: 0.


E-value leaders (path-averaged e-process; arm needs e >= 1/alpha AND P(net>0) >= bar):
- NHL|board NHL|NHL_MONEYLINE|T3|2|flat MODEL_FADE: e=2.71 P(net>0)=0.2689 mean=-0.00805
- NHL|board NHL|NHL_MONEYLINE|T3|3|flat MODEL_FADE: e=2.63 P(net>0)=0.2639 mean=-0.00833
- NHL|board NHL|NHL_MONEYLINE|T3|2|down MODEL_FADE: e=2.51 P(net>0)=0.2694 mean=-0.00807
- NHL|board NHL|NHL_MONEYLINE|T3|2|na MODEL_FADE: e=2.51 P(net>0)=0.2714 mean=-0.00799
- NHL|board NHL|NHL_MONEYLINE|T3|2|up MODEL_FADE: e=2.51 P(net>0)=0.2675 mean=-0.00814
- MLB|board MLB|MLB_RUN_LINE|T2|2|flat MODEL_FADE: e=1.81 P(net>0)=0.0531 mean=-0.04405
- MLB|board MLB|MLB_MONEYLINE|T3|2|flat MODEL_FADE: e=1.72 P(net>0)=0.0549 mean=-0.04399
- MLB|board MLB|MLB_MONEYLINE|T2|2|down MODEL_FADE: e=1.58 P(net>0)=0.0546 mean=-0.04406
- MLB|board MLB|MLB_MONEYLINE|T2|2|flat MODEL_FADE: e=1.58 P(net>0)=0.0547 mean=-0.04406
- MLB|board MLB|MLB_MONEYLINE|T2|2|na MODEL_FADE: e=1.58 P(net>0)=0.0549 mean=-0.044


```
