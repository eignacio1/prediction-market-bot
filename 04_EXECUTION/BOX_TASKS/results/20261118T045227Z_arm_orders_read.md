# Box task `arm_orders_read` — 20261118T045227Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T045227Z_arm_orders_read.toml`
- note: W117.1: coverage of archive backfill, clustered cross, skips by reason after caps.
- ran: 2026-11-18T04:54:46Z on root@157.230.91.33:/opt/prediction-market-bot
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
    "orders": 94,
    "skips": 1812
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 15,
    "skips": 713
   },
   "post_epoch_all_sides|FADE|NHL": {
    "orders": 2,
    "skips": 142
   },
   "post_epoch_all_sides|MODEL_FADE|NBA": {
    "skips": 203
   },
   "post_epoch_all_sides|MODEL_FADE|NHL": {
    "skips": 17
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 94,
    "skips": 2354
   },
   "post_epoch_all_sides|MOMENTUM|NFL": {
    "orders": 1,
    "skips": 159
   },
   "post_epoch_all_sides|MOMENTUM|NHL": {
    "orders": 1,
    "skips": 28
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 37509
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 7926
   },
   "post_epoch_all_sides|NO_BET|NHL": {
    "skips": 788
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 213,
    "skips": 2739,
    "would": 95
   },
   "post_epoch_all_sides|RIDE|NFL": {
    "orders": 47,
    "skips": 3073,
    "would": 1
   },
   "post_epoch_all_sides|RIDE|NHL": {
    "orders": 19,
    "skips": 686
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
    "side_unavailable_or_disagrees": 1,
    "size_zero:cap binds, stake 0: day": 2083,
    "size_zero:cap binds, stake 0: event": 490
   },
   "post_epoch_all_sides|MODEL_FADE": {
    "size_zero:cap binds, stake 0: day": 220
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 2110,
    "size_zero:cap binds, stake 0: event": 316
   },
   "post_epoch_all_sides|NO_BET": {
    "no_bet": 46223
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "side_unavailable_or_disagrees": 12,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 5073,
    "size_zero:cap binds, stake 0: event": 775,
    "size_zero:cap binds, stake 0: same_game_cluster": 4
   },
   "post_epoch_all_sides|UNROUTED": {
    "unrouted": 5573
   }
  }
 },
 "fills": {
  "FADE|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 111,
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
  "MOMENTUM|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 96,
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
   "E1_orders": 279,
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
        -0.0159,
        0.3483
       ],
       "n": 105,
       "n_games": 20,
       "net": 0.1662
      },
      "cross_minus_rest": {
       "ci": [
        -0.0261,
        0.3452
       ],
       "n": 105,
       "n_games": 20,
       "net": 0.1596
      },
      "n_no_spread": 6,
      "n_spread_archive": 105,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0156,
        0.029
       ],
       "n": 105,
       "n_games": 20,
       "net": 0.0067
      },
      "rest_touch_all": {
       "ci": [
        -0.0146,
        0.0272
       ],
       "n": 111,
       "n_games": 22,
       "net": 0.0063
      }
     },
     "MOMENTUM": {
      "cross": {
       "ci": [
        -0.0869,
        0.1912
       ],
       "n": 96,
       "n_games": 21,
       "net": 0.0521
      },
      "cross_minus_rest": {
       "ci": [
        -0.0894,
        0.1389
       ],
       "n": 96,
       "n_games": 21,
       "net": 0.0247
      },
      "n_no_spread": 0,
      "n_spread_archive": 96,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0289,
        0.0837
       ],
       "n": 96,
       "n_games": 21,
       "net": 0.0274
      },
      "rest_touch_all": {
       "ci": [
        -0.0289,
        0.0837
       ],
       "n": 96,
       "n_games": 21,
       "net": 0.0274
      }
     },
     "RIDE": {
      "cross": {
       "ci": [
        -0.0568,
        0.0891
       ],
       "n": 253,
       "n_games": 22,
       "net": 0.0161
      },
      "cross_minus_rest": {
       "ci": [
        -0.056,
        0.0889
       ],
       "n": 253,
       "n_games": 22,
       "net": 0.0164
      },
      "n_no_spread": 26,
      "n_spread_archive": 253,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0228,
        0.0222
       ],
       "n": 253,
       "n_games": 22,
       "net": -0.0003
      },
      "rest_touch_all": {
       "ci": [
        -0.0197,
        0.0213
       ],
       "n": 279,
       "n_games": 26,
       "net": 0.0008
      }
     }
    },
    "by_arm_sport": {
     "FADE|nba": {
      "cross": {
       "ci": [
        -0.0409,
        0.3802
       ],
       "n": 93,
       "n_games": 15,
       "net": 0.1696
      },
      "cross_minus_rest": {
       "ci": [
        -0.0497,
        0.3771
       ],
       "n": 93,
       "n_games": 15,
       "net": 0.1637
      },
      "n_no_spread": 1,
      "n_spread_archive": 93,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0138,
        0.0256
       ],
       "n": 93,
       "n_games": 15,
       "net": 0.0059
      },
      "rest_touch_all": {
       "ci": [
        -0.0137,
        0.0254
       ],
       "n": 94,
       "n_games": 15,
       "net": 0.0059
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
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.5833
      },
      "cross_minus_rest": {
       "ci": [
        -Infinity,
        Infinity
       ],
       "n": 2,
       "n_games": 2,
       "net": 0.5833
      },
      "n_no_spread": 0,
      "n_spread_archive": 2,
      "n_spread_logged": 0,
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
        -0.0955,
        0.191
       ],
       "n": 94,
       "n_games": 19,
       "net": 0.0478
      },
      "cross_minus_rest": {
       "ci": [
        -0.0991,
        0.1363
       ],
       "n": 94,
       "n_games": 19,
       "net": 0.0186
      },
      "n_no_spread": 0,
      "n_spread_archive": 94,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0288,
        0.087
       ],
       "n": 94,
       "n_games": 19,
       "net": 0.0291
      },
      "rest_touch_all": {
       "ci": [
        -0.0288,
        0.087
       ],
       "n": 94,
       "n_games": 19,
       "net": 0.0291
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
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": 0.6443
      },
      "cross_minus_rest": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": 0.6443
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
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        null,
        null
       ],
       "n": 1,
       "n_games": 1,
       "net": 0.0
      }
     },
     "RIDE|nba": {
      "cross": {
       "ci": [
        -0.0678,
        0.1028
       ],
       "n": 212,
       "n_games": 16,
       "net": 0.0175
      },
      "cross_minus_rest": {
       "ci": [
        -0.0561,
        0.1084
       ],
       "n": 212,
       "n_games": 16,
       "net": 0.0261
      },
      "n_no_spread": 1,
      "n_spread_archive": 212,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0262,
        0.009
       ],
       "n": 212,
       "n_games": 16,
       "net": -0.0086
      },
      "rest_touch_all": {
       "ci": [
        -0.026,
        0.0088
       ],
       "n": 213,
       "n_games": 17,
       "net": -0.0086
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
        -0.3842,
        0.2196
       ],
       "n": 19,
       "n_games": 4,
       "net": -0.0823
      },
      "cross_minus_rest": {
       "ci": [
        -0.3842,
        0.2196
       ],
       "n": 19,
       "n_games": 4,
       "net": -0.0823
      },
      "n_no_spread": 0,
      "n_spread_archive": 19,
      "n_spread_logged": 0,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 19,
       "n_games": 4,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 19,
       "n_games": 4,
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
   "orders": 486,
   "pending": 0,
   "resolved": 486,
   "void": 0
  },
  "join_note": "ok",
  "per_arm": {
   "FADE|post_epoch_all_sides": {
    "E1_fills": 6,
    "E1_orders": 111,
    "E2_per_filled_contract_after_fees": 0.1064,
    "E2_per_filled_contract_before_fees": 0.1167,
    "E3_win_rate_fills": 0.3333,
    "E3_win_rate_nonfills_counterfactual": 0.3619,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0541,
    "markout_mean": {
     "close": -0.006,
     "h1": -0.0058,
     "h30": -0.005,
     "h5": -0.005,
     "settle": 0.1167
    },
    "markout_n": {
     "close": 5,
     "h1": 6,
     "h30": 4,
     "h5": 2,
     "settle": 6
    },
    "n_nonfills_resolved": 105,
    "n_settled_fills": 6,
    "placement": null
   },
   "MOMENTUM|post_epoch_all_sides": {
    "E1_fills": 20,
    "E1_orders": 96,
    "E2_per_filled_contract_after_fees": 0.1184,
    "E2_per_filled_contract_before_fees": 0.1315,
    "E3_win_rate_fills": 0.6,
    "E3_win_rate_nonfills_counterfactual": 0.5789,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.2083,
    "markout_mean": {
     "close": -0.0015,
     "h1": -0.0097,
     "h30": -0.01,
     "h5": -0.0117,
     "settle": 0.1315
    },
    "markout_n": {
     "close": 13,
     "h1": 20,
     "h30": 4,
     "h5": 6,
     "settle": 20
    },
    "n_nonfills_resolved": 76,
    "n_settled_fills": 20,
    "placement": null
   },
   "RIDE|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 279,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8083,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1398,
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
    "n_nonfills_resolved": 240,
    "n_settled_fills": 39,
    "placement": null
   }
  },
  "per_arm_option": {
   "FADE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 6,
    "E1_orders": 111,
    "E2_per_filled_contract_after_fees": 0.1064,
    "E2_per_filled_contract_before_fees": 0.1167,
    "E3_win_rate_fills": 0.3333,
    "E3_win_rate_nonfills_counterfactual": 0.3619,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0541,
    "markout_mean": {
     "close": -0.006,
     "h1": -0.0058,
     "h30": -0.005,
     "h5": -0.005,
     "settle": 0.1167
    },
    "markout_n": {
     "close": 5,
     "h1": 6,
     "h30": 4,
     "h5": 2,
     "settle": 6
    },
    "n_nonfills_resolved": 105,
    "n_settled_fills": 6,
    "placement": "rest_touch"
   },
   "MOMENTUM|rest_touch|post_epoch_all_sides": {
    "E1_fills": 20,
    "E1_orders": 96,
    "E2_per_filled_contract_after_fees": 0.1184,
    "E2_per_filled_contract_before_fees": 0.1315,
    "E3_win_rate_fills": 0.6,
    "E3_win_rate_nonfills_counterfactual": 0.5789,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.2083,
    "markout_mean": {
     "close": -0.0015,
     "h1": -0.0097,
     "h30": -0.01,
     "h5": -0.0117,
     "settle": 0.1315
    },
    "markout_n": {
     "close": 13,
     "h1": 20,
     "h30": 4,
     "h5": 6,
     "settle": 20
    },
    "n_nonfills_resolved": 76,
    "n_settled_fills": 20,
    "placement": "rest_touch"
   },
   "RIDE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 279,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8083,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1398,
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
    "n_nonfills_resolved": 240,
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
       "fills": 6,
       "hi": 0.1129,
       "lo": 0.025,
       "n": 111,
       "p_fill": 0.0541
      },
      "MOMENTUM": {
       "fills": 20,
       "hi": 0.3,
       "lo": 0.1391,
       "n": 96,
       "p_fill": 0.2083
      },
      "RIDE": {
       "fills": 39,
       "hi": 0.1854,
       "lo": 0.104,
       "n": 279,
       "p_fill": 0.1398
      }
     },
     "min_n": 30,
     "options": {
      "FADE": {
       "best": "cross",
       "best_net": 0.1662,
       "cross": {
        "ci": [
         0.0762,
         0.2562
        ],
        "n": 105,
        "net": 0.1662,
        "spread_logged": 105,
        "supported": true
       },
       "no_place": {
        "n": 111,
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
         -0.0134,
         0.026
        ],
        "n": 111,
        "n_filled": 6,
        "net": 0.0063,
        "supported": false
       }
      },
      "MOMENTUM": {
       "best": "cross",
       "best_net": 0.0521,
       "cross": {
        "ci": [
         -0.0408,
         0.1451
        ],
        "n": 96,
        "net": 0.0521,
        "spread_logged": 96,
        "supported": true
       },
       "no_place": {
        "n": 96,
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
         -0.0124,
         0.0672
        ],
        "n": 96,
        "n_filled": 20,
        "net": 0.0274,
        "supported": false
       }
      },
      "RIDE": {
       "best": "cross",
       "best_net": 0.0161,
       "cross": {
        "ci": [
         -0.0292,
         0.0614
        ],
        "n": 253,
        "net": 0.0161,
        "spread_logged": 253,
        "supported": true
       },
       "no_place": {
        "n": 279,
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
         -0.017,
         0.0186
        ],
        "n": 279,
        "n_filled": 39,
        "net": 0.0008,
        "supported": true
       }
      }
     },
     "selection": {
      "FADE": {
       "edge_filled": 0.1167,
       "edge_filled_ci": [
        -0.2688,
        0.5022
       ],
       "edge_unfilled": 0.1953,
       "edge_unfilled_ci": [
        0.1051,
        0.2855
       ],
       "n_filled": 6,
       "n_unfilled": 105,
       "selection": -0.0787,
       "selection_ci": [
        -0.4746,
        0.3172
       ],
       "supported": false,
       "win_filled": 0.3333,
       "win_unfilled": 0.3619
      },
      "MOMENTUM": {
       "edge_filled": 0.1315,
       "edge_filled_ci": [
        -0.0562,
        0.3192
       ],
       "edge_unfilled": 0.0703,
       "edge_unfilled_ci": [
        -0.036,
        0.1766
       ],
       "n_filled": 20,
       "n_unfilled": 76,
       "selection": 0.0612,
       "selection_ci": [
        -0.1545,
        0.277
       ],
       "supported": false,
       "win_filled": 0.6,
       "win_unfilled": 0.5789
      },
      "RIDE": {
       "edge_filled": 0.0056,
       "edge_filled_ci": [
        -0.1229,
        0.1341
       ],
       "edge_unfilled": 0.0517,
       "edge_unfilled_ci": [
        0.0047,
        0.0986
       ],
       "n_filled": 39,
       "n_unfilled": 240,
       "selection": -0.046,
       "selection_ci": [
        -0.1828,
        0.0908
       ],
       "supported": true,
       "win_filled": 0.6923,
       "win_unfilled": 0.8083
      }
     }
    },
    "by_arm_leaf": {
     "by": [
      "arm",
      "leaf"
     ],
     "cells_below_min_orders_dropped": 35,
     "fill": {
      "FADE|NBA|NBA_SPREAD|T3|4|flat": {
       "fills": 4,
       "hi": 0.167,
       "lo": 0.0276,
       "n": 57,
       "p_fill": 0.0702
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "fills": 0,
       "hi": 0.2281,
       "lo": 0.0,
       "n": 13,
       "p_fill": 0.0
      },
      "MOMENTUM|NBA|NBA_GAME_TOTAL|T3|4|down": {
       "fills": 1,
       "hi": 0.4042,
       "lo": 0.0179,
       "n": 10,
       "p_fill": 0.1
      },
      "MOMENTUM|NBA|NBA_SPREAD|T3|3|up": {
       "fills": 7,
       "hi": 0.8067,
       "lo": 0.3195,
       "n": 12,
       "p_fill": 0.5833
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "fills": 0,
       "hi": 0.117,
       "lo": 0.0,
       "n": 29,
       "p_fill": 0.0
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|up": {
       "fills": 0,
       "hi": 0.2425,
       "lo": 0.0,
       "n": 12,
       "p_fill": 0.0
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T3|3|flat": {
       "fills": 3,
       "hi": 0.5323,
       "lo": 0.0889,
       "n": 12,
       "p_fill": 0.25
      },
      "RIDE|NBA|NBA_SPREAD|T1|2|na": {
       "fills": 0,
       "hi": 0.2775,
       "lo": 0.0,
       "n": 10,
       "p_fill": 0.0
      },
      "RIDE|NBA|NBA_SPREAD|T1|3|na": {
       "fills": 0,
       "hi": 0.2588,
       "lo": 0.0,
       "n": 11,
       "p_fill": 0.0
      },
      "RIDE|NBA|NBA_SPREAD|T1|4|na": {
       "fills": 0,
       "hi": 0.2153,
       "lo": 0.0,
       "n": 14,
       "p_fill": 0.0
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|down": {
       "fills": 4,
       "hi": 0.495,
       "lo": 0.1018,
       "n": 16,
       "p_fill": 0.25
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|flat": {
       "fills": 1,
       "hi": 0.4042,
       "lo": 0.0179,
       "n": 10,
       "p_fill": 0.1
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|down": {
       "fills": 5,
       "hi": 0.6124,
       "lo": 0.1634,
       "n": 14,
       "p_fill": 0.3571
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|flat": {
       "fills": 3,
       "hi": 0.4301,
       "lo": 0.0659,
       "n": 16,
       "p_fill": 0.1875
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|flat": {
       "fills": 2,
       "hi": 0.1513,
       "lo": 0.0126,
       "n": 44,
       "p_fill": 0.0455
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|up": {
       "fills": 0,
       "hi": 0.2588,
       "lo": 0.0,
       "n": 11,
       "p_fill": 0.0
      },
      "RIDE|NBA|NBA_TEAM_TOTAL|T3|2|flat": {
       "fills": 0,
       "hi": 0.1287,
       "lo": 0.0,
       "n": 26,
       "p_fill": 0.0
      },
      "RIDE|NFL|NFL_GAME_TOTAL|T1|4|na": {
       "fills": 0,
       "hi": 0.2775,
       "lo": 0.0,
       "n": 10,
       "p_fill": 0.0
      },
      "RIDE|NFL|NFL_SPREAD|T1|4|na": {
       "fills": 2,
       "hi": 0.3788,
       "lo": 0.0374,
       "n": 15,
       "p_fill": 0.1333
      },
      "RIDE|NFL|NFL_SPREAD|T3|4|flat": {
       "fills": 4,
       "hi": 0.6873,
       "lo": 0.1682,
       "n": 10,
       "p_fill": 0.4
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T3|4|flat": {
       "fills": 0,
       "hi": 0.1759,
       "lo": 0.0,
       "n": 18,
       "p_fill": 0.0
      }
     },
     "min_n": 30,
     "options": {
      "FADE|NBA|NBA_SPREAD|T3|4|flat": {
       "best": "cross",
       "best_net": 0.2082,
       "cross": {
        "ci": [
         0.0905,
         0.3259
        ],
        "n": 56,
        "net": 0.2082,
        "spread_logged": 56,
        "supported": true
       },
       "no_place": {
        "n": 57,
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
         -0.0193,
         0.0386
        ],
        "n": 57,
        "n_filled": 4,
        "net": 0.0096,
        "supported": false
       }
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2254,
         0.0861
        ],
        "n": 13,
        "net": -0.0697,
        "spread_logged": 13,
        "supported": false
       },
       "no_place": {
        "n": 13,
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
        "n": 13,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_GAME_TOTAL|T3|4|down": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.0676,
         0.1219
        ],
        "n": 10,
        "net": 0.0948,
        "spread_logged": 10,
        "supported": false
       },
       "no_place": {
        "n": 10,
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
         -0.0182,
         0.0562
        ],
        "n": 10,
        "n_filled": 1,
        "net": 0.019,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_SPREAD|T3|3|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.0125,
         0.5438
        ],
        "n": 12,
        "net": 0.2782,
        "spread_logged": 12,
        "supported": false
       },
       "no_place": {
        "n": 12,
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
         0.0547,
         0.4303
        ],
        "n": 12,
        "n_filled": 7,
        "net": 0.2425,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.201,
         0.155
        ],
        "n": 29,
        "net": -0.023,
        "spread_logged": 29,
        "supported": false
       },
       "no_place": {
        "n": 29,
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
        "n": 29,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.1117,
         0.4643
        ],
        "n": 12,
        "net": 0.1763,
        "spread_logged": 12,
        "supported": false
       },
       "no_place": {
        "n": 12,
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
        "n": 12,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T3|3|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.45,
         0.1441
        ],
        "n": 12,
        "net": -0.1529,
        "spread_logged": 12,
        "supported": false
       },
       "no_place": {
        "n": 12,
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
         -0.2391,
         0.0791
        ],
        "n": 12,
        "n_filled": 3,
        "net": -0.08,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T1|2|na": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.4862,
         0.1645
        ],
        "n": 10,
        "net": -0.1608,
        "spread_logged": 10,
        "supported": false
       },
       "no_place": {
        "n": 10,
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
        "n": 10,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T1|3|na": {
  

[... 1453 bytes cut ...]

       "ci": [
         -0.2061,
         0.2684
        ],
        "n": 16,
        "net": 0.0312,
        "spread_logged": 16,
        "supported": false
       },
       "no_place": {
        "n": 16,
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
         -0.2604,
         -0.0171
        ],
        "n": 16,
        "n_filled": 4,
        "net": -0.1387,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.209,
         0.3834
        ],
        "n": 10,
        "net": 0.0872,
        "spread_logged": 10,
        "supported": false
       },
       "no_place": {
        "n": 10,
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
         -0.1717,
         0.0557
        ],
        "n": 10,
        "n_filled": 1,
        "net": -0.058,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|down": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.2577,
         0.3007
        ],
        "n": 14,
        "net": 0.2792,
        "spread_logged": 14,
        "supported": false
       },
       "no_place": {
        "n": 14,
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
         0.0276,
         0.1853
        ],
        "n": 14,
        "n_filled": 5,
        "net": 0.1064,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|3|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.278,
         0.1705
        ],
        "n": 16,
        "net": -0.0537,
        "spread_logged": 16,
        "supported": false
       },
       "no_place": {
        "n": 16,
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
         -0.0028,
         0.0978
        ],
        "n": 16,
        "n_filled": 3,
        "net": 0.0475,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|flat": {
       "best": "cross",
       "best_net": 0.0693,
       "cross": {
        "ci": [
         0.0542,
         0.0843
        ],
        "n": 44,
        "net": 0.0693,
        "spread_logged": 44,
        "supported": true
       },
       "no_place": {
        "n": 44,
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
         -0.0005,
         0.0032
        ],
        "n": 44,
        "n_filled": 2,
        "net": 0.0014,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.0585,
         0.1208
        ],
        "n": 11,
        "net": 0.0896,
        "spread_logged": 11,
        "supported": false
       },
       "no_place": {
        "n": 11,
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
        "n": 11,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_TEAM_TOTAL|T3|2|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.1647,
         0.2145
        ],
        "n": 26,
        "net": 0.0249,
        "spread_logged": 26,
        "supported": false
       },
       "no_place": {
        "n": 26,
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
        "n": 26,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NFL|NFL_GAME_TOTAL|T1|4|na": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "net": null,
        "spread_logged": 0,
        "supported": false
       },
       "no_place": {
        "n": 10,
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
        "n": 10,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NFL|NFL_SPREAD|T1|4|na": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         null,
         null
        ],
        "n": 0,
        "net": null,
        "spread_logged": 0,
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
         -0.0067,
         0.0467
        ],
        "n": 15,
        "n_filled": 2,
        "net": 0.02,
        "supported": false
       }
      },
      "RIDE|NFL|NFL_SPREAD|T3|4|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.0789,
         0.1448
        ],
        "n": 10,
        "net": 0.1119,
        "spread_logged": 10,
        "supported": false
       },
       "no_place": {
        "n": 10,
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
         0.0099,
         0.1141
        ],
        "n": 10,
        "n_filled": 4,
        "net": 0.062,
        "supported": false
       }
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T3|4|flat": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2619,
         0.0861
        ],
        "n": 18,
        "net": -0.0879,
        "spread_logged": 18,
        "supported": false
       },
       "no_place": {
        "n": 18,
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
        "n": 18,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      }
     },
     "selection": {
      "FADE|NBA|NBA_SPREAD|T3|4|flat": {
       "edge_filled": 0.1375,
       "edge_filled_ci": [
        -0.3098,
        0.5848
       ],
       "edge_unfilled": 0.2358,
       "edge_unfilled_ci": [
        0.1147,
        0.357
       ],
       "n_filled": 4,
       "n_unfilled": 53,
       "selection": -0.0983,
       "selection_ci": [
        -0.5617,
        0.365
       ],
       "supported": false,
       "win_filled": 0.25,
       "win_unfilled": 0.3019
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0238,
       "edge_unfilled_ci": [
        -0.1804,
        0.1327
       ],
       "n_filled": 0,
       "n_unfilled": 13,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.0769
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
      "MOMENTUM|NBA|NBA_SPREAD|T3|3|up": {
       "edge_filled": 0.4157,
       "edge_filled_ci": [
        0.1613,
        0.6701
       ],
       "edge_unfilled": 0.154,
       "edge_unfilled_ci": [
        -0.3882,
        0.6962
       ],
       "n_filled": 7,
       "n_unfilled": 5,
       "selection": 0.2617,
       "selection_ci": [
        -0.3372,
        0.8607
       ],
       "supported": false,
       "win_filled": 0.8571,
       "win_unfilled": 0.6
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0103,
       "edge_unfilled_ci": [
        -0.1679,
        0.1886
       ],
       "n_filled": 0,
       "n_unfilled": 29,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5172
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.21,
       "edge_unfilled_ci": [
        -0.075,
        0.495
       ],
       "n_filled": 0,
       "n_unfilled": 12,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.6667
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
       "edge_unfilled": 0.2,
       "edge_unfilled_ci": [
        -0.0861,
        0.4861
       ],
       "n_filled": 1,
       "n_unfilled": 9,
       "selection": -0.78,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.7778
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
       "edge_unfilled": -0.0862,
       "edge_unfilled_ci": [
        -0.3511,
        0.1788
       ],
       "n_filled": 3,
       "n_unfilled": 13,
       "selection": 0.3395,
       "selection_ci": [
        0.0725,
        0.6065
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.6154
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|flat": {
       "edge_filled": 0.03,
       "edge_filled_ci": [
        0.03,
        0.03
       ],
       "edge_unfilled": 0.0969,
       "edge_unfilled_ci": [
        0.0812,
        0.1126
       ],
       "n_filled": 2,
       "n_unfilled": 42,
       "selection": -0.0669,
       "selection_ci": [
        -0.0826,
        -0.0512
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
       "edge_unfilled": 0.1164,
       "edge_unfilled_ci": [
        0.0886,
        0.1441
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
       "win_unfilled": 1.0
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
       "fills": 4,
       "hi": 0.1044,
       "lo": 0.0167,
       "n": 94,
       "p_fill": 0.0426
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
       "hi": 0.6576,
       "lo": 0.0,
       "n": 2,
       "p_fill": 0.0
      },
      "MOMENTUM|nba": {
       "fills": 19,
       "hi": 0.2943,
       "lo": 0.1334,
       "n": 94,
       "p_fill": 0.2021
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
       "hi": 0.7935,
       "lo": 0.0,
       "n": 1,
       "p_fill": 0.0
      },
      "RIDE|nba": {
       "fills": 26,
       "hi": 0.1728,
       "lo": 0.0847,
       "n": 213,
       "p_fill": 0.1221
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
       "hi": 0.1682,
       "lo": 0.0,
       "n": 19,
       "p_fill": 0.0
      }
     },
     "min_n": 30,
     "options": {
      "FADE|nba": {
       "best": "cross",
       "best_net": 0.1696,
       "cross": {
        "ci": [
         0.0749,
         0.2644
        ],
        "n": 93,
        "net": 0.1696,
        "spread_logged": 93,
        "supported": true
       },
       "no_place": {
        "n": 94,
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
         -0.0117,
         0.0234
        ],
        "n": 94,
        "n_filled": 4,
        "net": 0.0059,
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
         0.5236,
         0.6429
        ],
        "n": 2,
        "net": 0.5833,
        "spread_logged": 2,
        "supported": false
       },
       "no_place": {
        "n": 2,
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
       "best": "cross",
       "best_net": 0.0478,
       "cross": {
        "ci": [
         -0.0463,
         0.1418
        ],
        "n": 94,
        "net": 0.0478,
        "spread_logged": 94,
        "supported": true
       },
       "no_place": {
        "n": 94,
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
         -0.0114,
         0.0697
        ],
        "n": 94,
        "n_filled": 19,
        "net": 0.0291,
        "supported": false
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
         null,
         null
        ],
        "n": 1,
        "net": 0.6443,
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
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|nba": {
       "best": "cross",
       "best_net": 0.0175,
       "cross": {
        "ci": [
         -0.0322,
         0.0672
        ],
        "n": 212,
        "net": 0.0175,
        "spread_logged": 212,
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
         -0.0283,
         0.0111
        ],
        "n": 213,
        "n_filled": 26,
        "net": -0.0086,
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
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2472,
         0.0826
        ],
        "n": 19,
        "net": -0.0823,
        "spread_logged": 19,
        "supported": false
       },
       "no_place": {
        "n": 19,
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
        "n": 19,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      }
     },
     "selection": {
      "FADE|nba": {
       "edge_filled": 0.1375,
       "edge_filled_ci": [
        -0.3098,
        0.5848
       ],
       "edge_unfilled": 0.1996,
       "edge_unfilled_ci": [
        0.1033,
        0.2958
       ],
       "n_filled": 4,
       "n_unfilled": 90,
       "selection": -0.0621,
       "selection_ci": [
        -0.5195,
        0.3954
       ],
       "supported": false,
       "win_filled": 0.25,
       "win_unfilled": 0.3333
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
       "edge_unfilled": 0.61,
       "edge_unfilled_ci": [
        0.5512,
        0.6688
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
       "win_unfilled": 1.0
      },
      "MOMENTUM|nba": {
       "edge_filled": 0.1442,
       "edge_filled_ci": [
        -0.0519,
        0.3403
       ],
       "edge_unfilled": 0.0623,
       "edge_unfilled_ci": [
        -0.0443,
        0.1688
       ],
       "n_filled": 19,
       "n_unfilled": 75,
       "selection": 0.0819,
       "selection_ci": [
        -0.1413,
        0.3051
       ],
       "supported": false,
       "win_filled": 0.6316,
       "win_unfilled": 0.5733
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
       "edge_unfilled": 0.67,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 0,
       "n_unfilled": 1,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 1.0
      },
      "RIDE|nba": {
       "edge_filled": -0.0704,
       "edge_filled_ci": [
        -0.2327,
        0.0919
       ],
       "edge_unfilled": 0.0871,
       "edge_unfilled_ci": [
        0.0358,
        0.1384
       ],
       "n_filled": 26,
       "n_unfilled": 187,
       "selection": -0.1575,
       "selection_ci": [
        -0.3277,
        0.0127
       ],
       "supported": false,
       "win_filled": 0.6154,
       "win_unfilled": 0.8128
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
       "edge_unfilled": -0.0605,
       "edge_unfilled_ci": [
        -0.226,
        0.1049
       ],
       "n_filled": 0,
       "n_unfilled": 19,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.8421
      }
     }
    },
    "n": 486
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
    "logged": 0,
    "no_spread": 32,
    "orders": 486
   },
   "pre_epoch_yes_only": {
    "backfilled_archive": 0,
    "logged": 0,
    "no_spread": 0,
    "orders": 0
   }
  }
 },
 "last_row_ts": "2026-11-18T03:45:47Z",
 "read_utc": "2026-11-18T04:52:49Z",
 "rows": 70644,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
