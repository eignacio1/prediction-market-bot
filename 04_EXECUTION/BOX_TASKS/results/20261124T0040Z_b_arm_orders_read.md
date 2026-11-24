# Box task `arm_orders_read` — 20261124T0040Z_b_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261124T0040Z_b_arm_orders_read.toml`
- note: SW-9: are arm orders still placing? last order time per sport vs the demo-fill stall WARN
- ran: 2026-11-24T00:32:49Z on root@157.230.91.33:/opt/prediction-market-bot
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
    "orders": 599,
    "skips": 2018
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 15,
    "skips": 713
   },
   "post_epoch_all_sides|FADE|NHL": {
    "orders": 49,
    "skips": 207
   },
   "post_epoch_all_sides|MODEL_FADE|NBA": {
    "orders": 756,
    "refused": 45,
    "skips": 682
   },
   "post_epoch_all_sides|MODEL_FADE|NHL": {
    "orders": 97,
    "skips": 84
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 682,
    "skips": 2686
   },
   "post_epoch_all_sides|MOMENTUM|NFL": {
    "orders": 1,
    "skips": 159
   },
   "post_epoch_all_sides|MOMENTUM|NHL": {
    "orders": 40,
    "skips": 37
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 71427
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 21258
   },
   "post_epoch_all_sides|NO_BET|NHL": {
    "skips": 2927
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 573,
    "refused": 2,
    "skips": 3198,
    "would": 95
   },
   "post_epoch_all_sides|RIDE|NFL": {
    "orders": 47,
    "skips": 3073,
    "would": 1
   },
   "post_epoch_all_sides|RIDE|NHL": {
    "orders": 343,
    "skips": 1279
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
    "mid_gap_above_threshold": 7,
    "one_sided_or_crossed_book": 1,
    "side_unavailable_or_disagrees": 3,
    "size_zero:cap binds, stake 0: day": 2083,
    "size_zero:cap binds, stake 0: event": 591,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 3,
    "size_zero:cap binds, stake 0: same_game_cluster": 157
   },
   "post_epoch_all_sides|MODEL_FADE": {
    "mid_gap_above_threshold": 36,
    "not_listed_on_demo": 14,
    "size_zero:cap binds, stake 0: day": 220,
    "size_zero:cap binds, stake 0: event": 177,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 23,
    "size_zero:cap binds, stake 0: same_game_cluster": 296
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "mid_gap_above_threshold": 101,
    "one_sided_or_crossed_book": 29,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 2110,
    "size_zero:cap binds, stake 0: event": 463,
    "size_zero:cap binds, stake 0: same_game_cluster": 64
   },
   "post_epoch_all_sides|NO_BET": {
    "hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D)": 5830,
    "no_bet": 89782
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "mid_gap_above_threshold": 5,
    "one_sided_or_crossed_book": 4,
    "side_unavailable_or_disagrees": 13,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 5073,
    "size_zero:cap binds, stake 0: event": 1217,
    "size_zero:cap binds, stake 0: event,same_game_cluster": 2,
    "size_zero:cap binds, stake 0: same_game_cluster": 602
   },
   "post_epoch_all_sides|UNROUTED": {
    "unrouted": 5573
   }
  }
 },
 "fills": {
  "FADE|post_epoch_all_sides": {
   "E1_fills": null,
   "E1_orders": 663,
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
   "E1_orders": 853,
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
   "E1_orders": 723,
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
   "E1_orders": 963,
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
        -0.0864,
        0.034
       ],
       "n": 564,
       "n_games": 71,
       "net": -0.0262
      },
      "cross_minus_rest": {
       "ci": [
        -0.0884,
        0.0299
       ],
       "n": 564,
       "n_games": 71,
       "net": -0.0293
      },
      "n_no_spread": 6,
      "n_spread_archive": 105,
      "n_spread_logged": 459,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0075,
        0.0136
       ],
       "n": 564,
       "n_games": 71,
       "net": 0.003
      },
      "rest_touch_all": {
       "ci": [
        -0.0074,
        0.0135
       ],
       "n": 570,
       "n_games": 73,
       "net": 0.003
      }
     },
     "MODEL_FADE": {
      "cross": {
       "ci": [
        -0.2097,
        -0.0332
       ],
       "n": 740,
       "n_games": 67,
       "net": -0.1214
      },
      "cross_minus_rest": {
       "ci": [
        -0.2048,
        -0.0383
       ],
       "n": 740,
       "n_games": 67,
       "net": -0.1216
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 740,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.009,
        0.0093
       ],
       "n": 740,
       "n_games": 67,
       "net": 0.0001
      },
      "rest_touch_all": {
       "ci": [
        -0.009,
        0.0093
       ],
       "n": 740,
       "n_games": 67,
       "net": 0.0001
      }
     },
     "MOMENTUM": {
      "cross": {
       "ci": [
        -0.1105,
        0.0803
       ],
       "n": 679,
       "n_games": 71,
       "net": -0.0151
      },
      "cross_minus_rest": {
       "ci": [
        -0.1155,
        0.0534
       ],
       "n": 679,
       "n_games": 71,
       "net": -0.031
      },
      "n_no_spread": 0,
      "n_spread_archive": 96,
      "n_spread_logged": 583,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0053,
        0.0372
       ],
       "n": 679,
       "n_games": 71,
       "net": 0.016
      },
      "rest_touch_all": {
       "ci": [
        -0.0053,
        0.0372
       ],
       "n": 679,
       "n_games": 71,
       "net": 0.016
      }
     },
     "RIDE": {
      "cross": {
       "ci": [
        -0.0424,
        0.0317
       ],
       "n": 906,
       "n_games": 80,
       "net": -0.0053
      },
      "cross_minus_rest": {
       "ci": [
        -0.0422,
        0.0316
       ],
       "n": 906,
       "n_games": 80,
       "net": -0.0053
      },
      "n_no_spread": 26,
      "n_spread_archive": 253,
      "n_spread_logged": 653,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0062,
        0.0061
       ],
       "n": 906,
       "n_games": 80,
       "net": -0.0
      },
      "rest_touch_all": {
       "ci": [
        -0.0057,
        0.0063
       ],
       "n": 932,
       "n_games": 84,
       "net": 0.0003
      }
     }
    },
    "by_arm_sport": {
     "FADE|nba": {
      "cross": {
       "ci": [
        -0.0962,
        0.0374
       ],
       "n": 508,
       "n_games": 42,
       "net": -0.0294
      },
      "cross_minus_rest": {
       "ci": [
        -0.098,
        0.0331
       ],
       "n": 508,
       "n_games": 42,
       "net": -0.0325
      },
      "n_no_spread": 1,
      "n_spread_archive": 93,
      "n_spread_logged": 415,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0085,
        0.0147
       ],
       "n": 508,
       "n_games": 42,
       "net": 0.0031
      },
      "rest_touch_all": {
       "ci": [
        -0.0085,
        0.0146
       ],
       "n": 509,
       "n_games": 42,
       "net": 0.0031
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
        -0.1325,
        0.1172
       ],
       "n": 46,
       "n_games": 26,
       "net": -0.0077
      },
      "cross_minus_rest": {
       "ci": [
        -0.1325,
        0.1172
       ],
       "n": 46,
       "n_games": 26,
       "net": -0.0077
      },
      "n_no_spread": 0,
      "n_spread_archive": 2,
      "n_spread_logged": 44,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 46,
       "n_games": 26,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 46,
       "n_games": 26,
       "net": 0.0
      }
     },
     "MODEL_FADE|nba": {
      "cross": {
       "ci": [
        -0.2313,
        -0.0286
       ],
       "n": 651,
       "n_games": 37,
       "net": -0.1299
      },
      "cross_minus_rest": {
       "ci": [
        -0.2267,
        -0.0358
       ],
       "n": 651,
       "n_games": 37,
       "net": -0.1312
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 651,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0091,
        0.0118
       ],
       "n": 651,
       "n_games": 37,
       "net": 0.0013
      },
      "rest_touch_all": {
       "ci": [
        -0.0091,
        0.0118
       ],
       "n": 651,
       "n_games": 37,
       "net": 0.0013
      }
     },
     "MODEL_FADE|nhl": {
      "cross": {
       "ci": [
        -0.1717,
        0.0532
       ],
       "n": 89,
       "n_games": 30,
       "net": -0.0592
      },
      "cross_minus_rest": {
       "ci": [
        -0.1616,
        0.06
       ],
       "n": 89,
       "n_games": 30,
       "net": -0.0508
      },
      "n_no_spread": 0,
      "n_spread_archive": 0,
      "n_spread_logged": 89,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0207,
        0.0039
       ],
       "n": 89,
       "n_games": 30,
       "net": -0.0084
      },
      "rest_touch_all": {
       "ci": [
        -0.0207,
        0.0039
       ],
       "n": 89,
       "n_games": 30,
       "net": -0.0084
      }
     },
     "MOMENTUM|nba": {
      "cross": {
       "ci": [
        -0.1135,
        0.09
       ],
       "n": 641,
       "n_games": 50,
       "net": -0.0118
      },
      "cross_minus_rest": {
       "ci": [
        -0.1189,
        0.0612
       ],
       "n": 641,
       "n_games": 50,
       "net": -0.0289
      },
      "n_no_spread": 0,
      "n_spread_archive": 94,
      "n_spread_logged": 547,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0056,
        0.0398
       ],
       "n": 641,
       "n_games": 50,
       "net": 0.0171
      },
      "rest_touch_all": {
       "ci": [
        -0.0056,
        0.0398
       ],
       "n": 641,
       "n_games": 50,
       "net": 0.0171
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
        -0.2335,
        0.0954
       ],
       "n": 37,
       "n_games": 20,
       "net": -0.0691
      },
      "cross_minus_rest": {
       "ci": [
        -0.2335,
        0.0954
       ],
       "n": 37,
       "n_games": 20,
       "net": -0.0691
      },
      "n_no_spread": 0,
      "n_spread_archive": 1,
      "n_spread_logged": 36,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 37,
       "n_games": 20,
       "net": 0.0
      },
      "rest_touch_all": {
       "ci": [
        0.0,
        0.0
       ],
       "n": 37,
       "n_games": 20,
       "net": 0.0
      }
     },
     "RIDE|nba": {
      "cross": {
       "ci": [
        -0.0574,
        0.0455
       ],
       "n": 572,
       "n_games": 40,
       "net": -0.006
      },
      "cross_minus_rest": {
       "ci": [
        -0.0534,
        0.0492
       ],
       "n": 572,
       "n_games": 40,
       "net": -0.0021
      },
      "n_no_spread": 1,
      "n_spread_archive": 212,
      "n_spread_logged": 360,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0108,
        0.0031
       ],
       "n": 572,
       "n_games": 40,
       "net": -0.0039
      },
      "rest_touch_all": {
       "ci": [
        -0.0108,
        0.0031
       ],
       "n": 573,
       "n_games": 41,
       "net": -0.0039
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
        -0.0659,
        0.0444
       ],
       "n": 312,
       "n_games": 38,
       "net": -0.0107
      },
      "cross_minus_rest": {
       "ci": [
        -0.0672,
        0.043
       ],
       "n": 312,
       "n_games": 38,
       "net": -0.0121
      },
      "n_no_spread": 0,
      "n_spread_archive": 19,
      "n_spread_logged": 293,
      "no_place": {
       "net": 0.0
      },
      "rest_touch": {
       "ci": [
        -0.0014,
        0.0043
       ],
       "n": 312,
       "n_games": 38,
       "net": 0.0014
      },
      "rest_touch_all": {
       "ci": [
        -0.0014,
        0.0043
       ],
       "n": 312,
       "n_games": 38,
       "net": 0.0014
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
   "orders": 3202,
   "pending": 189,
   "resolved": 3013,
   "void": 0
  },
  "join_note": "ok",
  "per_arm": {
   "FADE|post_epoch_all_sides": {
    "E1_fills": 50,
    "E1_orders": 663,
    "E2_per_filled_contract_after_fees": 0.0177,
    "E2_per_filled_contract_before_fees": 0.0282,
    "E3_win_rate_fills": 0.24,
    "E3_win_rate_nonfills_counterfactual": 0.1699,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0754,
    "markout_mean": {
     "close": 0.0609,
     "h1": 0.0011,
     "h30": 0.001,
     "h5": 0.0194,
     "settle": 0.0282
    },
    "markout_n": {
     "close": 43,
     "h1": 46,
     "h30": 15,
     "h5": 16,
     "settle": 50
    },
    "n_nonfills_resolved": 612,
    "n_settled_fills": 50,
    "placement": null
   },
   "MODEL_FADE|post_epoch_all_sides": {
    "E1_fills": 15,
    "E1_orders": 853,
    "E2_per_filled_contract_after_fees": -0.0069,
    "E2_per_filled_contract_before_fees": 0.0067,
    "E3_win_rate_fills": 0.4,
    "E3_win_rate_nonfills_counterfactual": 0.3186,
    "arm": "MODEL_FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0176,
    "markout_mean": {
     "close": -0.0008,
     "h1": -0.0085,
     "h30": 0.005,
     "settle": 0.0067
    },
    "markout_n": {
     "close": 12,
     "h1": 13,
     "h30": 2,
     "settle": 15
    },
    "n_nonfills_resolved": 725,
    "n_settled_fills": 15,
    "placement": null
   },
   "MOMENTUM|post_epoch_all_sides": {
    "E1_fills": 119,
    "E1_orders": 723,
    "E2_per_filled_contract_after_fees": 0.0877,
    "E2_per_filled_contract_before_fees": 0.0994,
    "E3_win_rate_fills": 0.5872,
    "E3_win_rate_nonfills_counterfactual": 0.4702,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1646,
    "markout_mean": {
     "close": 0.0165,
     "h1": -0.0106,
     "h30": -0.0091,
     "h5": -0.0125,
     "settle": 0.0994
    },
    "markout_n": {
     "close": 58,
     "h1": 119,
     "h30": 11,
     "h5": 14,
     "settle": 109
    },
    "n_nonfills_resolved": 570,
    "n_settled_fills": 109,
    "placement": null
   },
   "RIDE|post_epoch_all_sides": {
    "E1_fills": 42,
    "E1_orders": 963,
    "E2_per_filled_contract_after_fees": -0.0072,
    "E2_per_filled_contract_before_fees": 0.0067,
    "E3_win_rate_fills": 0.6905,
    "E3_win_rate_nonfills_counterfactual": 0.7966,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0436,
    "markout_mean": {
     "close": 0.0011,
     "h1": -0.0128,
     "h30": -0.0044,
     "h5": -0.004,
     "settle": 0.0067
    },
    "markout_n": {
     "close": 32,
     "h1": 40,
     "h30": 9,
     "h5": 10,
     "settle": 42
    },
    "n_nonfills_resolved": 890,
    "n_settled_fills": 42,
    "placement": null
   }
  },
  "per_arm_option": {
   "FADE|rest_inside|post_epoch_all_sides": {
    "E1_fills": 12,
    "E1_orders": 92,
    "E2_per_filled_contract_after_fees": -0.0358,
    "E2_per_filled_contract_before_fees": -0.0258,
    "E3_win_rate_fills": 0.1667,
    "E3_win_rate_nonfills_counterfactual": 0.125,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1304,
    "markout_mean": {
     "close": 0.0805,
     "h1": 0.035,
     "h30": -0.0075,
     "h5": 0.145,
     "settle": -0.0258
    },
    "markout_n": {
     "close": 11,
     "h1": 10,
     "h30": 2,
     "h5": 2,
     "settle": 12
    },
    "n_nonfills_resolved": 80,
    "n_settled_fills": 12,
    "placement": "rest_inside"
   },
   "FADE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 38,
    "E1_orders": 571,
    "E2_per_filled_contract_after_fees": 0.0346,
    "E2_per_filled_contract_before_fees": 0.0453,
    "E3_win_rate_fills": 0.2632,
    "E3_win_rate_nonfills_counterfactual": 0.1767,
    "arm": "FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0665,
    "markout_mean": {
     "close": 0.0542,
     "h1": -0.0083,
     "h30": 0.0023,
     "h5": 0.0014,
     "settle": 0.0453
    },
    "markout_n": {
     "close": 32,
     "h1": 36,
     "h30": 13,
     "h5": 14,
     "settle": 38
    },
    "n_nonfills_resolved": 532,
    "n_settled_fills": 38,
    "placement": "rest_touch"
   },
   "MODEL_FADE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 15,
    "E1_orders": 853,
    "E2_per_filled_contract_after_fees": -0.0069,
    "E2_per_filled_contract_before_fees": 0.0067,
    "E3_win_rate_fills": 0.4,
    "E3_win_rate_nonfills_counterfactual": 0.3186,
    "arm": "MODEL_FADE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0176,
    "markout_mean": {
     "close": -0.0008,
     "h1": -0.0085,
     "h30": 0.005,
     "settle": 0.0067
    },
    "markout_n": {
     "close": 12,
     "h1": 13,
     "h30": 2,
     "settle": 15
    },
    "n_nonfills_resolved": 725,
    "n_settled_fills": 15,
    "placement": "rest_touch"
   },
   "MOMENTUM|rest_touch|post_epoch_all_sides": {
    "E1_fills": 119,
    "E1_orders": 723,
    "E2_per_filled_contract_after_fees": 0.0877,
    "E2_per_filled_contract_before_fees": 0.0994,
    "E3_win_rate_fills": 0.5872,
    "E3_win_rate_nonfills_counterfactual": 0.4702,
    "arm": "MOMENTUM",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.1646,
    "markout_mean": {
     "close": 0.0165,
     "h1": -0.0106,
     "h30": -0.0091,
     "h5": -0.0125,
     "settle": 0.0994
    },
    "markout_n": {
     "close": 58,
     "h1": 119,
     "h30": 11,
     "h5": 14,
     "settle": 109
    },
    "n_nonfills_resolved": 570,
    "n_settled_fills": 109,
    "placement": "rest_touch"
   },
   "RIDE|rest_touch|post_epoch_all_sides": {
    "E1_fills": 42,
    "E1_orders": 963,
    "E2_per_filled_contract_after_fees": -0.0072,
    "E2_per_filled_contract_before_fees": 0.0067,
    "E3_win_rate_fills": 0.6905,
    "E3_win_rate_nonfills_counterfactual": 0.7966,
    "arm": "RIDE",
    "epoch": "post_epoch_all_sides",
    "fill_rate": 0.0436,
    "markout_mean": {
     "close": 0.0011,
     "h1": -0.0128,
     "h30": -0.0044,
     "h5": -0.004,
     "settle": 0.0067
    },
    "markout_n": {
     "close": 32,
     "h1": 40,
     "h30": 9,
     "h5": 10,
     "settle": 42
    },
    "n_nonfills_resolved": 890,
    "n_settled_fills": 42,
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
       "fills": 50,
       "hi": 0.0981,
       "lo": 0.0577,
       "n": 663,
       "p_fill": 0.0754
      },
      "MODEL_FADE": {
       "fills": 15,
       "hi": 0.0288,
       "lo": 0.0107,
       "n": 853,
       "p_fill": 0.0176
      },
      "MOMENTUM": {
       "fills": 119,
       "hi": 0.1934,
       "lo": 0.1393,
       "n": 723,
       "p_fill": 0.1646
      },
      "RIDE": {
       "fills": 42,
       "hi": 0.0584,
       "lo": 0.0324,
       "n": 963,
       "p_fill": 0.0436
      }
     },
     "min_n": 30,
     "options": {
      "FADE": {
       "best": "rest_touch",
       "best_net": 0.003,
       "cross": {
        "ci": [
         -0.0567,
         0.0043
        ],
        "n": 564,
        "net": -0.0262,
        "spread_logged": 564,
        "supported": true
       },
       "no_place": {
        "n": 663,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         -0.0314,
         0.0247
        ],
        "n": 92,
        "n_filled": 12,
        "net": -0.0034,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0056,
         0.0116
        ],
        "n": 570,
        "n_filled": 38,
        "net": 0.003,
        "supported": true
       }
      },
      "MODEL_FADE": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1498,
         -0.0931
        ],
        "n": 740,
        "net": -0.1214,
        "spread_logged": 740,
        "supported": true
       },
       "no_place": {
        "n": 853,
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
         -0.0058,
         0.0061
        ],
        "n": 740,
        "n_filled": 15,
        "net": 0.0001,
        "supported": false
       }
      },
      "MOMENTUM": {
       "best": "rest_touch",
       "best_net": 0.016,
       "cross": {
        "ci": [
         -0.0472,
         0.017
        ],
        "n": 679,
        "net": -0.0151,
        "spread_logged": 679,
        "supported": true
       },
       "no_place": {
        "n": 723,
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
         0.0051,
         0.0269
        ],
        "n": 679,
        "n_filled": 109,
        "net": 0.016,
        "supported": true
       }
      },
      "RIDE": {
       "best": "rest_touch",
       "best_net": 0.0003,
       "cross": {
        "ci": [
         -0.0295,
         0.0188
        ],
        "n": 906,
        "net": -0.0053,
        "spread_logged": 906,
        "supported": true
       },
       "no_place": {
        "n": 963,
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
         -0.0052,
         0.0058
        ],
        "n": 932,
        "n_filled": 42,
        "net": 0.0003,
        "supported": true
       }
      }
     },
     "selection": {
      "FADE": {
       "edge_filled": 0.0282,
       "edge_filled_ci": [
        -0.0836,
        0.14
       ],
       "edge_unfilled": -0.0031,
       "edge_unfilled_ci": [
        -0.0317,
        0.0255
       ],
       "n_filled": 50,
       "n_unfilled": 612,
       "selection": 0.0313,
       "selection_ci": [
        -0.084,
        0.1467
       ],
       "supported": true,
       "win_filled": 0.24,
       "win_unfilled": 0.1699
      },
      "MODEL_FADE": {
       "edge_filled": 0.0067,
       "edge_filled_ci": [
        -0.2965,
        0.3098
       ],
       "edge_unfilled": -0.081,
       "edge_unfilled_ci": [
        -0.1093,
        -0.0528
       ],
       "n_filled": 15,
       "n_unfilled": 725,
       "selection": 0.0877,
       "selection_ci": [
        -0.2167,
        0.3921
       ],
       "supported": false,
       "win_filled": 0.4,
       "win_unfilled": 0.3186
      },
      "MOMENTUM": {
       "edge_filled": 0.0994,
       "edge_filled_ci": [
        0.0334,
        0.1655
       ],
       "edge_unfilled": 0.0025,
       "edge_unfilled_ci": [
        -0.0335,
        0.0384
       ],
       "n_filled": 109,
       "n_unfilled": 570,
       "selection": 0.097,
       "selection_ci": [
        0.0218,
        0.1721
       ],
       "supported": true,
       "win_filled": 0.5872,
       "win_unfilled": 0.4702
      },
      "RIDE": {
       "edge_filled": 0.0067,
       "edge_filled_ci": [
        -0.1178,
        0.1311
       ],
       "edge_unfilled": 0.0287,
       "edge_unfilled_ci": [
        0.0043,
        0.0531
       ],
       "n_filled": 42,
       "n_unfilled": 890,
       "selection": -0.022,
       "selection_ci": [
        -0.1488,
        0.1048
       ],
       "supported": true,
       "win_filled": 0.6905,
       "win_unfilled": 0.7966
      }
     }
    },
    "by_arm_leaf": {
     "by": [
      "arm",
      "leaf"
     ],
     "cells_below_min_orders_dropped": 64,
     "fill": {
      "FADE|NBA|NBA_GAME_TOTAL|T2|3|up": {
       "fills": 6,
       "hi": 0.3439,
       "lo": 0.0861,
       "n": 33,
       "p_fill": 0.1818
      },
      "FADE|NBA|NBA_GAME_TOTAL|T2|4|up": {
       "fills": 0,
       "hi": 0.1246,
       "lo": 0.0,
       "n": 27,
       "p_fill": 0.0
      },
      "FADE|NBA|NBA_GAME_TOTAL|T3|3|up": {
       "fills": 2,
       "hi": 0.3602,
       "lo": 0.035,
       "n": 16,
       "p_fill": 0.125
      },
      "FADE|NBA|NBA_SPREAD|T2|2|flat": {
       "fills": 9,
       "hi": 0.2025,
       "lo": 0.0611,
       "n": 79,
       "p_fill": 0.1139
      },
      "FADE|NBA|NBA_SPREAD|T2|3|down": {
       "fills": 2,
       "hi": 0.1425,
       "lo": 0.0117,
       "n": 47,
       "p_fill": 0.0426
      },
      "FADE|NBA|NBA_SPREAD|T2|4|down": {
       "fills": 3,
       "hi": 0.1236,
       "lo": 0.0153,
       "n": 67,
       "p_fill": 0.0448
      },
      "FADE|NBA|NBA_SPREAD|T3|3|down": {
       "fills": 3,
       "hi": 0.4301,
       "lo": 0.0659,
       "n": 16,
       "p_fill": 0.1875
      },
      "FADE|NBA|NBA_SPREAD|T3|4|flat": {
       "fills": 23,
       "hi": 0.1742,
       "lo": 0.0816,
       "n": 191,
       "p_fill": 0.1204
      },
      "FADE|NBA|NBA_TEAM_TOTAL|T2|4|up": {
       "fills": 0,
       "hi": 0.0303,
       "lo": 0.0,
       "n": 123,
       "p_fill": 0.0
      },
      "FADE|NHL|NHL_GAME_TOTAL|T2|3|flat": {
       "fills": 0,
       "hi": 0.1015,
       "lo": 0.0,
       "n": 34,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|2|na": {
       "fills": 0,
       "hi": 0.0493,
       "lo": 0.0,
       "n": 74,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|3|na": {
       "fills": 0,
       "hi": 0.0475,
       "lo": 0.0,
       "n": 77,
       "p_fill": 0.0
      },
      "MODEL_FADE|NBA|NBA_GAME_TOTAL|T1|4|na": {
       "fills": 0,
       "hi": 0.0131,
       "lo": 0.0

[... 77956 bytes cut ...]

       -0.2054,
        0.0508
       ],
       "n_filled": 0,
       "n_unfilled": 56,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.4107
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T2|3|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0768,
       "edge_unfilled_ci": [
        -0.1873,
        0.0337
       ],
       "n_filled": 0,
       "n_unfilled": 69,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.4493
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|down": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0898,
       "edge_unfilled_ci": [
        -0.0368,
        0.2164
       ],
       "n_filled": 0,
       "n_unfilled": 56,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5893
      },
      "MOMENTUM|NBA|NBA_TEAM_TOTAL|T3|2|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0122,
       "edge_unfilled_ci": [
        -0.1509,
        0.1265
       ],
       "n_filled": 0,
       "n_unfilled": 50,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.46
      },
      "MOMENTUM|NHL|NHL_PUCK_LINE|T2|3|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0933,
       "edge_unfilled_ci": [
        -0.3096,
        0.123
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
       "win_unfilled": 0.1667
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T2|4|down": {
       "edge_filled": 0.2,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0919,
       "edge_unfilled_ci": [
        0.0392,
        0.1447
       ],
       "n_filled": 1,
       "n_unfilled": 52,
       "selection": 0.1081,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.9615
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T3|2|flat": {
       "edge_filled": -0.105,
       "edge_filled_ci": [
        -1.036,
        0.826
       ],
       "edge_unfilled": 0.0437,
       "edge_unfilled_ci": [
        -0.3211,
        0.4086
       ],
       "n_filled": 2,
       "n_unfilled": 8,
       "selection": -0.1487,
       "selection_ci": [
        -1.1487,
        0.8512
       ],
       "supported": false,
       "win_filled": 0.5,
       "win_unfilled": 0.625
      },
      "RIDE|NBA|NBA_GAME_TOTAL|T3|3|flat": {
       "edge_filled": -0.32,
       "edge_filled_ci": [
        -0.96,
        0.32
       ],
       "edge_unfilled": -0.0562,
       "edge_unfilled_ci": [
        -0.2673,
        0.1549
       ],
       "n_filled": 3,
       "n_unfilled": 21,
       "selection": -0.2638,
       "selection_ci": [
        -0.9377,
        0.4101
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
        -0.1771,
        0.1311
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
       "win_unfilled": 0.525
      },
      "RIDE|NBA|NBA_SPREAD|T1|3|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.1932,
       "edge_unfilled_ci": [
        0.08,
        0.3064
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
       "win_unfilled": 0.871
      },
      "RIDE|NBA|NBA_SPREAD|T1|4|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0422,
       "edge_unfilled_ci": [
        -0.0296,
        0.114
       ],
       "n_filled": 0,
       "n_unfilled": 64,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.9219
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|down": {
       "edge_filled": -0.555,
       "edge_filled_ci": [
        -0.572,
        -0.538
       ],
       "edge_unfilled": 0.2024,
       "edge_unfilled_ci": [
        0.0017,
        0.403
       ],
       "n_filled": 4,
       "n_unfilled": 17,
       "selection": -0.7574,
       "selection_ci": [
        -0.9587,
        -0.556
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.7647
      },
      "RIDE|NBA|NBA_SPREAD|T2|2|flat": {
       "edge_filled": -0.58,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.148,
       "edge_unfilled_ci": [
        -0.0801,
        0.3761
       ],
       "n_filled": 1,
       "n_unfilled": 15,
       "selection": -0.728,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.7333
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
       "edge_unfilled": -0.0419,
       "edge_unfilled_ci": [
        -0.2384,
        0.1546
       ],
       "n_filled": 3,
       "n_unfilled": 21,
       "selection": 0.2952,
       "selection_ci": [
        0.0961,
        0.4944
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.6667
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|down": {
       "edge_filled": 0.12,
       "edge_filled_ci": [
        -0.0564,
        0.2964
       ],
       "edge_unfilled": -0.04,
       "edge_unfilled_ci": [
        -0.2127,
        0.1327
       ],
       "n_filled": 2,
       "n_unfilled": 15,
       "selection": 0.16,
       "selection_ci": [
        -0.0869,
        0.4069
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.8667
      },
      "RIDE|NBA|NBA_SPREAD|T2|4|flat": {
       "edge_filled": 0.03,
       "edge_filled_ci": [
        0.03,
        0.03
       ],
       "edge_unfilled": 0.1,
       "edge_unfilled_ci": [
        0.086,
        0.114
       ],
       "n_filled": 2,
       "n_unfilled": 51,
       "selection": -0.07,
       "selection_ci": [
        -0.084,
        -0.056
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
       "edge_unfilled": 0.0193,
       "edge_unfilled_ci": [
        -0.0362,
        0.0749
       ],
       "n_filled": 0,
       "n_unfilled": 119,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.8908
      },
      "RIDE|NBA|NBA_TEAM_TOTAL|T3|2|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0333,
       "edge_unfilled_ci": [
        -0.1768,
        0.1101
       ],
       "n_filled": 0,
       "n_unfilled": 48,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5208
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
      "RIDE|NHL|NHL_GAME_TOTAL|T1|2|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0577,
       "edge_unfilled_ci": [
        -0.3266,
        0.2112
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
       "win_unfilled": 0.4615
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T1|3|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.04,
       "edge_unfilled_ci": [
        -0.2045,
        0.2845
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
       "win_unfilled": 0.75
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T1|4|na": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.1018,
       "edge_unfilled_ci": [
        0.0494,
        0.1543
       ],
       "n_filled": 0,
       "n_unfilled": 38,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.9737
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T2|2|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0341,
       "edge_unfilled_ci": [
        -0.1222,
        0.1904
       ],
       "n_filled": 0,
       "n_unfilled": 39,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.5897
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T2|4|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0282,
       "edge_unfilled_ci": [
        -0.0246,
        0.0809
       ],
       "n_filled": 0,
       "n_unfilled": 87,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.931
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T2|4|up": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0008,
       "edge_unfilled_ci": [
        -0.1507,
        0.1524
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
       "win_unfilled": 0.9167
      },
      "RIDE|NHL|NHL_GAME_TOTAL|T3|4|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.0236,
       "edge_unfilled_ci": [
        -0.1517,
        0.1045
       ],
       "n_filled": 0,
       "n_unfilled": 25,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.88
      },
      "RIDE|NHL|NHL_MONEYLINE|T2|2|flat": {
       "edge_filled": 0.44,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0802,
       "edge_unfilled_ci": [
        -0.0596,
        0.2201
       ],
       "n_filled": 1,
       "n_unfilled": 48,
       "selection": 0.3598,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.625
      },
      "RIDE|NHL|NHL_MONEYLINE|T2|3|flat": {
       "edge_filled": null,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": -0.288,
       "edge_unfilled_ci": [
        -0.618,
        0.042
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
       "win_unfilled": 0.4
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
       "fills": 48,
       "hi": 0.1046,
       "lo": 0.061,
       "n": 599,
       "p_fill": 0.0801
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
       "hi": 0.0727,
       "lo": 0.0,
       "n": 49,
       "p_fill": 0.0
      },
      "MODEL_FADE|nba": {
       "fills": 13,
       "hi": 0.0292,
       "lo": 0.0101,
       "n": 756,
       "p_fill": 0.0172
      },
      "MODEL_FADE|nhl": {
       "fills": 2,
       "hi": 0.0721,
       "lo": 0.0057,
       "n": 97,
       "p_fill": 0.0206
      },
      "MOMENTUM|nba": {
       "fills": 118,
       "hi": 0.2032,
       "lo": 0.1465,
       "n": 682,
       "p_fill": 0.173
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
       "hi": 0.0876,
       "lo": 0.0,
       "n": 40,
       "p_fill": 0.0
      },
      "RIDE|nba": {
       "fills": 28,
       "hi": 0.0697,
       "lo": 0.034,
       "n": 573,
       "p_fill": 0.0489
      },
      "RIDE|nfl": {
       "fills": 13,
       "hi": 0.4176,
       "lo": 0.1694,
       "n": 47,
       "p_fill": 0.2766
      },
      "RIDE|nhl": {
       "fills": 1,
       "hi": 0.0163,
       "lo": 0.0005,
       "n": 343,
       "p_fill": 0.0029
      }
     },
     "min_n": 30,
     "options": {
      "FADE|nba": {
       "best": "rest_touch",
       "best_net": 0.0031,
       "cross": {
        "ci": [
         -0.0607,
         0.0019
        ],
        "n": 508,
        "net": -0.0294,
        "spread_logged": 508,
        "supported": true
       },
       "no_place": {
        "n": 599,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         -0.0321,
         0.0252
        ],
        "n": 90,
        "n_filled": 12,
        "net": -0.0034,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         -0.0062,
         0.0123
        ],
        "n": 509,
        "n_filled": 36,
        "net": 0.0031,
        "supported": true
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
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1346,
         0.1192
        ],
        "n": 46,
        "net": -0.0077,
        "spread_logged": 46,
        "supported": true
       },
       "no_place": {
        "n": 49,
        "net": 0.0
       },
       "rest_inside": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 2,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       },
       "rest_touch": {
        "ci": [
         0.0,
         0.0
        ],
        "n": 46,
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
         -0.1601,
         -0.0998
        ],
        "n": 651,
        "net": -0.1299,
        "spread_logged": 651,
        "supported": true
       },
       "no_place": {
        "n": 756,
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
         -0.0052,
         0.0079
        ],
        "n": 651,
        "n_filled": 13,
        "net": 0.0013,
        "supported": false
       }
      },
      "MODEL_FADE|nhl": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.1421,
         0.0236
        ],
        "n": 89,
        "net": -0.0592,
        "spread_logged": 89,
        "supported": true
       },
       "no_place": {
        "n": 97,
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
         -0.0204,
         0.0036
        ],
        "n": 89,
        "n_filled": 2,
        "net": -0.0084,
        "supported": false
       }
      },
      "MOMENTUM|nba": {
       "best": "rest_touch",
       "best_net": 0.0171,
       "cross": {
        "ci": [
         -0.0447,
         0.0212
        ],
        "n": 641,
        "net": -0.0118,
        "spread_logged": 641,
        "supported": true
       },
       "no_place": {
        "n": 682,
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
         0.0055,
         0.0286
        ],
        "n": 641,
        "n_filled": 108,
        "net": 0.0171,
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
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.2162,
         0.078
        ],
        "n": 37,
        "net": -0.0691,
        "spread_logged": 37,
        "supported": true
       },
       "no_place": {
        "n": 40,
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
        "n": 37,
        "n_filled": 0,
        "net": 0.0,
        "supported": false
       }
      },
      "RIDE|nba": {
       "best": "no_place",
       "best_net": 0.0,
       "cross": {
        "ci": [
         -0.036,
         0.0241
        ],
        "n": 572,
        "net": -0.006,
        "spread_logged": 572,
        "supported": true
       },
       "no_place": {
        "n": 573,
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
         0.0038
        ],
        "n": 573,
        "n_filled": 28,
        "net": -0.0039,
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
         -0.0529,
         0.0314
        ],
        "n": 312,
        "net": -0.0107,
        "spread_logged": 312,
        "supported": true
       },
       "no_place": {
        "n": 343,
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
         -0.0014,
         0.0042
        ],
        "n": 312,
        "n_filled": 1,
        "net": 0.0014,
        "supported": false
       }
      }
     },
     "selection": {
      "FADE|nba": {
       "edge_filled": 0.0262,
       "edge_filled_ci": [
        -0.0863,
        0.1388
       ],
       "edge_unfilled": -0.0066,
       "edge_unfilled_ci": [
        -0.0358,
        0.0227
       ],
       "n_filled": 48,
       "n_unfilled": 551,
       "selection": 0.0328,
       "selection_ci": [
        -0.0834,
        0.149
       ],
       "supported": true,
       "win_filled": 0.2292,
       "win_unfilled": 0.1525
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
       "edge_unfilled": 0.0075,
       "edge_unfilled_ci": [
        -0.1148,
        0.1298
       ],
       "n_filled": 0,
       "n_unfilled": 48,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.2917
      },
      "MODEL_FADE|nba": {
       "edge_filled": 0.0654,
       "edge_filled_ci": [
        -0.2737,
        0.4045
       ],
       "edge_unfilled": -0.0909,
       "edge_unfilled_ci": [
        -0.1208,
        -0.061
       ],
       "n_filled": 13,
       "n_unfilled": 638,
       "selection": 0.1563,
       "selection_ci": [
        -0.1841,
        0.4967
       ],
       "supported": false,
       "win_filled": 0.4615,
       "win_unfilled": 0.2931
      },
      "MODEL_FADE|nhl": {
       "edge_filled": -0.375,
       "edge_filled_ci": [
        -0.5612,
        -0.1888
       ],
       "edge_unfilled": -0.0089,
       "edge_unfilled_ci": [
        -0.0936,
        0.0759
       ],
       "n_filled": 2,
       "n_unfilled": 87,
       "selection": -0.3661,
       "selection_ci": [
        -0.5707,
        -0.1616
       ],
       "supported": false,
       "win_filled": 0.0,
       "win_unfilled": 0.5057
      },
      "MOMENTUM|nba": {
       "edge_filled": 0.1014,
       "edge_filled_ci": [
        0.0349,
        0.1679
       ],
       "edge_unfilled": 0.0056,
       "edge_unfilled_ci": [
        -0.0314,
        0.0427
       ],
       "n_filled": 108,
       "n_unfilled": 533,
       "selection": 0.0958,
       "selection_ci": [
        0.0196,
        0.1719
       ],
       "supported": true,
       "win_filled": 0.5926,
       "win_unfilled": 0.4765
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
       "edge_unfilled": -0.043,
       "edge_unfilled_ci": [
        -0.1903,
        0.1044
       ],
       "n_filled": 0,
       "n_unfilled": 37,
       "selection": null,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": null,
       "win_unfilled": 0.3784
      },
      "RIDE|nba": {
       "edge_filled": -0.0789,
       "edge_filled_ci": [
        -0.2349,
        0.077
       ],
       "edge_unfilled": 0.0407,
       "edge_unfilled_ci": [
        0.0102,
        0.0711
       ],
       "n_filled": 28,
       "n_unfilled": 545,
       "selection": -0.1196,
       "selection_ci": [
        -0.2785,
        0.0393
       ],
       "supported": false,
       "win_filled": 0.6071,
       "win_unfilled": 0.8092
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
       "edge_filled": 0.44,
       "edge_filled_ci": [
        null,
        null
       ],
       "edge_unfilled": 0.0197,
       "edge_unfilled_ci": [
        -0.0226,
        0.062
       ],
       "n_filled": 1,
       "n_unfilled": 311,
       "selection": 0.4203,
       "selection_ci": [
        null,
        null
       ],
       "supported": false,
       "win_filled": 1.0,
       "win_unfilled": 0.7781
      }
     }
    },
    "n": 3202
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
    "logged": 2716,
    "no_spread": 32,
    "orders": 3202
   },
   "pre_epoch_yes_only": {
    "backfilled_archive": 0,
    "logged": 0,
    "no_spread": 0,
    "orders": 0
   }
  }
 },
 "last_row_ts": "2026-11-24T00:27:34Z",
 "read_utc": "2026-11-24T00:27:54Z",
 "rows": 125006,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
