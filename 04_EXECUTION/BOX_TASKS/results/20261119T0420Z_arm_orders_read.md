# Box task `arm_orders_read` — 20261119T0420Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0420Z_arm_orders_read.toml`
- note: W119.3 post-merge read (#526)
- ran: 2026-11-19T04:24:55Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/arm_orders_read.py`

```
{
 "counts": {
  "per_epoch_arm_sport": {
   "post_epoch_all_sides|ERROR|NBA": {
    "skips": 6037
   },
   "post_epoch_all_sides|ERROR|NFL": {
    "skips": 206
   },
   "post_epoch_all_sides|ERROR|NHL": {
    "skips": 97
   },
   "post_epoch_all_sides|FADE|NBA": {
    "orders": 339,
    "skips": 1923
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 15,
    "skips": 713
   },
   "post_epoch_all_sides|FADE|NHL": {
    "orders": 5,
    "skips": 158
   },
   "post_epoch_all_sides|MODEL_FADE|NBA": {
    "orders": 188,
    "skips": 353
   },
   "post_epoch_all_sides|MODEL_FADE|NHL": {
    "orders": 25,
    "skips": 24
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 332,
    "skips": 2425
   },
   "post_epoch_all_sides|MOMENTUM|NFL": {
    "orders": 1,
    "skips": 159
   },
   "post_epoch_all_sides|MOMENTUM|NHL": {
    "orders": 7,
    "skips": 28
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 46571
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 8217
   },
   "post_epoch_all_sides|NO_BET|NHL": {
    "skips": 1125
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 331,
    "skips": 2796,
    "would": 95
   },
   "post_epoch_all_sides|RIDE|NFL": {
    "orders": 47,
    "skips": 3073,
    "would": 1
   },
   "post_epoch_all_sides|RIDE|NHL": {
    "orders": 50,
    "skips": 847
   },
   "post_epoch_all_sides|UNROUTED|NHL": {
    "skips": 5573
   }
  },
  "rows_with_unparseable_ts": 0,
  "skip_reasons_per_epoch_arm": {
   "post_epoch_all_sides|ERROR": {
    "unrouted": 6340
   },
   "post_epoch_all_sides|FADE": {
    "daily_breaker": 93,
    "mid_gap_above_threshold": 6,
    "side_unavailable_or_disagrees": 3,
    "size_zero:cap binds, stake 0: day": 2083,
    "size_zero:cap binds, stake 0: event": 536,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 2,
    "size_zero:cap binds, stake 0: same_game_cluster": 71
   },
   "post_epoch_all_sides|MODEL_FADE": {
    "mid_gap_above_threshold": 12,
    "size_zero:cap binds, stake 0: day": 220,
    "size_zero:cap binds, stake 0: event": 42,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 23,
    "size_zero:cap binds, stake 0: same_game_cluster": 80
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "mid_gap_above_threshold": 21,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 2110,
    "size_zero:cap binds, stake 0: event": 343,
    "size_zero:cap binds, stake 0: same_game_cluster": 23
   },
   "post_epoch_all_sides|NO_BET": {
    "hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D)": 40,
    "no_bet": 55873
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "mid_gap_above_threshold": 2,
    "side_unavailable_or_disagrees": 12,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 5073,
    "size_zero:cap binds, stake 0: event": 822,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 2,
    "size_zero:cap binds, stake 0: same_game_cluster": 171
   },
   "post_epoch_all_sides|UNROUTED": {
    "unrouted": 5573
   }
  }
 },
 "fills": {
  "FADE|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 359,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "FADE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": null,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  },
  "MODEL_FADE|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 213,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "MODEL_FADE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": null,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  },
  "MOMENTUM|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 340,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "MOMENTUM",
   "epoch": "post_epoch_all_sides",
   "fill_rate": null,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  },
  "RIDE|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 428,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "RIDE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": null,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  }
 },
 "fills_note": "legacy per-order lookup not run",
 "gg1771_epoch": "2026-11-06T01:03:42Z",
 "join": {
  "cross_clustered": {
   "post_epoch_all_sides": {
    "by_arm": {
     "FADE": {
      "cross": {
       "ci": [
        -0.093,
        0.1168
       ],
       "n": 307,
       "n_games": 31,
       "net": 0.0119
      },
      "cross_minus_rest": {
       "ci": [
        -0.1014,
        0.1031
       ],
       "n": 307,
       "n_games": 31,
       "net": 0.0008
      },
      "n_no_spread": 6,
      "n_spread_archive": 105,
      "n_spread_logged": 202,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0045,
        0.0267
       ],
       "n": 307,
       "n_games": 31,
       "net": 0.0111
      },
      "rest_touch_all": {
       "ci": [
        -0.0043,
        0.0261
       ],
       "n": 313,
       "n_games": 33,
       "net": 0.0109
      }
     },
     "MODEL_FADE": {
      "cross": {
       "ci": [
        -0.3801,
        0.1221
       ],
       "n": 122,
       "n_games": 10,
       "net": -0.129
      },
      "cross_minus_rest": {
       "ci": [
        -0.3766,
        0.1283
       ],
       "n": 122,
       "n_games": 10,
       "net": -0.1242
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 122,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0145,
        0.0048
       ],
       "n": 122,
       "n_games": 10,
       "net": -0.0048
      },
      "rest_touch_all": {
       "ci": [
        -0.0145,
        0.0048
       ],
       "n": 122,
       "n_games": 10,
       "net": -0.0048
      }
     },
     "MOMENTUM": {
      "cross": {
       "ci": [
        -0.1887,
        0.1012
       ],
       "n": 308,
       "n_games": 31,
       "net": -0.0437
      },
      "cross_minus_rest": {
       "ci": [
        -0.1758,
        0.0627
       ],
       "n": 308,
       "n_games": 31,
       "net": -0.0566
      },
      "n_no_spread": 0,
      "n_spread_archive": 96,
      "n_spread_logged": 212,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0278,
        0.0535
       ],
       "n": 308,
       "n_games": 31,
       "net": 0.0129
      },
      "rest_touch_all": {
       "ci": [
        -0.0278,
        0.0535
       ],
       "n": 308,
       "n_games": 31,
       "net": 0.0129
      }
     },
     "RIDE": {
      "cross": {
       "ci": [
        -0.0508,
        0.0676
       ],
       "n": 385,
       "n_games": 32,
       "net": 0.0084
      },
      "cross_minus_rest": {
       "ci": [
        -0.0508,
        0.0679
       ],
       "n": 385,
       "n_games": 32,
       "net": 0.0086
      },
      "n_no_spread": 26,
      "n_spread_archive": 253,
      "n_spread_logged": 132,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0146,
        0.0142
       ],
       "n": 385,
       "n_games": 32,
       "net": -0.0002
      },
      "rest_touch_all": {
       "ci": [
        -0.0131,
        0.0142
       ],
       "n": 411,
       "n_games": 36,
       "net": 0.0005
      }
     }
    },
    "by_arm_sport": {
     "FADE|nba": {
      "cross": {
       "ci": [
        -0.1016,
        0.1213
       ],
       "n": 292,
       "n_games": 24,
       "net": 0.0099
      },
      "cross_minus_rest": {
       "ci": [
        -0.1099,
        0.1074
       ],
       "n": 292,
       "n_games": 24,
       "net": -0.0013
      },
      "n_no_spread": 1,
      "n_spread_archive": 93,
      "n_spread_logged": 199,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0048,
        0.027
       ],
       "n": 292,
       "n_games": 24,
       "net": 0.0111
      },
      "rest_touch_all": {
       "ci": [
        -0.0047,
        0.0269
       ],
       "n": 293,
       "n_games": 24,
       "net": 0.0111
      }
     },
     "FADE|nfl": {
      "cross": {
       "ci": [
        -0.0209,
        0.1228
       ],
       "n": 10,
       "n_games": 3,
       "net": 0.0509
      },
      "cross_minus_rest": {
       "ci": [
        -0.2211,
        0.293
       ],
       "n": 10,
       "n_games": 3,
       "net": 0.0359
      },
      "n_no_spread": 5,
      "n_spread_archive": 10,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.309,
        0.339
       ],
       "n": 10,
       "n_games": 3,
       "net": 0.015
      },
      "rest_touch_all": {
       "ci": [
        -0.133,
        0.153
       ],
       "n": 15,
       "n_games": 5,
       "net": 0.01
      }
     },
     "FADE|nhl": {
      "cross": {
       "ci": [
        -0.7016,
        0.8075
       ],
       "n": 5,
       "n_games": 4,
       "net": 0.0529
      },
      "cross_minus_rest": {
       "ci": [
        -0.7016,
        0.8075
       ],
       "n": 5,
       "n_games": 4,
       "net": 0.0529
      },
      "n_no_spread": 0,
      "n_spread_archive": 2,
      "n_spread_logged": 3,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 5,
       "n_games": 4,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 5,
       "n_games": 4,
       "net": 0.0
      }
     },
     "MODEL_FADE|nba": {
      "cross": {
       "ci": [
        -0.3979,
        0.1424
       ],
       "n": 120,
       "n_games": 8,
       "net": -0.1278
      },
      "cross_minus_rest": {
       "ci": [
        -0.3945,
        0.1487
       ],
       "n": 120,
       "n_games": 8,
       "net": -0.1229
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 120,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0153,
        0.0055
       ],
       "n": 120,
       "n_games": 8,
       "net": -0.0049
      },
      "rest_touch_all": {
       "ci": [
        -0.0153,
        0.0055
       ],
       "n": 120,
       "n_games": 8,
       "net": -0.0049
      }
     },
     "MODEL_FADE|nhl": {
      "cross": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": -0.2024
      },
      "cross_minus_rest": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": -0.2024
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 2,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        NaN,
        NaN
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        NaN,
        NaN
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.0
      }
     },
     "MOMENTUM|nba": {
      "cross": {
       "ci": [
        -0.192,
        0.1022
       ],
       "n": 305,
       "n_games": 28,
       "net": -0.0449
      },
      "cross_minus_rest": {
       "ci": [
        -0.1792,
        0.0627
       ],
       "n": 305,
       "n_games": 28,
       "net": -0.0582
      },
      "n_no_spread": 0,
      "n_spread_archive": 94,
      "n_spread_logged": 211,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0279,
        0.0546
       ],
       "n": 305,
       "n_games": 28,
       "net": 0.0133
      },
      "rest_touch_all": {
       "ci": [
        -0.0279,
        0.0546
       ],
       "n": 305,
       "n_games": 28,
       "net": 0.0133
      }
     },
     "MOMENTUM|nfl": {
      "cross": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": -0.1274
      },
      "cross_minus_rest": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": -0.0174
      },
      "n_no_spread": 0,
      "n_spread_archive": 1,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": -0.11
      },
      "rest_touch_all": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": -0.11
      }
     },
     "MOMENTUM|nhl": {
      "cross": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.1802
      },
      "cross_minus_rest": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.1802
      },
      "n_no_spread": 0,
      "n_spread_archive": 1,
      "n_spread_logged": 1,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        NaN,
        NaN
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        NaN,
        NaN
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.0
      }
     },
     "RIDE|nba": {
      "cross": {
       "ci": [
        -0.06,
        0.0791
       ],
       "n": 323,
       "n_games": 24,
       "net": 0.0095
      },
      "cross_minus_rest": {
       "ci": [
        -0.054,
        0.0844
       ],
       "n": 323,
       "n_games": 24,
       "net": 0.0152
      },
      "n_no_spread": 1,
      "n_spread_archive": 212,
      "n_spread_logged": 111,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0174,
        0.006
       ],
       "n": 323,
       "n_games": 24,
       "net": -0.0057
      },
      "rest_touch_all": {
       "ci": [
        -0.0173,
        0.006
       ],
       "n": 324,
       "n_games": 25,
       "net": -0.0056
      }
     },
     "RIDE|nfl": {
      "cross": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 22,
       "n_games": 2,
       "net": 0.0878
      },
      "cross_minus_rest": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 22,
       "n_games": 2,
       "net": 0.0082
      },
      "n_no_spread": 25,
      "n_spread_archive": 22,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 22,
       "n_games": 2,
       "net": 0.0795
      },
      "rest_touch_all": {
       "ci": [
        -0.0451,
        0.1323
       ],
       "n": 47,
       "n_games": 5,
       "net": 0.0436
      }
     },
     "RIDE|nhl": {
      "cross": {
       "ci": [
        -0.1686,
        0.0788
       ],
       "n": 40,
       "n_games": 6,
       "net": -0.0449
      },
      "cross_minus_rest": {
       "ci": [
        -0.1686,
        0.0788
       ],
       "n": 40,
       "n_games": 6,
       "net": -0.0449
      },
      "n_no_spread": 0,
      "n_spread_archive": 19,
      "n_spread_logged": 21,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 40,
       "n_games": 6,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 40,
       "n_games": 6,
       "net": 0.0
      }
     }
    }
   },
   "pre_epoch_yes_only": {
    "by_arm": {},
    "by_arm_sport": {}
   }
  },
  "join_health": {
   "fill_status_unknown": 0,
   "lookups_failed": 0,
   "orders": 1340,
   "pending": 185,
   "resolved": 1155,
   "void": 0
  },
  "join_note": "ok",
  "per_arm": {
   "FADE|post_epoch_all_sides": {
    "E1_fills": 24,
    "E1_orders": 359,
    "E2_per_filled_contract_after_fees": 0.2017,
    "E2_per_filled_contract_before_fees": 0.2125,
    "E3_win_rate_fills": 0.4375,
    "E3_win_rate_nonfills_counterfactual": 0.1946,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0669,
    "markout_mean": {
     "close": 0.0579,
     "h1": -0.0081,
     "h30": 0.0055,
     "h5": 0.0042,
     "settle": 0.2125
    },
    "markout_n": {
     "close": 12,
     "h1": 24,
     "h30": 11,
     "h5": 12,
     "settle": 16
    },
    "n_nonfills_resolved": 298,
    "n_settled_fills": 16,
    "placement": null
   },
   "MODEL_FADE|post_epoch_all_sides": {
    "E1_fills": 7,
    "E1_orders": 213,
    "E2_per_filled_contract_after_fees": -0.3064,
    "E2_per_filled_contract_before_fees": -0.295,
    "E3_win_rate_fills": 0.0,
    "E3_win_rate_nonfills_counterfactual": 0.3333,
    "arm": "MODEL_FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0329,
    "markout_mean": {
     "h1": -0.0079,
     "h30": 0.005,
     "settle": -0.295
    },
    "markout_n": {
     "h1": 7,
     "h30": 2,
     "settle": 2
    },
    "n_nonfills_resolved": 120,
    "n_settled_fills": 2,
    "placement": null
   },
   "MOMENTUM|post_epoch_all_sides": {
    "E1_fills": 57,
    "E1_orders": 340,
    "E2_per_filled_contract_after_fees": 0.0568,
    "E2_per_filled_contract_before_fees": 0.0695,
    "E3_win_rate_fills": 0.4912,
    "E3_win_rate_nonfills_counterfactual": 0.4382,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1676,
    "markout_mean": {
     "close": -0.0023,
     "h1": -0.0104,
     "h30": -0.0112,
     "h5": -0.0122,
     "settle": 0.0695
    },
    "markout_n": {
     "close": 30,
     "h1": 57,
     "h30": 8,
     "h5": 9,
     "settle": 57
    },
    "n_nonfills_resolved": 251,
    "n_settled_fills": 57,
    "placement": null
   },
   "RIDE|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 428,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8253,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0911,
    "markout_mean": {
     "close": 0.0017,
     "h1": -0.0132,
     "h30": -0.0044,
     "h5": -0.004,
     "settle": 0.0056
    },
    "markout_n": {
     "close": 30,
     "h1": 37,
     "h30": 9,
     "h5": 10,
     "settle": 39
    },
    "n_nonfills_resolved": 372,
    "n_settled_fills": 39,
    "placement": null
   }
  },
  "per_arm_option": {
   "FADE|rest_inside|post_epoch_all_sides": {
    "E1_fills": 2,
    "E1_orders": 17,
    "E2_per_filled_contract_after_fees": null,
    "E2_per_filled_contract_before_fees": null,
    "E3_win_rate_fills": null,
    "E3_win_rate_nonfills_counterfactual": 0.0,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1176,
    "markout_mean": {
     "h1": -0.005,
     "h30": -0.005,
     "h5": -0.005
    },
    "markout_n": {
     "h1": 2,
     "h30": 1,
     "h5": 1
    },
    "n_nonfills_resolved": 1,
    "n_settled_fills": 0,
    "placement": "rest_inside"
   },
   "FADE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 22,
    "E1_orders": 342,
    "E2_per_filled_contract_after_fees": 0.2017,
    "E2_per_filled_contract_before_fees": 0.2125,
    "E3_win_rate_fills": 0.4375,
    "E3_win_rate_nonfills_counterfactual": 0.1953,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0643,
    "markout_mean": {
     "close": 0.0579,
     "h1": -0.0084,
     "h30": 0.0065,
     "h5": 0.005,
     "settle": 0.2125
    },
    "markout_n": {
     "close": 12,
     "h1": 22,
     "h30": 10,
     "h5": 11,
     "settle": 16
    },
    "n_nonfills_resolved": 297,
    "n_settled_fills": 16,
    "placement": "rest_touch"
   },
   "MODEL_FADE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 7,
    "E1_orders": 213,
    "E2_per_filled_contract_after_fees": -0.3064,
    "E2_per_filled_contract_before_fees": -0.295,
    "E3_win_rate_fills": 0.0,
    "E3_win_rate_nonfills_counterfactual": 0.3333,
    "arm": "MODEL_FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0329,
    "markout_mean": {
     "h1": -0.0079,
     "h30": 0.005,
     "settle": -0.295
    },
    "markout_n": {
     "h1": 7,
     "h30": 2,
     "settle": 2
    },
    "n_nonfills_resolved": 120,
    "n_settled_fills": 2,
    "placement": "rest_touch"
   },
   "MOMENTUM|rest_touch|post_epoch_all_sides": {
    "E1_fills": 57,
    "E1_orders": 340,
    "E2_per_filled_contract_after_fees": 0.0568,
    "E2_per_filled_contract_before_fees": 0.0695,
    "E3_win_rate_fills": 0.4912,
    "E3_win_rate_nonfills_counterfactual": 0.4382,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1676,
    "markout_mean": {
     "close": -0.0023,
     "h1": -0.0104,
     "h30": -0.0112,
     "h5": -0.0122,
     "settle": 0.0695
    },
    "markout_n": {
     "close": 30,
     "h1": 57,
     "h30": 8,
     "h5": 9,
     "settle": 57
    },
    "n_nonfills_resolved": 251,
    "n_settled_fills": 57,
    "placement": "rest_touch"
   },
   "RIDE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 428,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8253,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0911,
    "markout_mean": {
     "close": 0.0017,
     "h1": -0.0132,
     "h30": -0.0044,
     "h5": -0.004,
     "settle": 0.0056
    },
    "markout_n": {
     "close": 30,
     "h1": 37,
     "h30": 9,
     "h5": 10,
     "settle": 39
    },
    "n_nonfills_resolved": 372,
    "n_settled_fills": 39,
    "placement": "rest_touch"
   }
  },
  "placement_model": {
   "post_epoch_all_sides": {
    "by_arm": {
     "by": [
      "arm"
     ],
     "fill": {
      "FADE": {
       "fills": 24,
       "hi": 0.0975,
       "lo": 0.0453,
       "n": 359,
       "p_fill": 0.0669
      },
      "MODEL_FADE": {
       "fills": 7,
       "hi": 0.0663,
       "lo": 0.016,
       "n": 213,
       "p_fill": 0.0329
      },
      "MOMENTUM": {
       "fills": 57,
       "hi": 0.211,
       "lo": 0.1317,
       "n": 340,
       "p_fill": 0.1676
      },
      "RIDE": {
       "fills": 39,
       "hi": 0.1221,
       "lo": 0.0674,
       "n": 428,
       "p_fill": 0.0911
      }
     },
     "min_n": 30,
     "options": {
      "FADE": {
       "best": "cross",
       "best_net": 0.0119,
       "cross": {
        "ci": [
         -0.0312,
         0.055
        ],
        "n": 307,
        "net": 0.0119,
        "spread_logged": 307,
        "supported": true
       },
       "no_place": {
        "n": 359,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 1,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0009,
         0.0226
        ],
        "n": 313,
        "n_filled": 16,
        "net": 0.0109,
        "supported": false
       }
      },
      "MODEL_FADE": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1935,
         -0.0646
        ],
        "n": 122,
        "net": -0.129,
        "spread_logged": 122,
        "supported": true
       },
       "no_place": {
        "n": 213,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0131,
         0.0034
        ],
        "n": 122,
        "n_filled": 2,
        "net": -0.0048,
        "supported": false
       }
      },
      "MOMENTUM": {
       "best": "rest_touch",
       "best_net": 0.0129,
       "cross": {
        "ci": [
         -0.0925,
         0.0051
        ],
        "n": 308,
        "net": -0.0437,
        "spread_logged": 308,
        "supported": true
       },
       "no_place": {
        "n": 340,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.006,
         0.0317
        ],
        "n": 308,
        "n_filled": 57,
        "net": 0.0129,
        "supported": true
       }
      },
      "RIDE": {
       "best": "cross",
       "best_net": 0.0084,
       "cross": {
        "ci": [
         -0.027,
         0.0438
        ],
        "n": 385,
        "net": 0.0084,
        "spread_logged": 385,
        "supported": true
       },
       "no_place": {
        "n": 428,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0115,
         0.0126
        ],
        "n": 411,
        "n_filled": 39,
        "net": 0.0005,
        "supported": true
       }
      }
     },
     "selection": {
      "FADE": {
       "edge_filled": 0.2125,
       "edge_filled_ci": [
        0.0,
        0.425
       ],
       "edge_unfilled": 0.0327,
       "edge_unfilled_ci": [
        -0.0108,
        0.0761
       ],
       "n_filled": 16,
       "n_unfilled": 298,
       "selection": 0.1798,
       "selection_ci": [
        -0.037,
        0.3967
       ],
       "supported": false,
       "win_filled": 0.4375,
       "win_unfilled": 0.1946
      },
      "MODEL_FADE": {
       "edge_filled": -0.295,
       "edge_filled_ci": [
        -0.7164,
        0.1264
       ],
       "edge_unfilled": -0.0877,
       "edge_unfilled_ci": [
        -0.1526,
        -0.0229
       ],
       "n_filled": 2,
       "n_unfilled": 120,
       "selection": -0.2072,
       "selection_ci": [
        -0.6336,
        0.2191
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.3333
      },
      "MOMENTUM": {
       "edge_filled": 0.0695,
       "edge_filled_ci": [
        -0.0317,
        0.1706
       ],
       "edge_unfilled": -0.0303,
       "edge_unfilled_ci": [
        -0.0853,
        0.0246
       ],
       "n_filled": 57,
       "n_unfilled": 251,
       "selection": 0.0998,
       "selection_ci": [
        -0.0153,
        0.2149
       ],
       "supported": true,
       "win_filled": 0.4912,
       "win_unfilled": 0.4382
      },
      "RIDE": {
       "edge_filled": 0.0056,
       "edge_filled_ci": [
        -0.1229,
        0.1341
       ],
       "edge_unfilled": 0.0413,
       "edge_unfilled_ci": [
        0.0051,
        0.0774
       ],
       "n_filled": 39,
       "n_unfilled": 372,
       "selection": -0.0356,
       "selection_ci": [
        -0.1691,
        0.0979
       ],
       "supported": true,
       "win_filled": 0.6923,
       "win_unfilled": 0.8253
      }
     }
    },
    "by_arm_leaf": {
     "by": [
      "arm",
      "leaf"
     ],
     "cells_below_min_orders_dropped": 51,
     "fill": {
      "FADE|NBA|NBA_GAME_TOTAL|T2|3|up": {
       "fills": 3,
       "hi": 0.4103,
       "lo": 0.0619,
       "n": 17,
       "p_fill": 0.1765
      },
      "FADE|NBA|NBA_GAME_TOTAL|T2|4|up": {
       "fills": 0,
       "hi": 0.2281,
       "lo": 0.0,
       "n": 13,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_GAME_TOTAL|T3|3|up": {
       "fills": 0,
       "hi": 0.2153,
       "lo": 0.0,
       "n": 14,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_SPREAD|T2|2|flat": {
       "fills": 3,
       "hi": 0.2562,
       "lo": 0.0346,
       "n": 30,
       "p_fill": 0.1
      },
      "FADE|NBA|NBA_SPREAD|T2|3|down": {
       "fills": 0,
       "hi": 0.1843,
       "lo": 0.0,
       "n": 17,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_SPREAD|T2|4|down": {
       "fills": 0,
       "hi": 0.117,
       "lo": 0.0,
       "n": 29,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_SPREAD|T3|3|down": {
       "fills": 0,
       "hi": 0.2775,
       "lo": 0.0,
       "n": 10,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_SPREAD|T3|4|flat": {
       "fills": 16,
       "hi": 0.2025,
       "lo": 0.0824,
       "n": 122,
       "p_fill": 0.1311
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "fills": 0,
       "hi": 0.0423,
       "lo": 0.0,
       "n": 87,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|2|na": {
       "fills": 0,
       "hi": 0.1611,
       "lo": 0.0,
       "n": 20,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|3|na": {
       "fills": 0,
       "hi": 0.1431,
       "lo": 0.0,
       "n": 23,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|4|na": {
       "fills": 0,
       "hi": 0.0676,
       "lo": 0.0,
       "n": 53,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T2|4|flat": {
       "fills": 1,
       "hi": 0.1889,
       "lo": 0.0068,
       "n": 26,
       "p_fill": 0.0385
      },
      "MODEL_FADE|NBA|NBA_SPREAD|T3|2|flat": {
       "fills": 5,
       "hi": 0.5313,
       "lo": 0.1328,
       "n": 17,
       "p_fill": 0.2941
      },
      "MODEL_FADE|NHL|NHL_GAME_TOTAL|T1|4|na": {
       "fills": 0,
       "hi": 0.2588,
       "lo": 0.0,
       "n": 11,
       "p_fill": 0.0
      },
      "MODEL_FADE|NHL|NHL_PUCK_LINE|T1|4|na": {
       "fills": 0,
       "hi": 0.2425,
       "lo": 0.0,
       "n": 12,
     

[... 46411 bytes cut ...]

filled": -0.325,
       "edge_unfilled_ci": [
        -0.4919,
        -0.1581
       ],
       "n_filled": 2,
       "n_unfilled": 18,
       "selection": 0.235,
       "selection_ci": [
        -0.7398,
        1.2098
       ],
       "supported": false,
       "win_filled": 0.5,
       "win_unfilled": 0.1667
      },
      "MOMENTUM|NBA|NBA_GAME_TOTAL|T2|3|down": {
       "edge_filled": 0.32,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0421,
       "edge_unfilled_ci": [
        -0.203,
        0.1188
       ],
       "n_filled": 1,
       "n_unfilled": 19,
       "selection": 0.3621,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.4737
      },
      "MOMENTUM|NBA|NBA_GAME_TOTAL|T2|4|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.018,
       "edge_unfilled_ci": [
        -0.0937,
        0.0577
       ],
       "n_filled": 0,
       "n_unfilled": 10,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.3
      },
      "MOMENTUM|NBA|NBA_GAME_TOTAL|T3|4|down": {
       "edge_filled": 0.19,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.11,
       "edge_unfilled_ci": [
        0.0856,
        0.1344
       ],
       "n_filled": 1,
       "n_unfilled": 9,
       "selection": 0.08,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 1.0
      },
      "MOMENTUM|NBA|NBA_SPREAD|T2|2|down": {
       "edge_filled": 0.5483,
       "edge_filled_ci": [
        0.4903,
        0.6063
       ],
       "edge_unfilled": 0.55,
       "edge_unfilled_ci": [
        0.4377,
        0.6623
       ],
       "n_filled": 6,
       "n_unfilled": 4,
       "selection": -0.0017,
       "selection_ci": [
        -0.1281,
        0.1247
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 1.0
      },
      "MOMENTUM|NBA|NBA_SPREAD|T2|2|up": {
       "edge_filled": -0.405,
       "edge_filled_ci": [
        -0.4462,
        -0.3638
       ],
       "edge_unfilled": -0.1093,
       "edge_unfilled_ci": [
        -0.384,
        0.1654
       ],
       "n_filled": 4,
       "n_unfilled": 14,
       "selection": -0.2957,
       "selection_ci": [
        -0.5735,
        -0.0179
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.3571
      },
      "MOMENTUM|NBA|NBA_SPREAD|T2|3|up": {
       "edge_filled": -0.051,
       "edge_filled_ci": [
        -0.3076,
        0.2056
       ],
       "edge_unfilled": 0.089,
       "edge_unfilled_ci": [
        -0.1136,
        0.2916
       ],
       "n_filled": 10,
       "n_unfilled": 20,
       "selection": -0.14,
       "selection_ci": [
        -0.467,
        0.187
       ],
       "supported": false,
       "win_filled": 0.2,
       "win_unfilled": 0.4
      },
      "MOMENTUM|NBA|NBA_SPREAD|T2|4|up": {
       "edge_filled": -0.1138,
       "edge_filled_ci": [
        -0.1417,
        -0.0858
       ],
       "edge_unfilled": 0.0105,
       "edge_unfilled_ci": [
        -0.1196,
        0.1406
       ],
       "n_filled": 8,
       "n_unfilled": 20,
       "selection": -0.1242,
       "selection_ci": [
        -0.2573,
        0.0088
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.15
      },
      "MOMENTUM|NBA|NBA_SPREAD|T3|3|up": {
       "edge_filled": 0.4157,
       "edge_filled_ci": [
        0.1613,
        0.6701
       ],
       "edge_unfilled": 0.02,
       "edge_unfilled_ci": [
        -0.4948,
        0.5348
       ],
       "n_filled": 7,
       "n_unfilled": 6,
       "selection": 0.3957,
       "selection_ci": [
        -0.1785,
        0.9699
       ],
       "supported": false,
       "win_filled": 0.8571,
       "win_unfilled": 0.5
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T2|2|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.1178,
       "edge_unfilled_ci": [
        -0.3,
        0.0644
       ],
       "n_filled": 0,
       "n_unfilled": 27,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.3704
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T2|3|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.2342,
       "edge_unfilled_ci": [
        -0.3766,
        -0.0918
       ],
       "n_filled": 0,
       "n_unfilled": 31,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.3226
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0439,
       "edge_unfilled_ci": [
        -0.129,
        0.2167
       ],
       "n_filled": 0,
       "n_unfilled": 31,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5484
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0565,
       "edge_unfilled_ci": [
        -0.1932,
        0.3062
       ],
       "n_filled": 0,
       "n_unfilled": 17,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5294
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T2|4|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0927,
       "edge_unfilled_ci": [
        0.0146,
        0.1708
       ],
       "n_filled": 0,
       "n_unfilled": 26,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.9615
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T3|3|flat": {
       "edge_filled": -0.32,
       "edge_filled_ci": [
        -0.96,
        0.32
       ],
       "edge_unfilled": -0.0522,
       "edge_unfilled_ci": [
        -0.3975,
        0.293
       ],
       "n_filled": 3,
       "n_unfilled": 9,
       "selection": -0.2678,
       "selection_ci": [
        -0.995,
        0.4594
       ],
       "supported": false,
       "win_filled": 0.3333,
       "win_unfilled": 0.6667
      },
      "RIDE|NBA|NBA_SPREAD|T1|2|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.023,
       "edge_unfilled_ci": [
        -0.3445,
        0.2985
       ],
       "n_filled": 0,
       "n_unfilled": 10,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5
      },
      "RIDE|NBA|NBA_SPREAD|T1|3|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.1627,
       "edge_unfilled_ci": [
        -0.0609,
        0.3863
       ],
       "n_filled": 0,
       "n_unfilled": 11,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.8182
      },
      "RIDE|NBA|NBA_SPREAD|T1|4|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.2114,
       "edge_unfilled_ci": [
        0.1655,
        0.2573
       ],
       "n_filled": 0,
       "n_unfilled": 14,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 1.0
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|down": {
       "edge_filled": -0.555,
       "edge_filled_ci": [
        -0.572,
        -0.538
       ],
       "edge_unfilled": 0.2675,
       "edge_unfilled_ci": [
        0.0581,
        0.4769
       ],
       "n_filled": 4,
       "n_unfilled": 12,
       "selection": -0.8225,
       "selection_ci": [
        -1.0326,
        -0.6124
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.8333
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|flat": {
       "edge_filled": -0.58,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.1123,
       "edge_unfilled_ci": [
        -0.1465,
        0.3711
       ],
       "n_filled": 1,
       "n_unfilled": 13,
       "selection": -0.6923,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.6923
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|down": {
       "edge_filled": 0.298,
       "edge_filled_ci": [
        0.2562,
        0.3398
       ],
       "edge_unfilled": 0.3156,
       "edge_unfilled_ci": [
        0.2904,
        0.3407
       ],
       "n_filled": 5,
       "n_unfilled": 9,
       "selection": -0.0176,
       "selection_ci": [
        -0.0663,
        0.0312
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 1.0
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|flat": {
       "edge_filled": 0.2533,
       "edge_filled_ci": [
        0.2207,
        0.286
       ],
       "edge_unfilled": -0.0629,
       "edge_unfilled_ci": [
        -0.3124,
        0.1867
       ],
       "n_filled": 3,
       "n_unfilled": 14,
       "selection": 0.3162,
       "selection_ci": [
        0.0645,
        0.5679
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.6429
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|down": {
       "edge_filled": 0.12,
       "edge_filled_ci": [
        -0.0564,
        0.2964
       ],
       "edge_unfilled": -0.0773,
       "edge_unfilled_ci": [
        -0.3113,
        0.1568
       ],
       "n_filled": 2,
       "n_unfilled": 11,
       "selection": 0.1973,
       "selection_ci": [
        -0.0958,
        0.4903
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.8182
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|flat": {
       "edge_filled": 0.03,
       "edge_filled_ci": [
        0.03,
        0.03
       ],
       "edge_unfilled": 0.0963,
       "edge_unfilled_ci": [
        0.0818,
        0.1108
       ],
       "n_filled": 2,
       "n_unfilled": 46,
       "selection": -0.0663,
       "selection_ci": [
        -0.0808,
        -0.0518
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 1.0
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0593,
       "edge_unfilled_ci": [
        -0.0741,
        0.1927
       ],
       "n_filled": 0,
       "n_unfilled": 14,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.9286
      },
      "RIDE|NBA|NBA_TEAM_TOTAL|T2|4|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0297,
       "edge_unfilled_ci": [
        -0.0419,
        0.1012
       ],
       "n_filled": 0,
       "n_unfilled": 65,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.9077
      },
      "RIDE|NBA|NBA_TEAM_TOTAL|T3|2|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0573,
       "edge_unfilled_ci": [
        -0.1324,
        0.247
       ],
       "n_filled": 0,
       "n_unfilled": 26,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.6154
      },
      "RIDE|NFL|NFL_GAME_TOTAL|T1|4|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.22,
       "edge_unfilled_ci": [
        -0.4986,
        0.0586
       ],
       "n_filled": 0,
       "n_unfilled": 10,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.7
      },
      "RIDE|NFL|NFL_SPREAD|T1|4|na": {
       "edge_filled": 0.15,
       "edge_filled_ci": [
        0.15,
        0.15
       ],
       "edge_unfilled": -0.0946,
       "edge_unfilled_ci": [
        -0.332,
        0.1428
       ],
       "n_filled": 2,
       "n_unfilled": 13,
       "selection": 0.2446,
       "selection_ci": [
        0.0072,
        0.482
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.7692
      },
      "RIDE|NFL|NFL_SPREAD|T3|4|flat": {
       "edge_filled": 0.155,
       "edge_filled_ci": [
        0.1115,
        0.1985
       ],
       "edge_unfilled": 0.1117,
       "edge_unfilled_ci": [
        0.0635,
        0.1598
       ],
       "n_filled": 4,
       "n_unfilled": 6,
       "selection": 0.0433,
       "selection_ci": [
        -0.0215,
        0.1082
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 1.0
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T2|4|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0875,
       "edge_unfilled_ci": [
        0.0489,
        0.1261
       ],
       "n_filled": 0,
       "n_unfilled": 8,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 1.0
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T3|4|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0661,
       "edge_unfilled_ci": [
        -0.2406,
        0.1084
       ],
       "n_filled": 0,
       "n_unfilled": 18,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.8333
      }
     }
    },
    "by_arm_sport": {
     "by": [
      "arm",
      "sport"
     ],
     "fill": {
      "FADE|nba": {
       "fills": 22,
       "hi": 0.0963,
       "lo": 0.0432,
       "n": 339,
       "p_fill": 0.0649
      },
      "FADE|nfl": {
       "fills": 2,
       "hi": 0.3788,
       "lo": 0.0374,
       "n": 15,
       "p_fill": 0.1333
      },
      "FADE|nhl": {
       "fills": 0,
       "hi": 0.4345,
       "lo": 0.0,
       "n": 5,
       "p_fill": 0.0
      },
      "MODEL_FADE|nba": {
       "fills": 7,
       "hi": 0.0748,
       "lo": 0.0182,
       "n": 188,
       "p_fill": 0.0372
      },
      "MODEL_FADE|nhl": {
       "fills": 0,
       "hi": 0.1332,
       "lo": 0.0,
       "n": 25,
       "p_fill": 0.0
      },
      "MOMENTUM|nba": {
       "fills": 56,
       "hi": 0.2127,
       "lo": 0.1322,
       "n": 332,
       "p_fill": 0.1687
      },
      "MOMENTUM|nfl": {
       "fills": 1,
       "hi": 1.0,
       "lo": 0.2065,
       "n": 1,
       "p_fill": 1.0
      },
      "MOMENTUM|nhl": {
       "fills": 0,
       "hi": 0.3543,
       "lo": 0.0,
       "n": 7,
       "p_fill": 0.0
      },
      "RIDE|nba": {
       "fills": 26,
       "hi": 0.1126,
       "lo": 0.0542,
       "n": 331,
       "p_fill": 0.0785
      },
      "RIDE|nfl": {
       "fills": 13,
       "hi": 0.4176,
       "lo": 0.1694,
       "n": 47,
       "p_fill": 0.2766
      },
      "RIDE|nhl": {
       "fills": 0,
       "hi": 0.0713,
       "lo": 0.0,
       "n": 50,
       "p_fill": 0.0
      }
     },
     "min_n": 30,
     "options": {
      "FADE|nba": {
       "best": "cross",
       "best_net": 0.0099,
       "cross": {
        "ci": [
         -0.0337,
         0.0534
        ],
        "n": 292,
        "net": 0.0099,
        "spread_logged": 292,
        "supported": true
       },
       "no_place": {
        "n": 339,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 1,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0004,
         0.0226
        ],
        "n": 293,
        "n_filled": 14,
        "net": 0.0111,
        "supported": false
       }
      },
      "FADE|nfl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2768,
         0.3786
        ],
        "n": 10,
        "net": 0.0509,
        "spread_logged": 10,
        "supported": false
       },
       "no_place": {
        "n": 15,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0894,
         0.1094
        ],
        "n": 15,
        "n_filled": 2,
        "net": 0.01,
        "supported": false
       }
      },
      "FADE|nhl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.3756,
         0.4815
        ],
        "n": 5,
        "net": 0.0529,
        "spread_logged": 5,
        "supported": false
       },
       "no_place": {
        "n": 5,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 5,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "MODEL_FADE|nba": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1929,
         -0.0627
        ],
        "n": 120,
        "net": -0.1278,
        "spread_logged": 120,
        "supported": true
       },
       "no_place": {
        "n": 188,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0133,
         0.0035
        ],
        "n": 120,
        "n_filled": 2,
        "net": -0.0049,
        "supported": false
       }
      },
      "MODEL_FADE|nhl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.8199,
         0.415
        ],
        "n": 2,
        "net": -0.2024,
        "spread_logged": 2,
        "supported": false
       },
       "no_place": {
        "n": 25,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 2,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "MOMENTUM|nba": {
       "best": "rest_touch",
       "best_net": 0.0133,
       "cross": {
        "ci": [
         -0.094,
         0.0042
        ],
        "n": 305,
        "net": -0.0449,
        "spread_logged": 305,
        "supported": true
       },
       "no_place": {
        "n": 332,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0057,
         0.0323
        ],
        "n": 305,
        "n_filled": 56,
        "net": 0.0133,
        "supported": true
       }
      },
      "MOMENTUM|nfl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         null,
         null
        ],
        "n": 1,
        "net": -0.1274,
        "spread_logged": 1,
        "supported": false
       },
       "no_place": {
        "n": 1,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         null,
         null
        ],
        "n": 1,
        "n_filled": 1,
        "net": -0.11,
        "supported": false
       }
      },
      "MOMENTUM|nhl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.7293,
         1.0898
        ],
        "n": 2,
        "net": 0.1802,
        "spread_logged": 2,
        "supported": false
       },
       "no_place": {
        "n": 7,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 2,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|nba": {
       "best": "cross",
       "best_net": 0.0095,
       "cross": {
        "ci": [
         -0.0291,
         0.0482
        ],
        "n": 323,
        "net": 0.0095,
        "spread_logged": 323,
        "supported": true
       },
       "no_place": {
        "n": 331,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0186,
         0.0073
        ],
        "n": 324,
        "n_filled": 26,
        "net": -0.0056,
        "supported": false
       }
      },
      "RIDE|nfl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.0577,
         0.2332
        ],
        "n": 22,
        "net": 0.0878,
        "spread_logged": 22,
        "supported": false
       },
       "no_place": {
        "n": 47,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0113,
         0.0985
        ],
        "n": 47,
        "n_filled": 13,
        "net": 0.0436,
        "supported": false
       }
      },
      "RIDE|nhl": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1559,
         0.0661
        ],
        "n": 40,
        "net": -0.0449,
        "spread_logged": 40,
        "supported": true
       },
       "no_place": {
        "n": 50,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 40,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      }
     },
     "selection": {
      "FADE|nba": {
       "edge_filled": 0.2321,
       "edge_filled_ci": [
        0.0143,
        0.4499
       ],
       "edge_unfilled": 0.0286,
       "edge_unfilled_ci": [
        -0.0153,
        0.0724
       ],
       "n_filled": 14,
       "n_unfilled": 280,
       "selection": 0.2036,
       "selection_ci": [
        -0.0186,
        0.4257
       ],
       "supported": false,
       "win_filled": 0.4286,
       "win_unfilled": 0.1786
      },
      "FADE|nfl": {
       "edge_filled": 0.075,
       "edge_filled_ci": [
        -0.9344,
        1.0844
       ],
       "edge_unfilled": 0.1023,
       "edge_unfilled_ci": [
        -0.1848,
        0.3894
       ],
       "n_filled": 2,
       "n_unfilled": 13,
       "selection": -0.0273,
       "selection_ci": [
        -1.0767,
        1.0221
       ],
       "supported": false,
       "win_filled": 0.5,
       "win_unfilled": 0.4615
      },
      "FADE|nhl": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.08,
       "edge_unfilled_ci": [
        -0.3484,
        0.5084
       ],
       "n_filled": 0,
       "n_unfilled": 5,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.4
      },
      "MODEL_FADE|nba": {
       "edge_filled": -0.295,
       "edge_filled_ci": [
        -0.7164,
        0.1264
       ],
       "edge_unfilled": -0.0862,
       "edge_unfilled_ci": [
        -0.1517,
        -0.0207
       ],
       "n_filled": 2,
       "n_unfilled": 118,
       "selection": -0.2088,
       "selection_ci": [
        -0.6353,
        0.2176
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.3305
      },
      "MODEL_FADE|nhl": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.18,
       "edge_unfilled_ci": [
        -0.7876,
        0.4276
       ],
       "n_filled": 0,
       "n_unfilled": 2,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5
      },
      "MOMENTUM|nba": {
       "edge_filled": 0.0727,
       "edge_filled_ci": [
        -0.0301,
        0.1755
       ],
       "edge_unfilled": -0.0322,
       "edge_unfilled_ci": [
        -0.0873,
        0.0229
       ],
       "n_filled": 56,
       "n_unfilled": 249,
       "selection": 0.1049,
       "selection_ci": [
        -0.0117,
        0.2215
       ],
       "supported": true,
       "win_filled": 0.5,
       "win_unfilled": 0.4378
      },
      "MOMENTUM|nfl": {
       "edge_filled": -0.11,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": null,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 1,
       "n_unfilled": 0,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": null
      },
      "MOMENTUM|nhl": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.205,
       "edge_unfilled_ci": [
        -0.7064,
        1.1164
       ],
       "n_filled": 0,
       "n_unfilled": 2,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5
      },
      "RIDE|nba": {
       "edge_filled": -0.0704,
       "edge_filled_ci": [
        -0.2327,
        0.0919
       ],
       "edge_unfilled": 0.0638,
       "edge_unfilled_ci": [
        0.0245,
        0.103
       ],
       "n_filled": 26,
       "n_unfilled": 298,
       "selection": -0.1341,
       "selection_ci": [
        -0.3011,
        0.0328
       ],
       "supported": false,
       "win_filled": 0.6154,
       "win_unfilled": 0.8356
      },
      "RIDE|nfl": {
       "edge_filled": 0.1577,
       "edge_filled_ci": [
        -0.0322,
        0.3476
       ],
       "edge_unfilled": -0.0806,
       "edge_unfilled_ci": [
        -0.2187,
        0.0575
       ],
       "n_filled": 13,
       "n_unfilled": 34,
       "selection": 0.2383,
       "selection_ci": [
        0.0035,
        0.4731
       ],
       "supported": false,
       "win_filled": 0.8462,
       "win_unfilled": 0.7647
      },
      "RIDE|nhl": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0227,
       "edge_unfilled_ci": [
        -0.1339,
        0.0884
       ],
       "n_filled": 0,
       "n_unfilled": 40,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.8
      }
     }
    },
    "n": 1340
   },
   "pre_epoch_yes_only": {
    "by_arm": {
     "by": [
      "arm"
     ],
     "fill": {},
     "min_n": 30,
     "options": {},
     "selection": {}
    },
    "by_arm_leaf": {
     "by": [
      "arm",
      "leaf"
     ],
     "cells_below_min_orders_dropped": 0,
     "fill": {},
     "min_n": 30,
     "options": {},
     "selection": {}
    },
    "by_arm_sport": {
     "by": [
      "arm",
      "sport"
     ],
     "fill": {},
     "min_n": 30,
     "options": {},
     "selection": {}
    },
    "n": 0
   }
  },
  "spread_coverage": {
   "post_epoch_all_sides": {
    "backfilled_archive": 454,
    "logged": 854,
    "no_spread": 32,
    "orders": 1340
   },
   "pre_epoch_yes_only": {
    "backfilled_archive": 0,
    "logged": 0,
    "no_spread": 0,
    "orders": 0
   }
  }
 },
 "last_row_ts": "2026-11-19T03:27:48Z",
 "read_utc": "2026-11-19T04:20:43Z",
 "rows": 81761,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
