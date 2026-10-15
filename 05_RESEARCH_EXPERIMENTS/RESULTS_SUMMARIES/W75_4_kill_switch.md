# W75.4 — One kill switch for every order path (GG-745)

Pillar: EXECUTION (PLUMBING in support). Measure: order paths honouring the one switch / all order paths.
Source: `grep -rn "\.submit_order(" src scripts` against origin/main 417344c and this branch.

## Inventory (before)

`KalshiMarketClient.submit_order` is the only order-submitting function in `src/`. Callers:

| # | Order path | Process | Checked before | Flag |
|---|---|---|---|---|
| 1 | `PaperTrader.open_position` -> `submit_order` (T1 NBA, `run_paper_trade.py`) | cron | none inside the funnel; C7 in-memory event only (invisible to cron) | none |
| 2 | same, T1 MLB (`run_mlb_paper_trade.py`) | cron | same | none |
| 3 | same, T4 MLB (`run_t4_mlb_live.py`) | systemd `t4-mlb` | loop-level `kill_switch_armed(path.exists())` | `t4_mlb_kill_switch.flag` only |
| 4 | `shadow_flat_stake.maybe_place` | in-process (T4/pregame shadow) | `halt_reason()` | any `*kill_switch*.flag` (W72.1) |
| 5 | `scripts/w65_2_cancel_canary.py` | manual | none | none |
| 6 | `kalshi_client.py:487` helper | library | none | none |

Honouring a global switch before: **1 of 6** (path 4; path 3 only for its own legacy flag). C7 `trigger_kill_switch` wrote no file, so no cron/systemd process could see it.

## Change

- `kill_switch_state.halt_reason()` now the one check: global `kill_switch.flag` halts everything; `kill_switch_<band>.flag` halts only that band; legacy `t4_mlb_kill_switch.flag` / `t4_kill_switch.flag` read as band aliases; unrecognised flag names and unlabeled callers fail closed; unreadable dir fails closed.
- Check moved INSIDE `submit_order` (before the key check). Returns `KalshiOrder(ok=False, status="halted", error="kill_switch_halted:<reason>")`. A new runner cannot skip it.
- Band labels: `t1_nba`, `t1_mlb`, `t4_mlb`, `shadow`.
- C7 `trigger_kill_switch` (non-drill) writes the global flag; `reset_kill_switch` removes it only if C7 wrote it. Write failure logs CRITICAL, never masks the in-memory halt.
- Design note: legacy `t4_kill_switch.flag` now halts only band `t4`, no longer the shadow staker.
- No change to price, size, side, ticker, stake or kelly.

## Inventory (after, from code)

Honouring the global flag: **6 of 6** (all route through `submit_order`). Proven by `tests/test_w75_4_one_kill_switch.py` (14 tests): every band label and unlabeled caller refused under the global flag; band flag halts only its band; aliases; fail-closed; flag-appears -> next order refused, flag-removed -> resumes; PaperTrader label; t4-mlb loop reads shared state; C7 trip writes / drill does not.
Existing `test_kill_switch_shadow_stake`, `test_gg038_*halt_latency` pass (one assertion in the latter updated: flags are directory-scoped, so the "absent" path must live in an empty directory).

## Part B — drill on the running processes

PENDING (merge, deploy read-back, live DEMO drill in an idle window).
