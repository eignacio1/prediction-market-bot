# Box task `arm_orders_read` — 20261113T0044Z_arm_orders_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261113T0044Z_arm_orders_read.toml`
- note: W114.2 B-090: arm-order log E1-E3 per arm
- ran: 2026-11-13T00:45:26Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/arm_orders_read.py`

```
{
 "counts": {
  "per_epoch_arm_sport": {
   "post_epoch_all_sides|ERROR|NBA": {
    "skips": 584
   },
   "post_epoch_all_sides|ERROR|NFL": {
    "skips": 9
   },
   "post_epoch_all_sides|FADE|NBA": {
    "orders": 31,
    "skips": 62
   },
   "post_epoch_all_sides|FADE|NFL": {
    "orders": 6,
    "skips": 32
   },
   "post_epoch_all_sides|MOMENTUM|NBA": {
    "orders": 6,
    "skips": 101
   },
   "post_epoch_all_sides|MOMENTUM|NFL": {
    "orders": 1,
    "skips": 9
   },
   "post_epoch_all_sides|NO_BET|NBA": {
    "skips": 3216
   },
   "post_epoch_all_sides|NO_BET|NFL": {
    "skips": 326
   },
   "post_epoch_all_sides|RIDE|NBA": {
    "orders": 162,
    "skips": 338,
    "would": 95
   },
   "post_epoch_all_sides|RIDE|NFL": {
    "skips": 184,
    "would": 1
   },
   "post_epoch_all_sides|UNROUTED|NHL": {
    "skips": 1415
   }
  },
  "rows_with_unparseable_ts": 0,
  "skip_reasons_per_epoch_arm": {
   "post_epoch_all_sides|ERROR": {
    "unrouted": 593
   },
   "post_epoch_all_sides|FADE": {
    "daily_breaker": 93,
    "size_zero:cap binds, stake 0: event": 1
   },
   "post_epoch_all_sides|MOMENTUM": {
    "daily_breaker": 110
   },
   "post_epoch_all_sides|NO_BET": {
    "no_bet": 3542
   },
   "post_epoch_all_sides|RIDE": {
    "daily_breaker": 487,
    "size_zero:cap binds, stake 0: arm_budget": 31,
    "size_zero:cap binds, stake 0: event": 4
   },
   "post_epoch_all_sides|UNROUTED": {
    "unrouted": 1415
   }
  }
 },
 "fills": {
  "FADE|post_epoch_all_sides": {
   "E1_fills": 1,
   "E1_orders": 37,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "FADE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.02702702702702703,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  },
  "MOMENTUM|post_epoch_all_sides": {
   "E1_fills": 1,
   "E1_orders": 7,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "MOMENTUM",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.14285714285714285,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  },
  "RIDE|post_epoch_all_sides": {
   "E1_fills": 21,
   "E1_orders": 162,
   "E2_pnl_per_filled_contract_before_fees": null,
   "E3_win_rate_fills": null,
   "E3_win_rate_nonfills_counterfactual": null,
   "arm": "RIDE",
   "epoch": "post_epoch_all_sides",
   "fill_rate": 0.12962962962962962,
   "lookups_failed": 0,
   "n_nonfills_resolved": 0,
   "n_settled_fills": 0
  }
 },
 "fills_note": "ok",
 "gg1771_epoch": "2026-11-06T01:03:42Z",
 "last_row_ts": "2026-11-13T00:44:44Z",
 "read_utc": "2026-11-13T00:44:55Z",
 "rows": 6578,
 "source": "/opt/prediction-market-bot/logs/arm_orders/orders.jsonl"
}

```
