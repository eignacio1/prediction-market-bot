# Runbook: Order Duplication / Double Submission (FM-05, HIGH)

**Purpose:** Detect and remediate duplicate bet/order placement — a ticker fired twice, a position double-resolved, or a Kalshi order submitted more than once for the same intended bet.
**Owner (role):** Architecture Owner (AO)
**Last reviewed:** 2026-07-13
**Next review:** On any change to `PaperTrader.open_position()`/`resolve_position()`, the T1/T2/T4 re-entry dedup guards, or `kalshi_client.submit_order()`
**Staleness triggers:** New band added with its own re-entry logic; Kalshi live-order path activated (post-G6); a real duplicate-order incident with a cause not covered here
**Upstream links:** `RESILIENCE_FAILURE_MODES.md` (FM-05 definition), ADR-0008 (Kalshi order submission)
**Downstream links:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-028/GG-079
**Decision references:** GG-028/T-166 (idempotency guard, run-level game_date scope), GG-079/T-234 (rejected vs open position routing), T-225 (T4 per-ticker re-entry rules), GG-034 (double-resolution guard)
**Confidence:** 8/10 — grounded in real dedup code across all three active bands (T1, T2/T4 pool-shared, T4M-PROJ); important nuance is that dedup strategy differs by band and this runbook makes that explicit rather than assuming one mechanism covers all bands.

---

## Overview

FM-05 (`RESILIENCE_FAILURE_MODES.md`) is order duplication at C5 — a timeout-retry without an idempotency check, or a network partition causing a caller to re-submit the same intended bet. In this system, duplication risk has **two distinct layers** that must not be conflated:

1. **Local position duplication** — the bot opening two local `paper_portfolio` positions for what should be one bet (e.g. two cron runs firing on the same ticker/game).
2. **Venue order duplication** — the bot submitting two real Kalshi orders for one intended local position (relevant only where `PaperTrader` has a signing key per ADR-0008 — i.e. paper trading with live demo-order confirmation, not yet live capital).

**Important nuance the runbook must preserve:** dedup is band-specific, not a single global mechanism:

| Band | Re-entry / dedup mechanism | Source |
|------|----------------------------|--------|
| T1 (NBA + MLB) | Run-level `game_date` guard + open-position ticker check — "GG-028 defense-in-depth" | `run_paper_trade.py:452,532,538`; MLB equivalent `run_mlb_paper_trade.py:875` |
| T2 (MLB same-day) | PaperTrader idempotency guard blocks re-entry on tickers where T1 already has an open position (shared pool) | `run_t2_mlb_sameday.py` |
| T4 (NBA) | **Explicitly no cross-cycle idempotency by design** — `run_t4_live.py:21` states this outright; dedup for NBA T4 works differently (not ticker-level blocking) | `run_t4_live.py` |
| T4M-PROJ (MLB) | Per-ticker re-entry dedup guard, rebuilt from the persisted portfolio at startup; explicitly allows re-entry once the live state feeding `p_t4` (h_so_far, ab_remaining) has moved since the last fire (T-225) — this is intentional re-fire-on-new-information, not a bug | `run_t4_mlb_live.py:675,858,1349` |
| Position resolution (all bands) | File-lock + re-read-then-mutate pattern prevents double-resolution when a concurrent runner (e.g. two overlapping resolve-cron windows) tries to close the same position twice | `paper_trader.py:762-770` (GG-034) |

**Do not assume T1's ticker-blocking guard applies to T4.** T4 (both NBA and MLB) is designed to re-fire on the same ticker across cycles when the underlying game state has genuinely moved — that is the entire T4 thesis (CLAUDE.md's live-market-latency alpha). A T4 "duplicate" is only a real FM-05 incident if it fires twice on **identical** underlying state (same `h_so_far`/`ab_remaining`/cycle), not merely the same ticker.

---

## Trigger Conditions

### Automatic

