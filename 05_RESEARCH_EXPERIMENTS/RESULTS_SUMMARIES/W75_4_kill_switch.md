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

Superseded by "Drill" below (W76.1). Kept: the merge/deploy was read back first.

## Drill (W76.1, 2026-10-15T23:50Z to 2026-10-16T00:14Z, DEMO, run on the VPS) — PASS

**Running code.** `t4-mlb` (systemd) restarted 2026-10-15 05:48:27Z, after the W75.4 files landed at 05:48:24Z, so it runs the one-switch code; no restart was needed. Every other order path is a cron that imports `submit_order` fresh on each launch (the check is inside `KalshiMarketClient.submit_order`). Idle window: demo only, no real capital, no existing cron line, setting or ledger row touched. The flags were written by `/tmp/w76_1_drill.sh` (a shell script that touches then removes flags under `trap` cleanup; log `logs/w76_1_drill_*.log`). Baseline: no `*kill_switch*.flag` in `logs/`.

| Phase | Flag | Window (UTC) | What was asserted | Observed |
|---|---|---|---|---|
| P1 | global `kill_switch.flag` | 23:50:57.154 to 00:01:57.169 | every order path halts; nothing placed | `t4-mlb`: first `T4-MLB kill switch armed — sleeping 10s` at **23:51:26.6 (29.5 s after touch)**, repeating every 10 s. Shadow stake cron (T2 slot 23:5x/00:0x): **72 `shadow_skip reason=kill_switch_halted` (first 23:58:05.9, last 23:58:12.7), 0 `shadow_order` in the window.** Direct `submit_order` probe at 23:58:14.7 on a deliberately non-existent ticker (`KXZZZ-W76PROBE-NOSUCH`), five caller labels: unlabeled, `t1_mlb`, `t1_nba`, `shadow`, `t4_mlb` all returned `status=halted, error=kill_switch_halted:kill_switch_flag:kill_switch.flag` in **19 to 37 ms**, no HTTP request made. |
| P2 | band `kill_switch_t4_mlb.flag` | 00:01:57.174 to 00:12:57.191 | halts only `t4_mlb` | `t4-mlb` armed throughout (last 00:12:50). Probe at 00:08:32: unlabeled and `t4_mlb` **halted** (18 and 21 ms); `t1_mlb`, `t1_nba`, `shadow` **not halted** (they reached the exchange and got HTTP 404 on the fake ticker, 113 to 116 ms, nothing placed). Shadow cron in the window: 42 `shadow_order` attempts, 0 `kill_switch_halted` skips (all 42 rejected `insufficient_balance`, GG-840, not a halt). |
| P3 | none | 00:12:57 to 00:14:27 (+ read at 00:17) | removal resumes | `t4-mlb` first ESPN poll **00:13:04.5 (7.3 s after removal)**, first full evaluation cycle `C0143` 00:13:35; shadow cron placed its next order attempt 00:16:24.6 (the next cron slot; rejected `insufficient_balance`). `ls logs/*.flag`: none left. |

**Result.** NFR-03 halt within 60 s: worst observed 29.5 s (`t4-mlb`, bounded by its 10 s loop plus the in-flight cycle); cron paths check at call time (milliseconds). Global flag halts every running order path; a band flag halts only its band; removal resumes. Order paths proven on the running processes: `t4-mlb` (systemd, loop check), shadow-stake crons (in-process `maybe_place`), and the `submit_order` funnel for all five caller labels (T1 NBA and T1 MLB crons are the `t1_nba`/`t1_mlb` labels of the same funnel; no T1 cron fired inside the window, so they are proven at the funnel, not by a cron launch).

**Not exercised, stated plainly.** (1) Cancels are intentionally not gated and no cancel was pending during the window, so "cancels continue under a flag" is by design and by code, not observed. (2) The C7 in-memory trip writing the global flag is covered by the 14 unit tests, not by the drill. (3) The armed message still prints the legacy path `t4_mlb_kill_switch.flag` although any flag halts it (cosmetic, GG-842).

**C7 record.** `kill_switch_drill_result` appended to `logs/audit.jsonl` on the box at 00:18:54Z (event `EVT-3B72CDCB0720`, `passed_sla: true`, `sla_threshold_ms: 60000`, session `W76.1-DRILL`).

**GG-745: RESOLVED** on this pass (all six order paths honour the one switch in code, and the running processes were drilled).
