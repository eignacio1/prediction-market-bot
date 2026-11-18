# Box task `arm_orders_read` — 20261118T004845Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T004845Z_arm_orders_read.toml`
- note: W116.2 after PR 504: join lookups_failed vs 244/432, per-arm E1/E2/E3, selection, option nets
- ran: 2026-11-18T00:52:45Z on root@157.230.91.33:/opt/prediction-market-bot
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
    "skips": 25
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 36547
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 7926
   },
   "post_epoch_all_sides|NO_BET|NHL": {
    "skips": 717
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
    "skips": 657
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
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 2043,
    "size_zero:cap binds, stake 0: event": 316
   },
   "post_epoch_all_sides|NO_BET": {
    "no_bet": 45190
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "side_unavailable_or_disagrees": 12,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 5010,
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
   "E1_fills": 6,
   "E1_orders": 111,
   "E2_pnl_per_filled_contract_before_fees": 0.1166666666666667,
   "E3_win_rate_fills": 0.3333333333333333,
   "E3_win_rate_nonfills_counterfactual": 0.2777777777777778,
   "arm": "FADE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.05405405405405406,
   "lookups_failed": 76,
   "n_nonfills_resolved": 18,
   "n_settled_fills": 6
  },
  "MOMENTUM|post_epoch_all_sides": {
   "E1_fills": 20,
   "E1_orders": 96,
   "E2_pnl_per_filled_contract_before_fees": 0.0875,
   "E3_win_rate_fills": 0.5,
   "E3_win_rate_nonfills_counterfactual": 0.5454545454545454,
   "arm": "MOMENTUM",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.20833333333333334,
   "lookups_failed": 27,
   "n_nonfills_resolved": 33,
   "n_settled_fills": 16
  },
  "RIDE|post_epoch_all_sides": {
   "E1_fills": 39,
   "E1_orders": 279,
   "E2_pnl_per_filled_contract_before_fees": 0.005641025641025643,
   "E3_win_rate_fills": 0.6923076923076923,
   "E3_win_rate_nonfills_counterfactual": 0.8125,
   "arm": "RIDE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.13978494623655913,
   "lookups_failed": 185,
   "n_nonfills_resolved": 32,
   "n_settled_fills": 39
  }
 },
 "fills_note": "ok",
 "gg1771_epoch": "2026-11-06T01:03:42Z",
 "last_row_ts": "2026-11-18T00:51:40Z",
 "read_utc": "2026-11-18T00:51:48Z",
 "rows": 69218,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