| Signal | Where | What it means |
|--------|-------|----------------|
| `[IDEMPOTENCY] SKIP <player> — <ticker> already open` | `run_paper_trade.py:538`, `run_mlb_paper_trade.py:875` | T1 guard fired correctly — this is the guard *working*, not a failure. Its **absence** when it should have fired is the actual failure signal. |
| Two `OPEN` positions for the same `kalshi_ticker` + same `game_date` in `paper_portfolio*.json` | Manual/periodic audit | The T1/T2 dedup guard was bypassed — genuine FM-05 incident |
| Two `kalshi_order_id` values recorded for what should be one local `position_id` | Manual audit of `paper_portfolio*.json` | Venue-layer duplication — a retry at the `submit_order()` call site resulted in two accepted Kalshi orders |
| `T4-MLB dedup guard reconstructed: N ticker(s) already fired` at startup shows an unexpectedly high N or mismatches actual open positions | `run_t4_mlb_live.py:1349` log line | The guard's in-memory reconstruction from the persisted portfolio may be out of sync — verify against the portfolio file directly |

### Manual

- Two cron windows for the same band overlap in time (e.g. a slow-running previous invocation still executing when the next cron fires) — check `deploy/cron.conf` for windows close enough to overlap under a slow run.
- The systemd `t4-mlb` service restarts (`Restart=on-failure`, `RestartSec=60`) mid-cycle — verify the singleton lock (`acquire_singleton_lock()` in `run_t4_mlb_live.py`, backed by `ExecStartPre=-/usr/bin/pkill -f run_t4_mlb_live.py` in `deploy/t4-mlb.service`) actually prevented two live processes rather than just cleaning up after the fact.
- A manual re-run of a pipeline script by an operator while a cron-triggered run is still in flight.

---

## Diagnostic Procedure

