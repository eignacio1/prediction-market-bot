# Runbook: Order Duplication / Double Submission (FM-05, C5)

**Purpose:** Diagnose and recover from duplicate order placement — the same market bet twice, doubling exposure. Grounded in the real 2026-06-12 incident (GG-028, $402.49 of $1,003.38 deployed on duplicated tickers) and the current, real (not aspirational) idempotency mechanisms.
**Owner (role):** Infrastructure Operator (IO) + Risk Owner
**Last reviewed:** 2026-07-12
**Next review:** After next real duplication incident, or if `client_order_id` becomes venue-verified before retry (would materially change this runbook)
**Staleness triggers:** Kalshi order API version change; execution engine (C5) refactor; new band added without its own dedup guard
**Upstream links:** `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` (FM-05), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-028, GG-092)
**Downstream links:** `10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/`
**Decision references:** T-166 (PIPE-03 idempotency fix), T-209/T-225 (T4-MLB dedup guard evolution)
**Confidence:** 7/10 — mechanisms verified directly against current source; the venue-side idempotency gap below is real and unmitigated

---

## Overview

**There is no single duplication guard in this system — there are at least four separate, band-specific mechanisms, and none of them is a venue-side idempotency check.** `client_order_id` is generated and sent to Kalshi on every order (`c5_execution/kalshi_client.py:582`, `submit_order()`), but the code never queries Kalshi to check whether a `client_order_id` was already accepted before deciding to retry or re-place — real duplicate protection in this system is **entirely local-ledger-based**: "have I already recorded an open position for this ticker in my own portfolio file?" If the local ledger is wrong, stale, or bypassed (e.g., two processes running against the same portfolio file without a lock), duplication can still occur even though `client_order_id` exists.

---

## The Real Historical Incident: GG-028 (2026-06-12)

`run_paper_trade.py` (PIPE-03, NBA) had no check for existing open positions before its bet-placement loop. A second cron execution at 01:00 UTC (same day as a 22:00 UTC run) re-evaluated all markets and placed 12 additional bets — including duplicate Wembanyama NO ≥40/≥35 positions, because the first run's orders showed `kalshi_order_status: failed (transient)` and were therefore excluded from the "already open" check. **The position was already committed locally (bankroll decremented, position recorded) — "failed" only meant a Kalshi-connectivity retry state, not "this position doesn't exist."** Total effect: $1,003.38 deployed from a $1,000 bankroll (100.3%), reserve mandate breached (13% vs. 15% target). Root cause and fix: T-166, SESSION 53 — `_open_tickers` now includes ALL open positions regardless of `kalshi_order_status`. See `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-028 for full detail.

**This is the design lesson this runbook exists to encode: "order failed at the venue" and "position does not exist locally" are not the same fact, and conflating them is exactly how GG-028 happened.**

---

## Current Dedup Mechanisms (per band — do not assume one covers another)

| Band | Mechanism | Code location | Granularity |
|---|---|---|---|
| PIPE-05 (MLB T1, pregame) | `_open_tickers` set built fresh each run from `trader.get_state()["open_positions"]`; skip if ticker already open | `run_mlb_paper_trade.py:870-876` (explicitly commented `# Idempotency guard`) | Per-ticker, per-run — a market that resolves and reopens with a new ticker string is not protected against re-entry |
| PIPE-03 (NBA T1, legacy) | Same pattern, all open positions regardless of `kalshi_order_status` (T-166 fix) | `run_paper_trade.py:525-538` | Per-ticker, per-run |
| T2 MLB (same-day injury overlay) | Same local-ledger pattern | `run_t2_mlb_sameday.py` | Per-ticker, per-run |
| T4-MLB (`run_t4_mlb_live.py`, live 45s loop) | `already_fired_game: dict[ticker → (h_so_far, ab_remaining)]`, reconstructed from the persisted portfolio at process start (survives restarts), **re-keyed to allow re-fire once game state actually changes** (T-225, 2026-07-03 operator design ruling) — NOT a permanent one-shot set | `run_t4_mlb_live.py:1337-1351`, `_reconstruct_fired_ticker_states()` | Per-ticker, state-keyed — this is the most sophisticated of the four; a ticker CAN legitimately re-fire if `(h_so_far, ab_remaining)` has moved since its last entry, by design |
| T4 (NBA, `run_t4_live.py`, dark/frozen) | `fired_tickers: set[str]` — one bet per ticker **per process run**, not persisted across restarts | `run_t4_live.py:473,574,731,770` | Per-ticker, per-cycle-loop-lifetime only — weaker than T4-MLB's; NBA is currently dark so this gap is not live-risk, but do not assume T4-MLB's persistence applies here if NBA work resumes |

