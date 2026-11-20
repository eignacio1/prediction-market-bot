# Box task `capacity_read` — 20261120T1516Z_capacity_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1516Z_capacity_read.toml`
- note: W121.3 B-097: fillable size per cell from logged depth (retry after deploy)
- ran: 2026-11-20T15:17:12Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/capacity_read.py`

```
{
 "as_of_utc": "2026-11-20T15:17:11Z",
 "epoch": "2026-11-06T01:03:42Z",
 "ladder": {
  "files": 0,
  "n_ladder_rows": 0,
  "note": "hours_to_close, NOT to start: the archive stores close_time only. Series: MLB and NFL; no NBA / NHL ladder is captured.",
  "rows": []
 },
 "limits": [
  "ORDERS log the touch size only; ticks 1 / 2 / 3 are measured from the ladder archive (MLB, NFL)",
  "own_touch = queue ahead of a resting order; cross_touch = size a taker meets at the opposite touch"
 ],
 "order_rows": 89885,
 "orders": {
  "cells": [
   {
    "arm": "MODEL_FADE",
    "band": "T1",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 240.84,
       "n": 225,
       "p25": 4.0,
       "p75": 824.2
      },
      "own": {
       "median": 296.89,
       "n": 225,
       "p25": 181.35,
       "p75": 1205.2
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T1|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 240.84,
     "n": 225,
     "p25": 4.0,
     "p75": 824.2
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.23,
     "n": 225,
     "p25": 0.1,
     "p75": 0.57
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 225,
    "opportunities": 225,
    "opportunities_per_day": 25.0,
    "own_touch_contracts": {
     "median": 296.89,
     "n": 225,
     "p25": 181.35,
     "p75": 1205.2
    },
    "sport": "NBA",
    "spread": {
     "median": 0.04,
     "n": 225,
     "p25": 0.03,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 225,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 182.0,
       "n": 5,
       "p25": 6.0,
       "p75": 1187.0
      },
      "own": {
       "median": 1244.89,
       "n": 5,
       "p25": 323.0,
       "p75": 3209.02
      }
     },
     "6-24h": {
      "cross": {
       "median": 219.17,
       "n": 33,
       "p25": 182.0,
       "p75": 1141.18
      },
      "own": {
       "median": 237.24,
       "n": 33,
       "p25": 100.0,
       "p75": 1053.8
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T2|FADE",
    "cross_touch_contracts": {
     "median": 218.47,
     "n": 38,
     "p25": 113.0,
     "p75": 1175.545
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.22,
     "n": 38,
     "p25": 0.095,
     "p75": 0.29
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 38,
    "opportunities": 245,
    "opportunities_per_day": 27.222,
    "own_touch_contracts": {
     "median": 293.375,
     "n": 38,
     "p25": 100.0,
     "p75": 1129.84
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 38,
     "p25": 0.02,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 38,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 759.175,
       "n": 28,
       "p25": 5.75,
       "p75": 1367.51
      },
      "own": {
       "median": 182.0,
       "n": 28,
       "p25": 5.75,
       "p75": 431.385
      }
     },
     "6-24h": {
      "cross": {
       "median": 274.075,
       "n": 46,
       "p25": 182.0,
       "p75": 1687.9575
      },
      "own": {
       "median": 201.64,
       "n": 46,
       "p25": 61.25,
       "p75": 758.5125
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T2|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 284.0,
     "n": 74,
     "p25": 89.98,
     "p75": 1663.53
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.49,
     "n": 74,
     "p25": 0.13,
     "p75": 0.79
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 74,
    "opportunities": 166,
    "opportunities_per_day": 18.444,
    "own_touch_contracts": {
     "median": 183.5,
     "n": 74,
     "p25": 33.48,
     "p75": 758.5125
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 74,
     "p25": 0.02,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 74,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 841.13,
       "n": 49,
       "p25": 182.0,
       "p75": 3929.2
      },
      "own": {
       "median": 1822.43,
       "n": 49,
       "p25": 370.52,
       "p75": 4236.0
      }
     },
     "6-24h": {
      "cross": {
       "median": 568.23,
       "n": 17,
       "p25": 183.0,
       "p75": 3097.71
      },
      "own": {
       "median": 495.69,
       "n": 17,
       "p25": 182.0,
       "p75": 1399.2
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T2|MOMENTUM",
    "cross_touch_contracts": {
     "median": 727.4,
     "n": 66,
     "p25": 182.0,
     "p75": 3732.3125
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.525,
     "n": 66,
     "p25": 0.3,
     "p75": 0.65
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 66,
    "opportunities": 262,
    "opportunities_per_day": 29.111,
    "own_touch_contracts": {
     "median": 1485.1,
     "n": 66,
     "p25": 211.0825,
     "p75": 3633.5425
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 66,
     "p25": 0.01,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 66,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 182.0,
       "n": 23,
       "p25": 5.0,
       "p75": 4181.055
      },
      "own": {
       "median": 6.0,
       "n": 23,
       "p25": 2.5,
       "p75": 206.395
      }
     },
     "6-24h": {
      "cross": {
       "median": 1971.37,
       "n": 16,
       "p25": 151.6125,
       "p75": 4141.75
      },
      "own": {
       "median": 211.73,
       "n": 16,
       "p25": 39.0,
       "p75": 368.655
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T2|RIDE",
    "cross_touch_contracts": {
     "median": 1253.0,
     "n": 39,
     "p25": 44.5,
     "p75": 4181.055
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.87,
     "n": 39,
     "p25": 0.83,
     "p75": 0.9
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 39,
    "opportunities": 180,
    "opportunities_per_day": 20.0,
    "own_touch_contracts": {
     "median": 121.0,
     "n": 39,
     "p25": 4.5,
     "p75": 242.0
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 39,
     "p25": 0.02,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 39,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 244.5,
       "n": 6,
       "p25": 132.9125,
       "p75": 585.1675
      },
      "own": {
       "median": 480.0,
       "n": 6,
       "p25": 183.5,
       "p75": 579.25
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T3|FADE",
    "cross_touch_contracts": {
     "median": 244.5,
     "n": 6,
     "p25": 132.9125,
     "p75": 585.1675
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.27,
     "n": 14,
     "p25": 0.2225,
     "p75": 0.3
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 14,
    "opportunities": 86,
    "opportunities_per_day": 9.556,
    "own_touch_contracts": {
     "median": 480.0,
     "n": 6,
     "p25": 183.5,
     "p75": 579.25
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 6,
     "p25": 0.0225,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 14,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 1546.685,
       "n": 16,
       "p25": 306.25,
       "p75": 2561.0
      },
      "own": {
       "median": 316.0,
       "n": 16,
       "p25": 197.19,
       "p75": 764.35
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T3|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 1546.685,
     "n": 16,
     "p25": 306.25,
     "p75": 2561.0
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.595,
     "n": 16,
     "p25": 0.3,
     "p75": 0.8475
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 16,
    "opportunities": 182,
    "opportunities_per_day": 20.222,
    "own_touch_contracts": {
     "median": 316.0,
     "n": 16,
     "p25": 197.19,
     "p75": 764.35
    },
    "sport": "NBA",
    "spread": {
     "median": 0.01,
     "n": 16,
     "p25": 0.01,
     "p75": 0.0225
    },
    "stake_usd": {
     "median": 1.0,
     "n": 16,
     "p25": 0.95,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 278.28,
       "n": 14,
       "p25": 120.865,
       "p75": 625.7
      },
      "own": {
       "median": 331.0,
       "n": 14,
       "p25": 99.35,
       "p75": 751.08
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": 278.28,
     "n": 14,
     "p25": 120.865,
     "p75": 625.7
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.78,
     "n": 35,
     "p25": 0.21,
     "p75": 0.895
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 35,
    "opportunities": 262,
    "opportunities_per_day": 29.111,
    "own_touch_contracts": {
     "median": 331.0,
     "n": 14,
     "p25": 99.35,
     "p75": 751.08
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 14,
     "p25": 0.0125,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 35,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 1044.0,
       "n": 7,
       "p25": 986.0,
       "p75": 1292.67
      },
      "own": {
       "median": 426.12,
       "n": 7,
       "p25": 208.005,
       "p75": 936.815
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_GAME_TOTAL|T3|RIDE",
    "cross_touch_contracts": {
     "median": 1044.0,
     "n": 7,
     "p25": 986.0,
     "p75": 1292.67
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.7,
     "n": 20,
     "p25": 0.645,
     "p75": 0.75
    },
    "market_type": "NBA_GAME_TOTAL",
    "n_orders": 20,
    "opportunities": 249,
    "opportunities_per_day": 27.667,
    "own_touch_contracts": {
     "median": 426.12,
     "n": 7,
     "p25": 208.005,
     "p75": 936.815
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 7,
     "p25": 0.03,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 20,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T1",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 70.67,
       "n": 16,
       "p25": 1.0,
       "p75": 293.135
      },
      "own": {
       "median": 415.885,
       "n": 16,
       "p25": 306.605,
       "p75": 3750.6475
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T1|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 70.67,
     "n": 16,
     "p25": 1.0,
     "p75": 293.135
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.245,
     "n": 16,
     "p25": 0.0925,
     "p75": 0.4975
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 16,
    "opportunities": 16,
    "opportunities_per_day": 1.778,
    "own_touch_contracts": {
     "median": 415.885,
     "n": 16,
     "p25": 306.605,
     "p75": 3750.6475
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 16,
     "p25": 0.02,
     "p75": 0.0325
    },
    "stake_usd": {
     "median": 1.0,
     "n": 16,
     "p25": 0.975,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T1",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 1998.0,
       "n": 50,
       "p25": 365.4975,
       "p75": 5120.0175
      },
      "own": {
       "median": 474.895,
       "n": 50,
       "p25": 311.775,
       "p75": 639.195
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T1|RIDE",
    "cross_touch_contracts": {
     "median": 1998.0,
     "n": 50,
     "p25": 365.4975,
     "p75": 5120.0175
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.71,
     "n": 85,
     "p25": 0.59,
     "p75": 0.89
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 85,
    "opportunities": 343,
    "opportunities_per_day": 38.111,
    "own_touch_contracts": {
     "median": 474.895,
     "n": 50,
     "p25": 311.775,
     "p75": 639.195
    },
    "sport": "NBA",
    "spread": {
     "median": 0.03,
     "n": 50,
     "p25": 0.02,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 85,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 1019.5,
       "n": 48,
       "p25": 273.75,
       "p75": 1820.47
      },
      "own": {
       "median": 812.03,
       "n": 48,
       "p25": 177.75,
       "p75": 2354.0
      }
     },
     "6-24h": {
      "cross": {
       "median": 492.2,
       "n": 69,
       "p25": 188.29,
       "p75": 2406.25
      },
      "own": {
       "median": 1672.0,
       "n": 69,
       "p25": 242.0,
       "p75": 6825.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T2|FADE",
    "cross_touch_contracts": {
     "median": 608.34,
     "n": 117,
     "p25": 242.0,
     "p75": 1896.2
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.295,
     "n": 126,
     "p25": 0.13,
     "p75": 0.3975
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 126,
    "opportunities": 452,
    "opportunities_per_day": 50.222,
    "own_touch_contracts": {
     "median": 893.29,
     "n": 117,
     "p25": 242.0,
     "p75": 5429.79
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 117,
     "p25": 0.01,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 126,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T2",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 428.68,
       "n": 27,
       "p25": 295.28,
       "p75": 1223.005
      },
      "own": {
       "median": 302.0,
       "n": 27,
       "p25": 111.0,
       "p75": 1054.2
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T2|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 428.68,
     "n": 27,
     "p25": 295.28,
     "p75": 1223.005
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.45,
     "n": 27,
     "p25": 0.195,
     "p75": 0.655
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 27,
    "opportunities": 32,
    "opportunities_per_day": 3.556,
    "own_touch_contracts": {
     "median": 302.0,
     "n": 27,
     "p25": 111.0,
     "p75": 1054.2
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 27,
     "p25": 0.015,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 27,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 1241.5,
       "n": 70,
       "p25": 669.36,
       "p75": 2221.49
      },
      "own": {
       "median": 925.05,
       "n": 70,
       "p25": 166.25,
       "p75": 3413.1725
      }
     },
     "6-24h": {
      "cross": {
       "median": 661.23,
       "n": 32,
       "p25": 242.0,
       "p75": 5825.285
      },
      "own": {
       "median": 897.56,
       "n": 32,
       "p25": 227.0,
       "p75": 7000.06
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T2|MOMENTUM",
    "cross_touch_contracts": {
     "median": 1086.255,
     "n": 102,
     "p25": 426.23,
     "p75": 2374.95
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.33,
     "n": 105,
     "p25": 0.19,
     "p75": 0.52
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 105,
    "opportunities": 578,
    "opportunities_per_day": 64.222,
    "own_touch_contracts": {
     "median": 925.05,
     "n": 102,
     "p25": 182.0,
     "p75": 3861.4425
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 102,
     "p25": 0.01,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 105,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 105.0,
       "n": 25,
       "p25": 6.0,
       "p75": 1703.0
      },
      "own": {
       "median": 343.27,
       "n": 25,
       "p25": 107.0,
       "p75": 401.64
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T2|RIDE",
    "cross_touch_contracts": {
     "median": 105.0,
     "n": 25,
     "p25": 6.0,
     "p75": 1703.0
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.78,
     "n": 152,
     "p25": 0.6375,
     "p75": 0.91
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 152,
    "opportunities": 353,
    "opportunities_per_day": 39.222,
    "own_touch_contracts": {
     "median": 343.27,
     "n": 25,
     "p25": 107.0,
     "p75": 401.64
    },
    "sport": "NBA",
    "spread": {
     "median": 0.01,
     "n": 25,
     "p25": 0.01,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 152,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 1695.0,
       "n": 95,
       "p25": 655.505,
       "p75": 2123.375
      },
      "own": {
       "median": 1147.0,
       "n": 95,
       "p25": 65.0,
       "p75": 2277.6
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T3|FADE",
    "cross_touch_contracts": {
     "median": 1695.0,
     "n": 95,
     "p25": 655.505,
     "p75": 2123.375
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.06,
     "n": 159,
     "p25": 0.03,
     "p75": 0.105
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 159,
    "opportunities": 548,
    "opportunities_per_day": 60.889,
    "own_touch_contracts": {
     "median": 1147.0,
     "n": 95,
     "p25": 65.0,
     "p75": 2277.6
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 95,
     "p25": 0.01,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 0.55,
     "n": 159,
     "p25": 0.325,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 26994.19,
       "n": 22,
       "p25": 1540.84,
       "p75": 37790.9175
      },
      "own": {
       "median": 10660.81,
       "n": 22,
       "p25": 1217.465,
       "p75": 57300.6375
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T3|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 26994.19,
     "n": 22,
     "p25": 1540.84,
     "p75": 37790.9175
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.47,
     "n": 22,
     "p25": 0.395,
     "p75": 0.5425
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 22,
    "opportunities": 85,
    "opportunities_per_day": 9.444,
    "own_touch_contracts": {
     "median": 10660.81,
     "n": 22,
     "p25": 1217.465,
     "p75": 57300.6375
    },
    "sport": "NBA",
    "spread": {
     "median": 0.01,
     "n": 22,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 22,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 2835.205,
       "n": 4,
       "p25": 2409.9275,
       "p75": 5844.085
      },
      "own": {
       "median": 1870.015,
       "n": 4,
       "p25": 423.5,
       "p75": 8808.76
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": 2835.205,
     "n": 4,
     "p25": 2409.9275,
     "p75": 5844.085
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.645,
     "n": 28,
     "p25": 0.2825,
     "p75": 0.6925
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 28,
    "opportunities": 201,
    "opportunities_per_day": 22.333,
    "own_touch_contracts": {
     "median": 1870.015,
     "n": 4,
     "p25": 423.5,
     "p75": 8808.76
    },
    "sport": "NBA",
    "spread": {
     "median": 0.01,
     "n": 4,
     "p25": 0.01,
     "p75": 0.0125
    },
    "stake_usd": {
     "median": 1.0,
     "n": 28,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_SPREAD|T3|RIDE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.64,
     "n": 7,
     "p25": 0.565,
     "p75": 0.76
    },
    "market_type": "NBA_SPREAD",
    "n_orders": 7,
    "opportunities": 241,
    "opportunities_per_day": 26.778,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NBA",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 7,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 1.0,
       "n": 52,
       "p25": 1.0,
       "p75": 5.0
      },
      "own": {
       "median": 6.0,
       "n": 52,
       "p25": 5.0,
       "p75": 130.0
      }
     },
     "6-24h": {
      "cross": {
       "median": 7.0,
       "n": 22,
       "p25": 5.0,
       "p75": 165.0
      },
      "own": {
       "median": 5.0,
       "n": 22,
       "p25": 1.25,
       "p75": 105.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_TEAM_TOTAL|T2|FADE",
    "cross_touch_contracts": {
     "median": 5.0,
     "n": 74,
     "p25": 1.0,
     "p75": 6.75
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.09,
     "n": 87,
     "p25": 0.065,
     "p75": 0.135
    },
    "market_type": "NBA_TEAM_TOTAL",
    "n_orders": 87,
    "opportunities": 474,
    "opportunities_per_day": 52.667,
    "own_touch_contracts": {
     "median": 5.0,
     "n": 74,
     "p25": 3.5,
     "p75": 128.0
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 74,
     "p25": 0.02,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 87,
     "p25": 0.7,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 207.5,
       "n": 38,
       "p25": 29.4225,
       "p75": 641.905
      },
      "own": {
       "median": 201.0,
       "n": 38,
       "p25": 120.0,
       "p75": 557.6925
      }
     },
     "6-24h": {
      "cross": {
       "median": 398.69,
       "n": 15,
       "p25": 42.5,
       "p75": 482.635
      },
      "own": {
       "median": 211.0,
       "n": 15,
       "p25": 120.5,
       "p75": 320.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_TEAM_TOTAL|T2|MOMENTUM",
    "cross_touch_contracts": {
     "median": 250.0,
     "n": 53,
     "p25": 25.0,
     "p75": 549.22
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.545,
     "n": 58,
     "p25": 0.39,
     "p75": 0.6775
    },
    "market_type": "NBA_TEAM_TOTAL",
    "n_orders": 58,
    "opportunities": 534,
    "opportunities_per_day": 59.333,
    "own_touch_contracts": {
     "median": 201.0,
     "n": 53,
     "p25": 120.0,
     "p75": 486.0
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 53,
     "p25": 0.02,
     "p75": 0.02
    },
    "stake_usd": {
     "median": 1.0,
     "n": 58,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 60.0,
       "n": 37,
       "p25": 5.0,
       "p75": 250.0
      },
      "own": {
       "median": 1.0,
       "n": 37,
       "p25": 1.0,
       "p75": 14.0
      }
     },
     "6-24h": {
      "cross": {
       "median": 60.0,
       "n": 23,
       "p25": 5.0,
       "p75": 60.0
      },
      "own": {
       "median": 4.01,
       "n": 23,
       "p25": 1.0,
       "p75": 148.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_TEAM_TOTAL|T2|RIDE",
    "cross_touch_contracts": {
     "median": 60.0,
     "n": 60,
     "p25": 5.0,
     "p75": 70.0
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.88,
     "n": 65,
     "p25": 0.84,
     "p75": 0.92
    },
    "market_type": "NBA_TEAM_TOTAL",
    "n_orders": 65,
    "opportunities": 492,
    "opportunities_per_day": 54.667,
    "own_touch_contracts": {
     "median": 1.5,
     "n": 60,
     "p25": 1.0,
     "p75": 122.0
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 60,
     "p25": 0.02,
     "p75": 0.03
    },
    "stake_usd": {
     "median": 1.0,
     "n": 65,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 250.0,
       "n": 36,
       "p25": 100.0,
       "p75": 2000.0
      },
      "own": {
       "median": 236.5,
       "n": 36,
       "p25": 35.0,
       "p75": 542.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_TEAM_TOTAL|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": 250.0,
     "n": 36,
     "p25": 100.0,
     "p75": 2000.0
    },
    "days_sport_logged": 9,
    "entry_price": {
     "median": 0.49,
     "n": 77,
     "p25": 0.4,
     "p75": 0.58
    },
    "market_type": "NBA_TEAM_TOTAL",
    "n_orders": 77,
    "opportunities": 354,
    "opportunities_per_day": 39.333,
    "own_touch_contracts": {
     "median": 236.5,
     "n": 36,
     "p25": 35.0,
     "p75": 542.0
    },
    "sport": "NBA",
    "spread": {
     "median": 0.02,
     "n": 36,
     "p25": 0.01,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 77,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NBA|NBA_TEAM_TOTAL|T3|RIDE",
    "cross_touch_contracts": {
   

[... 2163 bytes cut ...]

945,
     "n": 10,
     "p25": 0.8975,
     "p75": 0.95
    },
    "market_type": "NFL_GAME_TOTAL",
    "n_orders": 10,
    "opportunities": 104,
    "opportunities_per_day": 17.333,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 10,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_GAME_TOTAL|T3|FADE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.45,
     "n": 5,
     "p25": 0.41,
     "p75": 0.47
    },
    "market_type": "NFL_GAME_TOTAL",
    "n_orders": 5,
    "opportunities": 63,
    "opportunities_per_day": 10.5,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 5,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_GAME_TOTAL|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.11,
     "n": 1,
     "p25": 0.11,
     "p75": 0.11
    },
    "market_type": "NFL_GAME_TOTAL",
    "n_orders": 1,
    "opportunities": 72,
    "opportunities_per_day": 12.0,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 1,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_GAME_TOTAL|T3|RIDE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.54,
     "n": 6,
     "p25": 0.525,
     "p75": 0.5475
    },
    "market_type": "NFL_GAME_TOTAL",
    "n_orders": 6,
    "opportunities": 65,
    "opportunities_per_day": 10.833,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 6,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T1",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_SPREAD|T1|RIDE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.87,
     "n": 15,
     "p25": 0.835,
     "p75": 0.885
    },
    "market_type": "NFL_SPREAD",
    "n_orders": 15,
    "opportunities": 143,
    "opportunities_per_day": 23.833,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 15,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_SPREAD|T3|FADE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.41,
     "n": 5,
     "p25": 0.38,
     "p75": 0.43
    },
    "market_type": "NFL_SPREAD",
    "n_orders": 5,
    "opportunities": 91,
    "opportunities_per_day": 15.167,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 5,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_SPREAD|T3|RIDE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.865,
     "n": 10,
     "p25": 0.8225,
     "p75": 0.9225
    },
    "market_type": "NFL_SPREAD",
    "n_orders": 10,
    "opportunities": 157,
    "opportunities_per_day": 26.167,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 10,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NFL|NFL_TEAM_TOTAL|T3|RIDE",
    "cross_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "days_sport_logged": 6,
    "entry_price": {
     "median": 0.945,
     "n": 6,
     "p25": 0.925,
     "p75": 0.965
    },
    "market_type": "NFL_TEAM_TOTAL",
    "n_orders": 6,
    "opportunities": 192,
    "opportunities_per_day": 32.0,
    "own_touch_contracts": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "sport": "NFL",
    "spread": {
     "median": null,
     "n": 0,
     "p25": null,
     "p75": null
    },
    "stake_usd": {
     "median": 1.0,
     "n": 6,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T1",
    "by_hours_to_start": {
     "24h+": {
      "cross": {
       "median": 9.47,
       "n": 28,
       "p25": 2.75,
       "p75": 427.0
      },
      "own": {
       "median": 150.0,
       "n": 28,
       "p25": 6.675,
       "p75": 1019.5
      }
     },
     "6-24h": {
      "cross": {
       "median": 6158.63,
       "n": 1,
       "p25": 6158.63,
       "p75": 6158.63
      },
      "own": {
       "median": 2223.31,
       "n": 1,
       "p25": 2223.31,
       "p75": 2223.31
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T1|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 10.0,
     "n": 29,
     "p25": 3.0,
     "p75": 682.0
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.13,
     "n": 29,
     "p25": 0.1,
     "p75": 0.17
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 29,
    "opportunities": 29,
    "opportunities_per_day": 7.25,
    "own_touch_contracts": {
     "median": 150.0,
     "n": 29,
     "p25": 7.0,
     "p75": 1024.0
    },
    "sport": "NHL",
    "spread": {
     "median": 0.04,
     "n": 29,
     "p25": 0.03,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 29,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T1",
    "by_hours_to_start": {
     "24h+": {
      "cross": {
       "median": 682.0,
       "n": 45,
       "p25": 75.0,
       "p75": 1102.0
      },
      "own": {
       "median": 746.39,
       "n": 45,
       "p25": 682.0,
       "p75": 1074.0
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T1|RIDE",
    "cross_touch_contracts": {
     "median": 682.0,
     "n": 45,
     "p25": 75.0,
     "p75": 1102.0
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.79,
     "n": 45,
     "p25": 0.72,
     "p75": 0.9
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 45,
    "opportunities": 45,
    "opportunities_per_day": 11.25,
    "own_touch_contracts": {
     "median": 746.39,
     "n": 45,
     "p25": 682.0,
     "p75": 1074.0
    },
    "sport": "NHL",
    "spread": {
     "median": 0.04,
     "n": 45,
     "p25": 0.03,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 45,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 1.5,
       "n": 6,
       "p25": 1.0,
       "p75": 375.5
      },
      "own": {
       "median": 5629.3,
       "n": 6,
       "p25": 3732.5,
       "p75": 8653.9125
      }
     },
     "6-24h": {
      "cross": {
       "median": 3389.49,
       "n": 15,
       "p25": 478.5,
       "p75": 3594.25
      },
      "own": {
       "median": 2798.0,
       "n": 15,
       "p25": 1038.735,
       "p75": 3833.365
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T2|FADE",
    "cross_touch_contracts": {
     "median": 910.0,
     "n": 21,
     "p25": 2.0,
     "p75": 3549.5
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.24,
     "n": 21,
     "p25": 0.21,
     "p75": 0.26
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 21,
    "opportunities": 60,
    "opportunities_per_day": 15.0,
    "own_touch_contracts": {
     "median": 3119.53,
     "n": 21,
     "p25": 1160.47,
     "p75": 5631.6
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 21,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 21,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T2",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 7884.76,
       "n": 4,
       "p25": 6686.8975,
       "p75": 10348.4625
      },
      "own": {
       "median": 1466.3,
       "n": 4,
       "p25": 907.0,
       "p75": 5201.595
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T2|MOMENTUM",
    "cross_touch_contracts": {
     "median": 7884.76,
     "n": 4,
     "p25": 6686.8975,
     "p75": 10348.4625
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.5,
     "n": 4,
     "p25": 0.4375,
     "p75": 0.5625
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 4,
    "opportunities": 15,
    "opportunities_per_day": 3.75,
    "own_touch_contracts": {
     "median": 1466.3,
     "n": 4,
     "p25": 907.0,
     "p75": 5201.595
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 4,
     "p25": 0.01,
     "p75": 0.0125
    },
    "stake_usd": {
     "median": 1.0,
     "n": 4,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 6722.15,
       "n": 15,
       "p25": 3850.605,
       "p75": 12886.78
      },
      "own": {
       "median": 3000.0,
       "n": 15,
       "p25": 496.0,
       "p75": 5242.645
      }
     },
     "6-24h": {
      "cross": {
       "median": 2260.96,
       "n": 89,
       "p25": 909.0,
       "p75": 4825.5
      },
      "own": {
       "median": 910.0,
       "n": 89,
       "p25": 5.0,
       "p75": 3408.07
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T2|RIDE",
    "cross_touch_contracts": {
     "median": 2618.925,
     "n": 104,
     "p25": 909.0,
     "p75": 6871.91
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.85,
     "n": 104,
     "p25": 0.6325,
     "p75": 0.9325
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 104,
    "opportunities": 275,
    "opportunities_per_day": 68.75,
    "own_touch_contracts": {
     "median": 910.0,
     "n": 104,
     "p25": 35.25,
     "p75": 3628.2475
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 104,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 104,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 783.76,
       "n": 1,
       "p25": 783.76,
       "p75": 783.76
      },
      "own": {
       "median": 399.0,
       "n": 1,
       "p25": 399.0,
       "p75": 399.0
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": 783.76,
     "n": 1,
     "p25": 783.76,
     "p75": 783.76
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.67,
     "n": 1,
     "p25": 0.67,
     "p75": 0.67
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 1,
    "opportunities": 4,
    "opportunities_per_day": 1.0,
    "own_touch_contracts": {
     "median": 399.0,
     "n": 1,
     "p25": 399.0,
     "p75": 399.0
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 1,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 1,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 2636.5,
       "n": 5,
       "p25": 1484.22,
       "p75": 2791.0
      },
      "own": {
       "median": 414.0,
       "n": 5,
       "p25": 399.0,
       "p75": 585.0
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NHL|NHL_GAME_TOTAL|T3|RIDE",
    "cross_touch_contracts": {
     "median": 2636.5,
     "n": 5,
     "p25": 1484.22,
     "p75": 2791.0
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.895,
     "n": 24,
     "p25": 0.875,
     "p75": 0.96
    },
    "market_type": "NHL_GAME_TOTAL",
    "n_orders": 24,
    "opportunities": 126,
    "opportunities_per_day": 31.5,
    "own_touch_contracts": {
     "median": 414.0,
     "n": 5,
     "p25": 399.0,
     "p75": 585.0
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 5,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 24,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 3636.08,
       "n": 1,
       "p25": 3636.08,
       "p75": 3636.08
      },
      "own": {
       "median": 18415.22,
       "n": 1,
       "p25": 18415.22,
       "p75": 18415.22
      }
     },
     "6-24h": {
      "cross": {
       "median": 36673.33,
       "n": 5,
       "p25": 8494.0,
       "p75": 117071.17
      },
      "own": {
       "median": 13216.75,
       "n": 5,
       "p25": 4733.28,
       "p75": 79715.82
      }
     }
    },
    "cell": "NHL|NHL_MONEYLINE|T2|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 22583.665,
     "n": 6,
     "p25": 4850.56,
     "p75": 96971.71
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.47,
     "n": 6,
     "p25": 0.41,
     "p75": 0.4775
    },
    "market_type": "NHL_MONEYLINE",
    "n_orders": 6,
    "opportunities": 10,
    "opportunities_per_day": 2.5,
    "own_touch_contracts": {
     "median": 15815.985,
     "n": 6,
     "p25": 6854.1475,
     "p75": 64390.67
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 6,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 6,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 122044.075,
       "n": 6,
       "p25": 44578.8125,
       "p75": 203834.175
      },
      "own": {
       "median": 90714.63,
       "n": 6,
       "p25": 26507.015,
       "p75": 116532.19
      }
     },
     "6-24h": {
      "cross": {
       "median": 14421.335,
       "n": 24,
       "p25": 3560.99,
       "p75": 91584.3125
      },
      "own": {
       "median": 20742.71,
       "n": 24,
       "p25": 4810.1375,
       "p75": 89174.1325
      }
     }
    },
    "cell": "NHL|NHL_MONEYLINE|T2|RIDE",
    "cross_touch_contracts": {
     "median": 28040.665,
     "n": 30,
     "p25": 6390.025,
     "p75": 126408.005
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.56,
     "n": 30,
     "p25": 0.51,
     "p75": 0.6
    },
    "market_type": "NHL_MONEYLINE",
    "n_orders": 30,
    "opportunities": 75,
    "opportunities_per_day": 18.75,
    "own_touch_contracts": {
     "median": 25531.605,
     "n": 30,
     "p25": 5209.695,
     "p75": 95522.425
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 30,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 30,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 38612.51,
       "n": 5,
       "p25": 11375.81,
       "p75": 114333.64
      },
      "own": {
       "median": 44909.87,
       "n": 5,
       "p25": 26020.11,
       "p75": 109232.47
      }
     }
    },
    "cell": "NHL|NHL_MONEYLINE|T3|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 38612.51,
     "n": 5,
     "p25": 11375.81,
     "p75": 114333.64
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.48,
     "n": 5,
     "p25": 0.31,
     "p75": 0.48
    },
    "market_type": "NHL_MONEYLINE",
    "n_orders": 5,
    "opportunities": 24,
    "opportunities_per_day": 6.0,
    "own_touch_contracts": {
     "median": 44909.87,
     "n": 5,
     "p25": 26020.11,
     "p75": 109232.47
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 5,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 5,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T1",
    "by_hours_to_start": {
     "24h+": {
      "cross": {
       "median": 11.0,
       "n": 19,
       "p25": 4.0,
       "p75": 723.5
      },
      "own": {
       "median": 15.0,
       "n": 19,
       "p25": 6.5,
       "p75": 682.0
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T1|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 11.0,
     "n": 19,
     "p25": 4.0,
     "p75": 723.5
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.84,
     "n": 19,
     "p25": 0.81,
     "p75": 0.85
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 19,
    "opportunities": 19,
    "opportunities_per_day": 4.75,
    "own_touch_contracts": {
     "median": 15.0,
     "n": 19,
     "p25": 6.5,
     "p75": 682.0
    },
    "sport": "NHL",
    "spread": {
     "median": 0.03,
     "n": 19,
     "p25": 0.03,
     "p75": 0.04
    },
    "stake_usd": {
     "median": 1.0,
     "n": 19,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 36065.56,
       "n": 1,
       "p25": 36065.56,
       "p75": 36065.56
      },
      "own": {
       "median": 24943.91,
       "n": 1,
       "p25": 24943.91,
       "p75": 24943.91
      }
     },
     "6-24h": {
      "cross": {
       "median": 16281.39,
       "n": 5,
       "p25": 2177.29,
       "p75": 17292.05
      },
      "own": {
       "median": 633.0,
       "n": 5,
       "p25": 294.97,
       "p75": 1508.0
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T2|FADE",
    "cross_touch_contracts": {
     "median": 16786.72,
     "n": 6,
     "p25": 5703.315,
     "p75": 17653.97
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.385,
     "n": 6,
     "p25": 0.3725,
     "p75": 0.42
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 6,
    "opportunities": 14,
    "opportunities_per_day": 3.5,
    "own_touch_contracts": {
     "median": 1070.5,
     "n": 6,
     "p25": 379.4775,
     "p75": 19084.9325
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 6,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 6,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T2",
    "by_hours_to_start": {
     "6-24h": {
      "cross": {
       "median": 5264.2,
       "n": 1,
       "p25": 5264.2,
       "p75": 5264.2
      },
      "own": {
       "median": 516.33,
       "n": 1,
       "p25": 516.33,
       "p75": 516.33
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T2|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 5264.2,
     "n": 1,
     "p25": 5264.2,
     "p75": 5264.2
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.91,
     "n": 1,
     "p25": 0.91,
     "p75": 0.91
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 1,
    "opportunities": 2,
    "opportunities_per_day": 0.5,
    "own_touch_contracts": {
     "median": 516.33,
     "n": 1,
     "p25": 516.33,
     "p75": 516.33
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 1,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 1,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 5087.88,
       "n": 6,
       "p25": 4428.3125,
       "p75": 14231.515
      },
      "own": {
       "median": 14771.76,
       "n": 6,
       "p25": 8986.955,
       "p75": 17012.845
      }
     },
     "6-24h": {
      "cross": {
       "median": 2907.18,
       "n": 13,
       "p25": 2144.0,
       "p75": 8060.8
      },
      "own": {
       "median": 1852.0,
       "n": 13,
       "p25": 983.62,
       "p75": 7807.0
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T2|MOMENTUM",
    "cross_touch_contracts": {
     "median": 4335.48,
     "n": 19,
     "p25": 2465.365,
     "p75": 8440.73
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.29,
     "n": 19,
     "p25": 0.22,
     "p75": 0.665
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 19,
    "opportunities": 30,
    "opportunities_per_day": 7.5,
    "own_touch_contracts": {
     "median": 2945.95,
     "n": 19,
     "p25": 1449.3,
     "p75": 11732.705
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 19,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 19,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "RIDE",
    "band": "T2",
    "by_hours_to_start": {
     "2-6h": {
      "cross": {
       "median": 13659.265,
       "n": 4,
       "p25": 13440.4375,
       "p75": 20841.2675
      },
      "own": {
       "median": 1550.095,
       "n": 4,
       "p25": 1498.0525,
       "p75": 10188.625
      }
     },
     "6-24h": {
      "cross": {
       "median": 31107.54,
       "n": 1,
       "p25": 31107.54,
       "p75": 31107.54
      },
      "own": {
       "median": 632.6,
       "n": 1,
       "p25": 632.6,
       "p75": 632.6
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T2|RIDE",
    "cross_touch_contracts": {
     "median": 13735.32,
     "n": 5,
     "p25": 13583.21,
     "p75": 31107.54
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.74,
     "n": 5,
     "p25": 0.7,
     "p75": 0.77
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 5,
    "opportunities": 17,
    "opportunities_per_day": 4.25,
    "own_touch_contracts": {
     "median": 1519.6,
     "n": 5,
     "p25": 1433.41,
     "p75": 1580.59
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 5,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 5,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 57934.77,
       "n": 1,
       "p25": 57934.77,
       "p75": 57934.77
      },
      "own": {
       "median": 33879.26,
       "n": 1,
       "p25": 33879.26,
       "p75": 33879.26
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T3|FADE",
    "cross_touch_contracts": {
     "median": 57934.77,
     "n": 1,
     "p25": 57934.77,
     "p75": 57934.77
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.36,
     "n": 3,
     "p25": 0.355,
     "p75": 0.39
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 3,
    "opportunities": 9,
    "opportunities_per_day": 2.25,
    "own_touch_contracts": {
     "median": 33879.26,
     "n": 1,
     "p25": 33879.26,
     "p75": 33879.26
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 1,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 3,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MODEL_FADE",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 14805.245,
       "n": 4,
       "p25": 10858.2125,
       "p75": 16751.655
      },
      "own": {
       "median": 6600.1,
       "n": 4,
       "p25": 4516.85,
       "p75": 11561.615
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T3|MODEL_FADE",
    "cross_touch_contracts": {
     "median": 14805.245,
     "n": 4,
     "p25": 10858.2125,
     "p75": 16751.655
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.87,
     "n": 4,
     "p25": 0.695,
     "p75": 0.87
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 4,
    "opportunities": 13,
    "opportunities_per_day": 3.25,
    "own_touch_contracts": {
     "median": 6600.1,
     "n": 4,
     "p25": 4516.85,
     "p75": 11561.615
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 4,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 4,
     "p25": 1.0,
     "p75": 1.0
    }
   },
   {
    "arm": "MOMENTUM",
    "band": "T3",
    "by_hours_to_start": {
     "0-2h": {
      "cross": {
       "median": 15724.27,
       "n": 2,
       "p25": 12173.6,
       "p75": 19274.94
      },
      "own": {
       "median": 4055.725,
       "n": 2,
       "p25": 2477.3675,
       "p75": 5634.0825
      }
     },
     "unknown": {
      "cross": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      },
      "own": {
       "median": null,
       "n": 0,
       "p25": null,
       "p75": null
      }
     }
    },
    "cell": "NHL|NHL_PUCK_LINE|T3|MOMENTUM",
    "cross_touch_contracts": {
     "median": 15724.27,
     "n": 2,
     "p25": 12173.6,
     "p75": 19274.94
    },
    "days_sport_logged": 4,
    "entry_price": {
     "median": 0.29,
     "n": 3,
     "p25": 0.245,
     "p75": 0.31
    },
    "market_type": "NHL_PUCK_LINE",
    "n_orders": 3,
    "opportunities": 6,
    "opportunities_per_day": 1.5,
    "own_touch_contracts": {
     "median": 4055.725,
     "n": 2,
     "p25": 2477.3675,
     "p75": 5634.0825
    },
    "sport": "NHL",
    "spread": {
     "median": 0.01,
     "n": 2,
     "p25": 0.01,
     "p75": 0.01
    },
    "stake_usd": {
     "median": 1.0,
     "n": 3,
     "p25": 1.0,
     "p75": 1.0
    }
   }
  ],
  "cells_with_opportunities_but_no_placed_order": [
   "NBA|NBA_TEAM_TOTAL|T3|MODEL_FADE",
   "NFL|NFL_GAME_TOTAL|T2|FADE",
   "NFL|NFL_GAME_TOTAL|T2|RIDE",
   "NFL|NFL_SPREAD|T2|FADE",
   "NFL|NFL_SPREAD|T2|RIDE",
   "NFL|NFL_TEAM_TOTAL|T1|RIDE",
   "NFL|NFL_TEAM_TOTAL|T2|FADE",
   "NFL|NFL_TEAM_TOTAL|T2|MOMENTUM",
   "NFL|NFL_TEAM_TOTAL|T2|RIDE",
   "NFL|NFL_TEAM_TOTAL|T3|FADE",
   "NHL|NHL_GAME_TOTAL|T3|FADE",
   "NHL|NHL_GAME_TOTAL|T3|MODEL_FADE"
  ],
  "days_by_sport": {
   "NBA": [
    "2026-11-12",
    "2026-11-13",
    "2026-11-14",
    "2026-11-15",
    "2026-11-16",
    "2026-11-17",
    "2026-11-18",
    "2026-11-19",
    "2026-11-20"
   ],
   "NFL": [
    "2026-11-12",
    "2026-11-13",
    "2026-11-14",
    "2026-11-15",
    "2026-11-16",
    "2026-11-17"
   ],
   "NHL": [
    "2026-11-17",
    "2026-11-18",
    "2026-11-19",
    "2026-11-20"
   ]
  }
 },
 "orders_files": 1
}

```
