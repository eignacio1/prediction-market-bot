# Box task `router_error_read` — 20261124T0554Z_router_error_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261124T0554Z_router_error_read.toml`
- note: W125.2 Part A retry after deploy
- ran: 2026-11-24T05:55:24Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/router_error_read.py`

```
{
 "causes": {
  "ERROR|KeyError": {
   "by_cell": {
    "NBA_NBA_GAME_TOTAL|T1": 666,
    "NBA_NBA_GAME_TOTAL|T2": 1439,
    "NBA_NBA_GAME_TOTAL|T3": 1654,
    "NBA_NBA_SPREAD|T1": 101,
    "NBA_NBA_SPREAD|T2": 262,
    "NBA_NBA_SPREAD|T3": 746,
    "NBA_NBA_TEAM_TOTAL|T3": 440,
    "NFL_NFL_GAME_TOTAL|T2": 25,
    "NFL_NFL_GAME_TOTAL|T3": 85,
    "NFL_NFL_SPREAD|T3": 11,
    "NFL_NFL_TEAM_TOTAL|T3": 85
   },
   "by_sport": {
    "NBA": 5308,
    "NFL": 206
   },
   "example": {
    "reason": "KeyError",
    "ticker": "KXNBATOTAL-26NOV12TORPHI-249",
    "ts": "2026-11-12T06:37:39Z"
   },
   "n": 5514
  },
  "ERROR|KeyError:'<x>'": {
   "by_cell": {
    "NBA_NBA_GAME_TOTAL|T1": 159,
    "NBA_NBA_GAME_TOTAL|T2": 233,
    "NBA_NBA_GAME_TOTAL|T3": 67,
    "NBA_NBA_SPREAD|T1": 33,
    "NBA_NBA_SPREAD|T2": 97,
    "NBA_NBA_SPREAD|T3": 102,
    "NBA_NBA_TEAM_TOTAL|T3": 38,
    "NHL_NHL_GAME_TOTAL|T1": 15,
    "NHL_NHL_MONEYLINE|T2": 20,
    "NHL_NHL_MONEYLINE|T3": 33,
    "NHL_NHL_PUCK_LINE|T1": 5,
    "NHL_NHL_PUCK_LINE|T3": 21
   },
   "by_sport": {
    "NBA": 729,
    "NHL": 97
   },
   "example": {
    "reason": "KeyError:'market_ticker'",
    "ticker": "KXNBASPREAD-26NOV17NYKTOR-TOR9",
    "ts": "2026-11-17T06:11:50Z"
   },
   "n": 826
  },
  "UNROUTED|(no reason logged)": {
   "by_cell": {
    "NHL_NHL_GAME_TOTAL|T1": 351,
    "NHL_NHL_GAME_TOTAL|T2": 2057,
    "NHL_NHL_GAME_TOTAL|T3": 872,
    "NHL_NHL_MONEYLINE|T1": 78,
    "NHL_NHL_MONEYLINE|T2": 488,
    "NHL_NHL_MONEYLINE|T3": 200,
    "NHL_NHL_PUCK_LINE|T1": 156,
    "NHL_NHL_PUCK_LINE|T2": 971,
    "NHL_NHL_PUCK_LINE|T3": 400
   },
   "by_sport": {
    "NHL": 5573
   },
   "example": {
    "reason": "None",
    "ticker": "KXNHLGAME-26NOV13NSHVGK-VGK",
    "ts": "2026-11-12T14:00:45Z"
   },
   "n": 5573
  }
 },
 "per_day": {
  "2026-11-12": {
   "ERROR|KeyError": 478,
   "UNROUTED|(no reason logged)": 1342
  },
  "2026-11-13": {
   "ERROR|KeyError": 1047,
   "UNROUTED|(no reason logged)": 654
  },
  "2026-11-14": {
   "ERROR|KeyError": 1134,
   "UNROUTED|(no reason logged)": 2044
  },
  "2026-11-15": {
   "ERROR|KeyError": 1611,
   "UNROUTED|(no reason logged)": 738
  },
  "2026-11-16": {
   "ERROR|KeyError": 961,
   "UNROUTED|(no reason logged)": 720
  },
  "2026-11-17": {
   "ERROR|KeyError": 283,
   "ERROR|KeyError:'<x>'": 666,
   "UNROUTED|(no reason logged)": 75
  },
  "2026-11-18": {
   "ERROR|KeyError:'<x>'": 160
  }
 },
 "skip_rows_seen": 122563,
 "total_by_arm": {
  "ERROR": 6340,
  "UNROUTED": 5573
 }
}

```