**Cross-process concurrency guards** (protect the ledger file itself, not order semantics):
- `paper_trader.py:_file_lock()` (line 251) — `fcntl.flock` exclusive lock around every state read-modify-write (lines 404, 580, 762, 829, 910) — prevents two processes writing the same portfolio file from corrupting/losing each other's writes.
- `run_t4_mlb_live.py` singleton lock (line ~245, `fcntl.flock(..., LOCK_EX | LOCK_NB)`) — prevents two `t4-mlb` processes from running concurrently against the same portfolio at all (non-blocking — a second instance fails to acquire and should exit rather than proceed).
- `c4_risk_engine/staged_order_store.py` — SQLite in WAL mode (`PRAGMA journal_mode=WAL`), single-writer-per-table — a "ghost protection" layer for staged (not-yet-fired) orders (`stage_order`, `mark_fired`, `mark_cancelled`, `expire_stale`). This governs the staging step, not the final `submit_order()` call to Kalshi.

---

## Trigger Conditions

| Symptom | Likely cause |
|---|---|
| Two positions in `paper_portfolio.json` with the same `kalshi_ticker` | Local-ledger dedup guard bypassed or ran against a stale read of `open_positions` — check for a concurrent second process (see GG-028 pattern) |
| Reserve/deployment percentage higher than expected for the day's bet count | Same as above — duplicated positions inflate deployment without a matching increase in unique markets |
| Kalshi account shows two resting orders for the same ticker | The most direct signal — check via `cancel_demo_orders.py`'s underlying API calls or Kalshi dashboard directly |
| T4-MLB fires on the same ticker twice with an unchanged `(h_so_far, ab_remaining)` | This would indicate the state-keyed dedup guard (T-225) itself has a bug — treat as CRITICAL, this is the guard specifically designed to prevent exactly this |

---

## Diagnostics

```bash
# Check for duplicate tickers in the live MLB paper portfolio
ssh prediction-market-vps "python3 -c \"
import json
d = json.load(open('/opt/prediction-market-bot/logs/paper_portfolio_mlb.json'))
tickers = [p['kalshi_ticker'] for p in d.get('open_positions', [])]
from collections import Counter
dupes = {k:v for k,v in Counter(tickers).items() if v > 1}
print('Duplicate tickers:', dupes if dupes else 'NONE')
\""

# Check for concurrent PIPE-05 cron executions in the same window
ssh prediction-market-vps "grep 'paper_run_start' /opt/prediction-market-bot/logs/audit_mlb.jsonl | tail -10"

# Check T4-MLB's dedup-guard reconstruction log on last restart — confirms it loaded prior state correctly
ssh prediction-market-vps "grep 'dedup guard reconstructed' /opt/prediction-market-bot/logs/*.log"

# Confirm the singleton lock is actually held by exactly one t4-mlb process
ssh prediction-market-vps "ps aux | grep run_t4_mlb_live.py | grep -v grep"
```

---

## Mitigations

### Mitigation A: Confirmed duplicate positions exist (paper mode)

1. Identify both duplicated position records (same `kalshi_ticker`) in the portfolio JSON.
2. Determine if both actually resulted in resting/filled Kalshi orders, or if one is a local-ledger artifact with no real venue order (check `kalshi_order_status` on each).
3. If both are real venue orders: cancel one manually.
   ```bash
   ssh prediction-market-vps "cd /opt/prediction-market-bot && BOT_ENV=paper PYTHONPATH=src python3 scripts/cancel_demo_orders.py"
   ```
   Note: `cancel_demo_orders.py` cancels **all** resting demo orders — it is a blunt instrument (there is no per-ticker selective cancel tool as of this writing). Use only when you intend to clear the full resting-order book, or extend the script with a ticker filter first.
