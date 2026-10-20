# Runbook: Kill Switch — Prediction Market Trading Bot

**Class:** LIVING (registered in `00_ADMIN/DOC_REGISTRY.toml`)
**Last verified:** 2026-10-20 against `src/prediction_market_bot/c5_execution/kill_switch_state.py`, `c7_monitoring/monitor.py`, `c5_execution/kalshi_client.py`, `scripts/run_t4_mlb_live.py`, and the W76.1 drill record (`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W75_4_kill_switch.md`).
**Owner (role):** Infrastructure Operator (IO) + Risk & Compliance Officer (RCO)
**Must match:** the flag-file contract in `kill_switch_state.py` and the C7 trigger/reset API in `monitor.py`. If either changes, this file is stale.
**Replaces:** the 2026-05-22 version, which described `python -m bot.kill_switch`, `bot.status` and a SIGTERM/`pkill` procedure. None of those exist. The superseded text is in git history.
**Decision references:** ADR-0001, NFR-03, GG-667, GG-745 (RESOLVED).

---

## What the kill switch is

One mechanism: **flag files in the box's `logs/` directory** (`/opt/prediction-market-bot/logs/`). Every order path asks `halt_reason()` before it acts. If a flag that applies to the caller exists, the order is refused. **Touch a file to halt; remove it to resume.**

| Flag file | Effect |
|---|---|
| `logs/kill_switch.flag` | **GLOBAL.** Halts every order path. |
| `logs/kill_switch_<band>.flag` | Halts only that band. Labels: `t1_nba`, `t1_mlb`, `t4_mlb`, `shadow`. |
| `logs/t4_mlb_kill_switch.flag` | Legacy alias for band `t4_mlb`. |
| `logs/t4_kill_switch.flag` | Legacy alias for band `t4`. |
| any other `*kill_switch*.flag` | Not recognised, so it **fails closed as GLOBAL**. |

Fail-closed rules: a caller with no band label is halted by any flag. An unreadable `logs/` directory halts everything. Cell-level halts (`CellKillSwitchStatus.HALTED` in `market_type_registry`) are a separate, finer switch.

What it does not cover: **order cancels are intentionally not gated**, so a halt never traps a resting order.

Where the check lives: `KalshiMarketClient.submit_order` calls `halt_reason()` itself, before the key check, and returns `KalshiOrder(ok=False, status="halted", error="kill_switch_halted:<reason>")` with no HTTP call. The long-running `t4-mlb` service (`run_t4_mlb_live.py`) also polls the flag on its loop (every 10 s) and logs `T4-MLB kill switch armed — sleeping 10s`. That message names a legacy path and is cosmetic (GG-842).

`PMBOT_KILL_SWITCH_DIR` redirects the flag directory. It is for tests and drills only. Never set it on the production box.

---

## Triggers

**Automatic**
- C4 risk engine returns `STATUS_KILL_SWITCH`: daily loss ≥ `MAX_DAILY_LOSS_PCT` (0.15), drawdown ≥ `max_drawdown_pct` (0.20), or a solvency-invariant breach. The caller then calls C7 `trigger_kill_switch`.
- C6 audit-write failure (`c4 audit`, `c5 write`, `c6 audit`) or an engine exception in `t4_live_runner.py`: `fast_halt.halt` plus a C7 trigger.
- Drift does not trip it alone. Brier L3 only pauses new positions; L4 is not fired by drift (GG-095). See `RUNBOOK_model-drift.md`.

**Manual** — any observed anomaly (wrong fills, runaway order rate, a duplicated order, a credential suspected leaked). When unsure, trip it. Resuming costs one `rm`.

C7 API (`monitor.py`): `trigger_kill_switch(reason, operator, session_id)` sets the in-memory event, writes the global flag, and logs CRITICAL `kill_switch_triggered` with `halt_time_ms` against `KILL_SWITCH_SLA_MS = 60000`. `reset_kill_switch(reason, operator)` clears the event and removes the flag only if C7 wrote it, and logs WARNING `kill_switch_reset`.

---

## Procedure 1 — Trip it by hand

The box bridge (`scripts/box_tasks.py` allowlist) has **no kill-switch task**, so this cannot be done through the bridge. Use ssh:

```bash
ssh prediction-market-vps            # root@157.230.91.33
cd /opt/prediction-market-bot
touch logs/kill_switch.flag          # GLOBAL halt
# or one band only:
touch logs/kill_switch_t4_mlb.flag
```

## Procedure 2 — Verify within 60 s (NFR-03)

```bash
# 1. the flag exists
ls -l /opt/prediction-market-bot/logs/*kill_switch*.flag
# 2. the t4-mlb loop saw it (expect "shadow_skip ... kill_switch_halted" rows, no shadow_order rows)
journalctl -u t4-mlb --since '-2 min' | grep -E 'kill switch|kill_switch_halted' | tail
# 3. cron-driven bands: the next run's audit line should show kill_switch_halted
grep -c kill_switch_halted /opt/prediction-market-bot/logs/audit.jsonl
```

Measured expectation (W76.1 drill, below): the polling service halts in ≤ 30 s worst case; a direct `submit_order` is refused in tens of milliseconds.

## Procedure 3 — Recover

1. Find the cause. Read `logs/audit.jsonl` for `kill_switch_triggered` and its `reason`.
2. **Do not resume a real kill without a written decision in `04_EXECUTION/RID_LOG.md`.** `reset_kill_switch` says the same in its warning.
3. `rm /opt/prediction-market-bot/logs/<the flag you touched>`. Do not remove flags you did not create without reading why they exist.
4. Confirm resume: `journalctl -u t4-mlb --since '-1 min'` shows the loop evaluating again (W76.1: resumed 7.3 s after removal).
5. If C7 wrote the flag, also call `reset_kill_switch` through the operator tooling so the in-memory event clears. A restart of the process clears it too.
6. Log the event in `RID_LOG.md`. A real event that exposed a gap in this file: register a GG and fix this file the same day.

---

## Evidence — W76.1 drill (DEMO, on the box, 2026-10-15T23:50Z–2026-10-16T00:14Z) — PASS

| Check | Result |
|---|---|
| Global flag → `t4-mlb` stops | 29.5 s after touch (worst case; bounded by the 10 s loop plus an in-flight cycle). 72 `shadow_skip reason=kill_switch_halted`, 0 `shadow_order`. |
| Direct `submit_order` probe (fake ticker `KXZZZ-W76PROBE-NOSUCH`), five labels | all halted in 19–37 ms, no HTTP |
| Band flag `t4_mlb` | halted unlabeled and `t4_mlb`; `t1_mlb`, `t1_nba`, `shadow` not halted |
| Flag removed → resume | `t4-mlb` resumed 7.3 s later |
| C7 record | `kill_switch_drill_result` in `logs/audit.jsonl`, 2026-10-16T00:18:54Z, event EVT-3B72CDCB0720, session `W76.1-DRILL`, `passed_sla: true` |

**Not exercised by the drill:** cancels under a flag; the C7 trip → flag write (unit-tested in `tests/test_w75_4_one_kill_switch.py`, 14 tests). Re-run the drill after any change to `kill_switch_state.py`, `kalshi_client.py`, or the loop in `run_t4_mlb_live.py`.

## Related
`RUNBOOK_model-drift.md`, `RUNBOOK_order-duplication.md`, `RUNBOOK_audit-log.md`, `04_EXECUTION/RID_LOG.md`, `02_ARCHITECTURE_DESIGN/RUNTIME_MAP.md`.
