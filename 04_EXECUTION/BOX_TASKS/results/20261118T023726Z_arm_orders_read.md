# Box task `arm_orders_read` — 20261118T023726Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T023726Z_arm_orders_read.toml`
- note: W117.1 B-095 re-read: spread_logged, skips by reason, E1-E3 per arm before caps flip.
- ran: 2026-11-18T02:38:39Z on root@157.230.91.33:/opt/prediction-market-bot
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
    "skips": 1769
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 15,
    "skips": 713
   },
   "post_epoch_all_sides|FADE|NHL": {
    "orders": 2,
    "skips": 142
   },
   "post_epoch_all_sides|MODEL_FADE|NHL": {
    "skips": 17
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 94,
    "skips": 2290
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
    "skips": 36648
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 7926
   },
   "post_epoch_all_sides|NO_BET|NHL": {
    "skips": 788
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 213,
    "skips": 2705,
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
    "size_zero:cap binds, stake 0: day": 2040,
    "size_zero:cap binds, stake 0: event": 490
   },
   "post_epoch_all_sides|MODEL_FADE": {
    "size_zero:cap binds, stake 0: day": 17
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 2046,
    "size_zero:cap binds, stake 0: event": 316
   },
   "post_epoch_all_sides|NO_BET": {
    "no_bet": 45362
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "side_unavailable_or_disagrees": 12,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 5039,
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
  "join_health": {
   "fill_status_unknown": 0,
   "lookups_failed": 0,
   "orders": 486,
   "pending": 54,
   "resolved": 432,
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
    "E3_win_rate_nonfills_counterfactual": 0.383,
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
    "n_nonfills_resolved": 94,
    "n_settled_fills": 6,
    "placement": null
   },
   "MOMENTUM|post_epoch_all_sides": {
    "E1_fills": 20,
    "E1_orders": 96,
    "E2_per_filled_contract_after_fees": 0.0748,
    "E2_per_filled_contract_before_fees": 0.0875,
    "E3_win_rate_fills": 0.5,
    "E3_win_rate_nonfills_counterfactual": 0.5,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.2083,
    "markout_mean": {
     "close": -0.0083,
     "h1": -0.0097,
     "h30": -0.01,
     "h5": -0.0117,
     "settle": 0.0875
    },
    "markout_n": {
     "close": 9,
     "h1": 20,
     "h30": 4,
     "h5": 6,
     "settle": 16
    },
    "n_nonfills_resolved": 60,
    "n_settled_fills": 16,
    "placement": null
   },
   "RIDE|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 279,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8111,
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
    "n_nonfills_resolved": 217,
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
    "E3_win_rate_nonfills_counterfactual": 0.383,
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
    "n_nonfills_resolved": 94,
    "n_settled_fills": 6,
    "placement": "rest_touch"
   },
   "MOMENTUM|rest_touch|post_epoch_all_sides": {
    "E1_fills": 20,
    "E1_orders": 96,
    "E2_per_filled_contract_after_fees": 0.0748,
    "E2_per_filled_contract_before_fees": 0.0875,
    "E3_win_rate_fills": 0.5,
    "E3_win_rate_nonfills_counterfactual": 0.5,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.2083,
    "markout_mean": {
     "close": -0.0083,
     "h1": -0.0097,
     "h30": -0.01,
     "h5": -0.0117,
     "settle": 0.0875
    },
    "markout_n": {
     "close": 9,
     "h1": 20,
     "h30": 4,
     "h5": 6,
     "settle": 16
    },
    "n_nonfills_resolved": 60,
    "n_settled_fills": 16,
    "placement": "rest_touch"
   },
   "RIDE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 39,
    "E1_orders": 279,
    "E2_per_filled_contract_after_fees": -0.0081,
    "E2_per_filled_contract_before_fees": 0.0056,
    "E3_win_rate_fills": 0.6923,
    "E3_win_rate_nonfills_counterfactual": 0.8111,
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
    "n_nonfills_resolved": 217,
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
       "best_net": 0.1831,
       "cross": {
        "ci": [
         0.0889,
         0.2773
        ],
        "n": 100,
        "net": 0.1831,
        "spread_logged": 0,
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
         -0.0149,
         0.0289
        ],
        "n": 100,
        "n_filled": 6,
        "net": 0.007,
        "supported": false
       }
      },
      "MOMENTUM": {
       "best": "cross",
       "best_net": 0.0203,
       "cross": {
        "ci": [
         -0.0907,
         0.1313
        ],
        "n": 76,
        "net": 0.0203,
        "spread_logged": 0,
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
         -0.0296,
         0.0664
        ],
        "n": 76,
        "n_filled": 16,
        "net": 0.0184,
        "supported": false
       }
      },
      "RIDE": {
       "best": "cross",
       "best_net": 0.0231,
       "cross": {
        "ci": [
         -0.0226,
         0.0689
        ],
        "n": 256,
        "net": 0.0231,
        "spread_logged": 0,
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
         -0.0185,
         0.0202
        ],
        "n": 256,
        "n_filled": 39,
        "net": 0.0009,
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
       "edge_unfilled": 0.2184,
       "edge_unfilled_ci": [
        0.1209,
        0.3159
       ],
       "n_filled": 6,
       "n_unfilled": 94,
       "selection": -0.1017,
       "selection_ci": [
        -0.4994,
        0.2959
       ],
       "supported": false,
       "win_filled": 0.3333,
       "win_unfilled": 0.383
      },
      "MOMENTUM": {
       "edge_filled": 0.0875,
       "edge_filled_ci": [
        -0.1431,
        0.3181
       ],
       "edge_unfilled": 0.0462,
       "edge_unfilled_ci": [
        -0.0811,
        0.1735
       ],
       "n_filled": 16,
       "n_unfilled": 60,
       "selection": 0.0413,
       "selection_ci": [
        -0.2221,
        0.3048
       ],
       "supported": false,
       "win_filled": 0.5,
       "win_unfilled": 0.5
      },
      "RIDE": {
       "edge_filled": 0.0056,
       "edge_filled_ci": [
        -0.1229,
        0.1341
       ],
       "edge_unfilled": 0.0631,
       "edge_unfilled_ci": [
        0.0143,
        0.1119
       ],
       "n_filled": 39,
       "n_unfilled": 217,
       "selection": -0.0575,
       "selection_ci": [
        -0.195,
        0.08
       ],
       "supported": true,
       "win_filled": 0.6923,
       "win_unfilled": 0.8111
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
       "best_net": 0.2384,
       "cross": {
        "ci": [
         0.1124,
         0.3644
        ],
        "n": 51,
        "net": 0.2384,
        "spread_logged": 0,
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
         -0.0216,
         0.0431
        ],
        "n": 51,
        "n_filled": 4,
        "net": 0.0108,
        "supported": false
       }
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.208,
         0.1058
        ],
        "n": 13,
        "net": -0.0511,
        "spread_logged": 0,
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
         0.0339,
         0.2011
        ],
        "n": 2,
        "net": 0.1175,
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
         -0.0912,
         0.2812
        ],
        "n": 2,
        "n_filled": 1,
        "net": 0.095,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_SPREAD|T3|3|up": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.1431,
         0.5811
        ],
        "n": 11,
        "net": 0.3621,
        "spread_logged": 0,
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
         0.0643,
         0.4647
        ],
        "n": 11,
        "n_filled": 7,
        "net": 0.2645,
        "supported": false
       }
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2797,
         0.1201
        ],
        "n": 24,
        "net": -0.0798,
        "spread_logged": 0,
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
        "n": 24,
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
         -0.112,
         0.4579
        ],
        "n": 12,
        "net": 0.173,
        "spread_logged": 0,
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
         -0.4499,
         0.144
        ],
        "n": 12,
        "net": -0.1529,
        "spread_logged": 0,
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
         -0.3818,
         0.2612
        ],
        "n": 10,
        "net": -0.0603,
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
      "RIDE|NBA|NBA_SPREAD|T1|3|na": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.0963,
         0.3515
        ],
        "n": 11,
        "net": 0.1276,
        "spread_logged": 0,
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
      "RIDE|NBA|NBA_SPREAD|T1|4|na": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         0.1374,
         0.2248
        ],
        "n": 14,
        "net": 0.1811,
        "spread_logged": 0,
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
         0.0,
         0.0
        ],
        "n": 14,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|down": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.2131,
         0.263
        ],
        "n": 16,
        "net": 0.025,
        "spread_logged": 0,
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
         -0.2129,
         0.3833
        ],
        "n": 10,
        "net": 0.0852,
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
         0.2542,
         0.2958
        ],
        "n": 14,
        "net": 0.275,
        "spread_logged": 0,
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
         -0.2804,
         0.1682
        ],
        "n": 16,
        "net": -0.0561,
        "spread_logged": 0,
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
         0.0546,
         0.084
        ],
        "n": 44,
        "net": 0.0693,
        "spread_logged": 0,
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
         0.0642,
         0.1166
        ],
        "n": 11,
        "net": 0.0904,
        "spread_logged": 0,
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
         -0.1645,
         0.2397
        ],
        "n": 22,
        "net": 0.0376,
        "spread_logged": 0,
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
        "n": 22,
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
         -0.5236,
         0.036
        ],
        "n": 10,
        "net": -0.2438,
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
         -0.2983,
         0.12
        ],
        "n": 15,
        "net": -0.0892,
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
         0.0695,
         0.1353
        ],
        "n": 10,
        "net": 0.1024,
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
         null,
         null
        ],
        "n": 0,
        "net": null,
        "spread_logged": 0,
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
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
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
       "edge_unfilled": 0.2747,
       "edge_unfilled_ci": [
        0.1421,
        0.4072
       ],
       "n_filled": 4,
       "n_unfilled": 47,
       "selection": -0.1372,
       "selection_ci": [
        -0.6037,
        0.3293
       ],
       "supported": false,
       "win_filled": 0.25,
       "win_unfilled": 0.3404
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
       "edge_unfilled": 0.1,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 1,
       "n_unfilled": 1,
       "selection": 0.09,
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
       "edge_unfilled": 0.3625,
       "edge_unfilled_ci": [
        -0.0976,
        0.8226
       ],
       "n_filled": 7,
       "n_unfilled": 4,
       "selection": 0.0532,
       "selection_ci": [
        -0.4725,
        0.579
       ],
       "supported": false,
       "win_filled": 0.8571,
       "win_unfilled": 0.75
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0429,
       "edge_unfilled_ci": [
        -0.2428,
        0.157
       ],
       "n_filled": 0,
       "n_unfilled": 24,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.4583
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
       "edge_unfilled": 0.0745,
       "edge_unfilled_ci": [
        -0.1275,
        0.2766
       ],
       "n_filled": 0,
       "n_unfilled": 22,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.6364
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
       "edge_unfilled": null,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 0,
       "n_unfilled": 0,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": null
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
       "best_net": 0.2044,
       "cross": {
        "ci": [
         0.104,
         0.3047
        ],
        "n": 85,
        "net": 0.2044,
        "spread_logged": 0,
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
         -0.0129,
         0.0258
        ],
        "n": 85,
        "n_filled": 4,
        "net": 0.0065,
        "supported": false
       }
      },
      "FADE|nfl": {
       "best": null,
       "best_net": null,
       "cross": {
        "ci": [
         -0.204,
         0.3292
        ],
        "n": 15,
        "net": 0.0626,
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
         null,
         null
        ],
        "n": 0,
        "net": null,
        "spread_logged": 0,
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
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       }
      },
      "MOMENTUM|nba": {
       "best": "cross",
       "best_net": 0.0224,
       "cross": {
        "ci": [
         -0.09,
         0.1348
        ],
        "n": 75,
        "net": 0.0224,
        "spread_logged": 0,
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
         -0.0284,
         0.0687
        ],
        "n": 75,
        "n_filled": 15,
        "net": 0.0201,
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
        "net": -0.1379,
        "spread_logged": 0,
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
        "n": 0,
        "net": null,
        "spread_logged": 0,
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
        "n": 0,
        "n_filled": 0,
        "net": null,
        "supported": false
       }
      },
      "RIDE|nba": {
       "best": "cross",
       "best_net": 0.0381,
       "cross": {
        "ci": [
         -0.0114,
         0.0876
        ],
        "n": 209,
        "net": 0.0381,
        "spread_logged": 0,
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
         -0.0288,
         0.0113
        ],
        "n": 209,
        "n_filled": 26,
        "net": -0.0088,
        "supported": false
       }
      },
      "RIDE|nfl": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1591,
         0.0724
        ],
        "n": 47,
        "net": -0.0434,
        "spread_logged": 0,
        "supported": true
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
         null,
         null
        ],
        "n": 0,
        "net": null,
        "spread_logged": 0,
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
         null,
         null
        ],
        "n": 0,
        "n_filled": 0,
        "net": null,
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
       "edge_unfilled": 0.237,
       "edge_unfilled_ci": [
        0.1335,
        0.3405
       ],
       "n_filled": 4,
       "n_unfilled": 81,
       "selection": -0.0995,
       "selection_ci": [
        -0.5586,
        0.3595
       ],
       "supported": false,
       "win_filled": 0.25,
       "win_unfilled": 0.3704
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
       "edge_unfilled": null,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 0,
       "n_unfilled": 0,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": null
      },
      "MOMENTUM|nba": {
       "edge_filled": 0.1007,
       "edge_filled_ci": [
        -0.1443,
        0.3457
       ],
       "edge_unfilled": 0.0462,
       "edge_unfilled_ci": [
        -0.0811,
        0.1735
       ],
       "n_filled": 15,
       "n_unfilled": 60,
       "selection": 0.0545,
       "selection_ci": [
        -0.2216,
        0.3306
       ],
       "supported": false,
       "win_filled": 0.5333,
       "win_unfilled": 0.5
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
       "edge_unfilled": null,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 0,
       "n_unfilled": 0,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": null
      },
      "RIDE|nba": {
       "edge_filled": -0.0704,
       "edge_filled_ci": [
        -0.2327,
        0.0919
       ],
       "edge_unfilled": 0.0898,
       "edge_unfilled_ci": [
        0.0387,
        0.141
       ],
       "n_filled": 26,
       "n_unfilled": 183,
       "selection": -0.1602,
       "selection_ci": [
        -0.3304,
        0.0099
       ],
       "supported": false,
       "win_filled": 0.6154,
       "win_unfilled": 0.8197
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
       "edge_unfilled": null,
       "edge_unfilled_ci": [
        null,
        null
       ],
       "n_filled": 0,
       "n_unfilled": 0,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": null
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
  }
 },
 "last_row_ts": "2026-11-18T02:37:39Z",
 "read_utc": "2026-11-18T02:37:52Z",
 "rows": 69439,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