4. Correct the local ledger (`paper_portfolio.json`) to reflect the true single position — this is a manual JSON edit; back up the file first (`cp paper_portfolio.json paper_portfolio.json.bak-$(date +%s)`).
5. Log the correction and root cause in `DECISION_LOG.md` immediately (Hard Rule 7).

### Mitigation B: Concurrent process collision suspected (root cause, not just symptom)

```bash
# Confirm no second PIPE-05/T4-MLB process is running
ssh prediction-market-vps "ps aux | grep -E 'run_mlb_paper_trade|run_t4_mlb_live' | grep -v grep"

# Check cron.conf for accidental duplicate schedule entries
grep -n "run_mlb_paper_trade\|run_t4_mlb_live" deploy/cron.conf
```

If a genuine second-process collision is found: this is the GG-028 pattern recurring in a new pipeline. Do not just clean up the symptom — confirm the relevant `_open_tickers`-style guard (or the T4-MLB singleton `flock`) is actually functioning, since GG-028's root cause was a guard that existed but excluded valid positions due to a status-field bug.

### Mitigation C: T4-MLB state-keyed dedup guard fired incorrectly

If T4-MLB re-fires on a ticker whose `(h_so_far, ab_remaining)` genuinely has not changed, this is a bug in `_reconstruct_fired_ticker_states()` or the live-state polling feeding it — treat as CRITICAL (this is the most recently hardened of the four mechanisms, T-225, and a regression here would be a real live-risk finding, not just a paper-trading nuisance). Escalate before attempting a live fix; capture the exact `(h_so_far, ab_remaining)` pair from both firings first.

---

## Rollback

There is no automated rollback — correction is manual (Mitigation A, steps 3-4). **Verification:** re-run the duplicate-ticker diagnostic script above and confirm 0 duplicates; confirm portfolio deployment percentage matches the corrected position count.

---

## Known Failure Modes

| Failure | Likelihood | Response |
|---|---|---|
| `client_order_id` sent but never venue-verified before a caller-level retry | MEDIUM — this is a real, current gap, not yet triggered into an incident as far as known | No current mitigation beyond the local-ledger guards above; a genuine fix would require checking Kalshi's order-status-by-`client_order_id` before any retry. Candidate for a new governance gap if not already tracked. |
| Local-ledger guard excludes positions based on a status field that doesn't mean what it's assumed to mean (GG-028's exact root cause) | MEDIUM — recurs any time a new status value is introduced without auditing every "already open" check that filters on status | Any change to `kalshi_order_status` semantics or values must re-audit every `_open_tickers`-style filter across all bands, not just the one being changed |
| Second process runs against the same portfolio file without acquiring the expected lock | LOW for PIPE-05/PIPE-03 (cron-scheduled, not expected to overlap) / LOW for T4-MLB (singleton `flock` explicitly guards this) | Diagnostics above; `flock` failure should cause the second process to exit, not silently proceed — confirm this behavior if ever in doubt |
| Manual re-run of a paper-trade script without checking for an already-in-progress cron run | MEDIUM — this is an operator-discretion risk, not a code gap | Always check `ps aux` for a running instance before manually re-triggering any of these scripts |

---

## References

- `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` — FM-05
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-028 (historical incident + fix), GG-092 (this runbook)
- `src/prediction_market_bot/c5_execution/kalshi_client.py` — `submit_order()`, lines 553-639
- `src/prediction_market_bot/run_mlb_paper_trade.py` — idempotency guard, lines 869-876
- `src/prediction_market_bot/run_t4_mlb_live.py` — dedup guard reconstruction, lines 1330-1351; singleton lock, ~line 245
- `src/prediction_market_bot/c5_execution/paper_trader.py` — `_file_lock()`, line 251
- `src/prediction_market_bot/c4_risk_engine/staged_order_store.py` — `StagedOrderStore`
- `scripts/cancel_demo_orders.py` — manual all-resting-orders cancellation tool