**Step 1 — Confirm which layer: local position or venue order?** ≤10 minutes.
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python -c \"
import json
d = json.load(open('logs/paper_portfolio_mlb.json'))
from collections import Counter
tickers = [p['kalshi_ticker'] for p in d['open_positions'] if p['status']=='OPEN']
dupes = {t:c for t,c in Counter(tickers).items() if c > 1}
print('duplicate open tickers:', dupes)
\""
```
Adjust the portfolio filename for the band in question (`paper_portfolio_mlb.json` for T1/T2, `paper_portfolio_mlb_t4.json` for T4M-PROJ, `paper_portfolio_t4.json` for NBA T4, `paper_portfolio.json` for NBA T1). Remember: for T4 bands, a repeated ticker is **not automatically a duplicate** — check `h_so_far_at_entry`/`ab_remaining_at_entry` on each position; if they differ, this is the intended re-fire-on-new-state behavior (T-225), not FM-05.

**Step 2 — For a confirmed T1/T2 duplicate, check for a race window.** ≤10 minutes.
```bash
grep -E "cron|pregame_cron|paper_early_cron|paper_mlb_cron" /opt/prediction-market-bot/logs/*.log | grep "$(date -u +%Y-%m-%d)"
```
Look for two invocations of the same script with overlapping timestamps. `deploy/cron.conf`'s two-window design (18:00 UTC / 01:30 UTC for T1; 19:30 UTC for T2) is intentionally spaced, but a hung prior run (e.g. a slow Kalshi API call) could still overlap into the next window.

**Step 3 — For a confirmed venue-order duplicate (two `kalshi_order_id`s for one intended bet).** ≤10 minutes.
Check whether `submit_order()` was called twice with two different `client_order_id` values for what should be one position. Per ADR-0008/`paper_trader.py:497`, `client_order_id` is set to `pos["position_id"]` — a **fresh UUID generated inside `open_position()` on every call**. This means: **`client_order_id` only provides idempotency protection against a retry of the exact same `submit_order()` call (e.g. an HTTP-layer retry inside `kalshi_client.py`)** — it does NOT protect against `open_position()` itself being called twice by an upstream caller, since each call mints a new UUID and therefore a new `client_order_id`. Two calls to `open_position()` for the same intended bet will produce two distinct Kalshi orders even though each individual call is internally idempotent. **This means the real duplicate-prevention boundary is the caller-side ticker-check (Step 1's table), not the Kalshi `client_order_id` mechanism itself** — if a caller-side guard is bypassed, `client_order_id` will not catch it.

**Step 4 — Check the T4 singleton lock if this is a T4 duplication.** ≤5 minutes.
```bash
ssh prediction-market-vps "systemctl status t4-mlb --no-pager | head -20"
ssh prediction-market-vps "ps aux | grep run_t4_mlb_live.py | grep -v grep"
```
Confirm only one `run_t4_mlb_live.py` process is running. If two are running, the `acquire_singleton_lock()` flock either failed to acquire correctly or the `ExecStartPre` `pkill` didn't fully clean up a stray process before systemd started a new one — this is the exact class of incident GG-062/T-209 previously addressed; if it recurs, re-open that gap rather than treating it as new.

**Step 5 — Remediate.**
- **T1/T2 race from overlapping cron windows:** shorten the slow call path, or add an explicit lock file (mirroring T4's `acquire_singleton_lock()` pattern) if the window spacing in `cron.conf` isn't sufficient.
- **Venue-order duplicate from a caller-side double-call:** identify why `open_position()` was invoked twice (retry logic in the calling pipeline script, not in `paper_trader.py` itself) and add a caller-side guard before the second call, following the T1 `[IDEMPOTENCY] SKIP` pattern.
- **T4 dedup guard desync:** restart `t4-mlb` (forces a fresh reconstruction from the persisted portfolio at startup, per `run_t4_mlb_live.py:675`) and confirm the reconstructed count matches actual open positions in the portfolio file.
- **Double-resolution (not double-open):** `paper_trader.py`'s file-lock + re-read pattern (GG-034) already guards this at the code level — if a double-resolution is observed anyway, this is a regression in that specific guard and should be treated as a P1 (it directly corrupts the realized-P&L ledger, which is the G6 evidence base).

**Step 6 — Escalate.**
Register any confirmed FM-05 incident in `03_DECISIONS/GOVERNANCE_GAP_LOG.md` immediately (Hard Rule 7). If the duplicate resulted in two real Kalshi demo orders (capital-adjacent even in demo mode) or corrupted the realized-P&L ledger, treat as P1 and flag affected positions before they're counted toward G6 `clean_n`.

---

## Known Failure Modes

| Failure mode | Cause | Detection signal | Mitigation |
|---|---|---|---|
| T1/T2 ticker double-open | Overlapping cron windows or a hung prior run | Two `OPEN` positions, same ticker+date, in Step 1's audit | `[IDEMPOTENCY]` guard (GG-028/T-166) — verify it fired; if it didn't, this is the incident itself |
| Mistaking T4 re-fire for a duplicate | T4's intentional re-entry-on-new-state design (T-225) misread as FM-05 | Repeated ticker in T4 portfolio | Check `h_so_far_at_entry`/`ab_remaining_at_entry` — differing values = intended behavior, not a bug |
| Venue order duplicate despite `client_order_id` | Caller invokes `open_position()` twice; each call mints a fresh UUID so Kalshi-side idempotency doesn't catch it | Two `kalshi_order_id` values for logically one bet | Real protection is caller-side ticker guard, not `client_order_id` — see Step 3 |
| T4 singleton lock bypass | systemd restart races with `ExecStartPre` pkill cleanup | Two `run_t4_mlb_live.py` processes in `ps aux` | `acquire_singleton_lock()` flock (GG-062/T-209) — verify still functioning after any systemd unit change |
| Double-resolution corrupting P&L | Two overlapping resolve-cron runs both attempt to close the same position | Would show as a position appearing twice in `closed_positions`, or bankroll drift | File-lock + re-read pattern (GG-034, `paper_trader.py:762-770`) |

---

## References

- `RESILIENCE_FAILURE_MODES.md` — FM-05 canonical definition
- `src/prediction_market_bot/c5_execution/paper_trader.py` — `open_position()`, `resolve_position()`, dedup/lock patterns
- `src/prediction_market_bot/c5_execution/kalshi_client.py` — `submit_order()`, `client_order_id`
- `src/prediction_market_bot/run_paper_trade.py`, `run_mlb_paper_trade.py` — T1 `[IDEMPOTENCY]` guard
- `src/prediction_market_bot/run_t2_mlb_sameday.py` — T2 shared-pool idempotency
- `src/prediction_market_bot/run_t4_mlb_live.py` — T4M-PROJ per-ticker re-entry guard, singleton lock
- `deploy/t4-mlb.service` — `ExecStartPre` stray-process cleanup, `Restart=on-failure`
- `03_DECISIONS/ADR-0008_kalshi-demo-order-execution.md` — venue order submission design
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-028, GG-034, GG-062, GG-079, GG-092
