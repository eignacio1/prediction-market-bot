# Box task `router_error_read` — 20261125T0039Z_router_error_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0039Z_router_error_read.toml`
- note: W126.1 after-merge read (#565)
- ran: 2026-11-25T00:59:29Z on root@157.230.91.33:/opt/prediction-market-bot
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
 "skip_rows_per_day_by_sport": {
  "2026-11-12": {
   "NBA": 3680,
   "NFL": 423,
   "NHL": 1342
  },
  "2026-11-13": {
   "NBA": 10107,
   "NFL": 856,
   "NHL": 654
  },
  "2026-11-14": {
   "NBA": 8672,
   "NFL": 3372,
   "NHL": 2044
  },
  "2026-11-15": {
   "NBA": 10042,
   "NFL": 6449,
   "NHL": 738
  },
  "2026-11-16": {
   "NBA": 9223,
   "NFL": 704,
   "NHL": 720
  },
  "2026-11-17": {
   "NBA": 6548,
   "NFL": 273,
   "NHL": 1616
  },
  "2026-11-18": {
   "NBA": 9667,
   "NFL": 219,
   "NHL": 691
  },
  "2026-11-19": {
   "NBA": 4318,
   "NFL": 510,
   "NHL": 799
  },
  "2026-11-20": {
   "NBA": 7553,
   "NFL": 872,
   "NHL": 282
  },
  "2026-11-21": {
   "NBA": 5287,
   "NFL": 3126,
   "NHL": 653
  },
  "2026-11-22": {
   "NBA": 4796,
   "NFL": 7725,
   "NHL": 367
  },
  "2026-11-23": {
   "NBA": 5753,
   "NFL": 806,
   "NHL": 295
  },
  "2026-11-24": {
   "NBA": 3573,
   "NFL": 659,
   "NHL": 195
  },
  "2026-11-25": {
   "NBA": 687,
   "NFL": 220,
   "NHL": 22
  }
 },
 "skip_rows_seen": 126538,
 "total_by_arm": {
  "ERROR": 6340,
  "UNROUTED": 5573
 }
}

```
