# Box task `arm_orders_read` — 20261117T005715Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261117T005715Z_arm_orders_read.toml`
- note: SW-9 Monday 11-16: weekend state before the Fable wave
- ran: 2026-11-17T00:58:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/arm_orders_read.py`

```
{
 "counts": {
  "per_epoch_arm_sport": {
   "post_epoch_all_sides|ERROR|NBA": {
    "skips": 5193
   },
   "post_epoch_all_sides|ERROR|NFL": {
    "skips": 197
   },
   "post_epoch_all_sides|FADE|NBA": {
    "orders": 85,
    "skips": 1566
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 15,
    "skips": 706
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 75,
    "skips": 1957
   },
   "post_epoch_all_sides|MOMENTUM|NFL": {
    "orders": 1,
    "skips": 159
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 31716
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 7905
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 209,
    "skips": 2463,
    "would": 95
   },
   "post_epoch_all_sides|RIDE|NFL": {
    "orders": 47,
    "skips": 3039,
    "would": 1
   },
   "post_epoch_all_sides|UNROUTED|NHL": {
    "skips": 5513
   }
  },
  "rows_with_unparseable_ts": 0,
  "skip_reasons_per_epoch_arm": {
   "post_epoch_all_sides|ERROR": {
    "unrouted": 5390
   },
   "post_epoch_all_sides|FADE": {
    "daily_breaker": 93,
    "side_unavailable_or_disagrees": 1,
    "size_zero:cap binds, stake 0: day": 1703,
    "size_zero:cap binds, stake 0: event": 475
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110,
    "size_zero:cap binds, stake 0: arm_budget": 5,
    "size_zero:cap binds, stake 0: day": 1738,
    "size_zero:cap binds, stake 0: event": 263
   },
   "post_epoch_all_sides|NO_BET": {
    "no_bet": 39621
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "side_unavailable_or_disagrees": 11,
    "size_zero:cap binds, stake 0: arm_budget": 147,
    "size_zero:cap binds, stake 0: day": 4111,
    "size_zero:cap binds, stake 0: event": 746
   },
   "post_epoch_all_sides|UNROUTED": {
    "unrouted": 5513
   }
  }
 },
 "fills": {
  "FADE|post_epoch_all_sides": {
   "E1_fills": 6,
   "E1_orders": 100,
   "E2_pnl_per_filled_contract_before_fees": 0.22500000000000003,
   "E3_win_rate_fills": 0.5,
   "E3_win_rate_nonfills_counterfactual": 0.6818181818181818,
   "arm": "FADE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.06,
   "lookups_failed": 58,
   "n_nonfills_resolved": 22,
   "n_settled_fills": 4
  },
  "MOMENTUM|post_epoch_all_sides": {
   "E1_fills": 16,
   "E1_orders": 76,
   "E2_pnl_per_filled_contract_before_fees": -0.04416666666666667,
   "E3_win_rate_fills": 0.4166666666666667,
   "E3_win_rate_nonfills_counterfactual": 0.65,
   "arm": "MOMENTUM",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.21052631578947367,
   "lookups_failed": 16,
   "n_nonfills_resolved": 20,
   "n_settled_fills": 12
  },
  "RIDE|post_epoch_all_sides": {
   "E1_fills": 39,
   "E1_orders": 256,
   "E2_pnl_per_filled_contract_before_fees": 0.005641025641025643,
   "E3_win_rate_fills": 0.6923076923076923,
   "E3_win_rate_nonfills_counterfactual": 0.5909090909090909,
   "arm": "RIDE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.15234375,
   "lookups_failed": 170,
   "n_nonfills_resolved": 22,
   "n_settled_fills": 39
  }
 },
 "fills_note": "ok",
 "gg1771_epoch": "2026-11-06T01:03:42Z",
 "last_row_ts": "2026-11-17T00:51:50Z",
 "read_utc": "2026-11-17T00:57:39Z",
 "rows": 60942,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
