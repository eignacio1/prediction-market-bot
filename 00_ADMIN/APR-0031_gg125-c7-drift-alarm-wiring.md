# APR-0031 — Wire C7 `SystemMonitor`'s Brier/ECE Drift-Alarm Ladder Into a Live Per-Bet-Resolution Call Path (GG-125)

**Status:** DRAFT — not submitted for DS sign-off. This document proposes a monitoring-wiring design and
an explicit warn-only/no-auto-halt posture; it does not itself request implementation authorization. Per
Hard Rule 3, if DS accepts this proposal, a superseding ADR would still be required before any
`run_resolve_mlb.py` / `run_resolve.py` change ships, since this is a monitoring-threshold/behavior
change, not a pure bugfix.
**Touches (if accepted):** `src/prediction_market_bot/run_resolve_mlb.py::_resolve_pool()` (line ~439-454,
the `trader.settle_position()` call site) and `run_resolve.py`'s equivalent NBA settlement loop;
`src/prediction_market_bot/c7_monitoring/monitor.py` (no interface change proposed — `record_forecast_outcome()`
and `check_and_alert()` already exist and are unmodified by this proposal; only their *callers* are new).
**Drafted:** 2026-07-21, Window B (T-379)
**Prior context:** GG-044/ADR-0046/APR-0026 (MLB-native Brier/ECE baseline derivation, ACCEPTED
2026-07-16) correctly derived and wired a baseline *value* into `SystemMonitor`'s constructor, but GG-125
(discovered same investigation, T-374) found that value is never actually read by any live alarm
computation — `check_and_alert()`/`get_drift_snapshot()` are called from nowhere in production, and
`record_forecast_outcome()` (which feeds the rolling window those methods read) appears only in
`monitor.py`'s own usage docstring (lines 238-256), never in a real call site. This document is the
follow-on GG-125 itself named as required before implementation ("This is materially larger and
higher-risk than a baseline-value fix and deserves its own APR before implementation").

---

## Why This Proposal Exists

`check_portfolio_pnl()` — a separate PNL-threshold check, unrelated to calibration drift — is the only
`SystemMonitor` method actually invoked from any of the four production entry points
(`run_mlb_paper_trade.py`, `run_resolve_mlb.py`, `run_paper_trade.py`, `run_resolve.py`), confirmed by
direct grep this session:

```
$ grep -rn "record_forecast_outcome(" src/ scripts/ --include="*.py" | grep -v "def record_forecast_outcome"
src/prediction_market_bot/c7_monitoring/monitor.py:243:        monitor.record_forecast_outcome(
# ^ this is the class docstring's own Usage:: example block (lines 238-256), not a real call site
```

The consequence GG-044's resolution did not surface at the time: a correctly-derived, correctly-wired
MLB-native baseline produces zero observable alarm behavior, for either sport, because nothing feeds the
rolling window it is compared against. Anyone reasoning about C7 drift-alarm coverage from ADR-0046 alone
would incorrectly conclude the alarm ladder is live. It is not.

---

## The Mechanism, In the Actual Code

**Where the data already exists.** `PaperTrader.settle_position()`
(`c5_execution/paper_trader.py:841-901`) returns `closed_pos`, a dict built as `{**pos, stat_label:
actual_stat, "outcome": outcome, "pnl": pnl, ...}` — i.e. it inherits every field set at entry time by
`open_position()` (`c5_execution/paper_trader.py:380-515`), including `model_p` (line 509, the T1/T4
calibrated pregame or live probability at entry) and `mid_price_at_entry` (line 494, the market mid price
— the market-implied-probability input `record_forecast_outcome()` expects). `_resolve_pool()`
(`run_resolve_mlb.py:391-454`) already captures `closed_pos` in its `resolved: list[dict]` accumulator per
iteration of the settlement loop (line 454) but currently only reads `pnl` and `outcome` from it for print
statements — `model_p` and `mid_price_at_entry` are sitting unused in the same dict, once per resolved
bet, right where `record_forecast_outcome()` would need them.

**The type mismatch to resolve.** `settle_position()` stores `outcome` as the string `"WIN"`/`"LOSS"`
(line 891); `record_forecast_outcome(p_estimate: float, outcome: int, market_implied_prob: float)` expects
`outcome` as `int` (0/1). A trivial per-call mapping (`1 if closed_pos["outcome"] == "WIN" else 0`) at the
call site closes this — no `monitor.py` change needed.

**The architectural gap this proposal must not paper over: the window does not persist across process
invocations.** `SystemMonitor.__init__` (`monitor.py:259-294`) builds `self._window` as a bare in-memory
`deque(maxlen=DRIFT_WINDOW_SIZE)` (`DRIFT_WINDOW_SIZE=30`, line 81) — no serialization, no disk backing,
nothing. Both `run_resolve_mlb.py` (line 578) and `run_resolve.py` (line 106) already instantiate a fresh
`SystemMonitor(...)` on every call, and `_resolve_pool()`'s own docstring states its scope precisely: one
cron invocation, `pending = [p for p in open_positions if p.get("game_date", today) < today]` — i.e. only
positions from *prior* game days, resolved once each. A naive wiring (call `record_forecast_outcome()`
inside the loop, then `check_and_alert()` once at the end alongside the existing `check_portfolio_pnl()`
call) would build a rolling window that resets to empty at the start of every single resolve run and
almost never approaches `DRIFT_WINDOW_SIZE=30` within one run — `_resolve_pool()`'s own GG-084/T-239
addendum records real resolved-counts per run in the range of single digits to low tens (the cited example
is 15/83 resolved as a *degraded* outlier, not typical volume). `get_drift_snapshot()` does not enforce
any minimum window size beyond `n==0 → ALERT_OK` (`monitor.py:366-381`), so `check_and_alert()` would
execute and could technically fire an alert level off of n as low as 1-2 resolved bets per run — a
statistically meaningless sample for a Brier/ECE comparison against a baseline computed from a much larger
reference set. **This proposal explicitly does not resolve this gap by choosing an answer** — see Open
Questions below — because a design decision this consequential (silently-underpowered alerts vs.
under-building persistence) is exactly the kind of monitoring-behavior choice Hard Rule 3 reserves for DS,
not something to default into via the simplest possible wiring.

---

## Proposed Design (Not Yet Implemented)

1. **Call `record_forecast_outcome()` once per resolved bet**, inside `_resolve_pool()`'s existing
   settlement loop, immediately after the `if closed_pos:` block (`run_resolve_mlb.py:446-454`) already
   captures `pnl`/`outcome` for the print statement — same data, same iteration, no new fetch. Requires
   `_resolve_pool()` to either receive a `SystemMonitor` instance as a parameter (constructed once in
   `main()`, passed to both pool calls, so both T1/T2 and T4 pools feed the *same* window rather than two
   independent ones) or return the accumulated `closed_pos` records to `main()` for a single post-loop
   feed — the latter is closer to today's structure (`resolved: list[dict]` is already built and returned
   as a count, easily returned as the list itself instead/also) and avoids threading a stateful object
   through a function whose signature is otherwise pool-label/trader/logger/session_id only.
2. **Call `check_and_alert(session_id=SESSION_ID)` once, after all pools have fed the window**, alongside
   the existing `check_portfolio_pnl()` call (`run_resolve_mlb.py:578-585`) — not per-bet, to avoid
   redundant snapshot computation and repeated C6 log emission within a single run.
3. **Persistence — the open design question, not pre-decided here (see Open Questions #1).** Options
   sketched, none selected:
   - **(a) Accept the reset-per-run window as-is.** Simplest; `check_and_alert()` would compute drift over
     whatever n resolved this run (frequently 0 < n < 30), producing a statistically weak but non-zero
     signal — still strictly more coverage than today's zero. Risk: a single bad-luck run of 2-3 losses
     could swing `rolling_brier` sharply on a tiny n and produce a noisy L1/L2 alert with no real
     statistical grounding, unlike the 30-event window the constant `DRIFT_WINDOW_SIZE` implies was
     designed for.
   - **(b) Persist the window to disk** (e.g. append resolved-bet records to a small JSONL sidecar file
     per pool, load the last `DRIFT_WINDOW_SIZE` records into the `deque` at `SystemMonitor.__init__`
     time) so the rolling window survives across cron invocations and actually reaches its designed size.
     More correct, more work, and introduces a new small stateful artifact requiring its own read/write
     path and (per this project's audit-logging convention) probably its own C6 event on load.
   - **(c) Replay from the existing audit log.** `audit_mlb.jsonl` / `audit.jsonl` already record every
     resolved position via `PIPE-05R`/settlement events — a `SystemMonitor` boot-time replay of the last
     `DRIFT_WINDOW_SIZE` resolution events from the audit log could reconstruct the window without a new
     sidecar file, reusing infrastructure that already exists and is already the source of truth. Not
     scoped or estimated here; flagged as the option most consistent with "the audit log is the append-only
     record" but the most implementation work of the three.
4. **Alert action: log-only, no auto-halt, for the initial wiring.** `check_and_alert()`'s L4 branch
   (`monitor.py:521-530`, guarded by `not self.is_kill_switch_active`) does call
   `trigger_kill_switch()` on `ALERT_L4_KILL` today, but the code's own comment (lines 89-96) and GG-125's
   own resolution note both flag that `get_drift_snapshot()` no longer sets `ALERT_L4_KILL` from Brier
   drift alone — that branch is presently dead/unreachable via the drift path specifically (L4 is meant to
   be driven independently by drawdown/daily-loss, i.e. `check_portfolio_pnl()`'s own kill path, per the
   code comment). This proposal does **not** propose changing that — L1/L2/L3 alerts would log to C6 via
   the existing `event_map` (`monitor.py:494-498`) exactly as `check_and_alert()` already does, with no
   new halt behavior introduced. Any future proposal to make a live drift-alarm level trigger an actual
   halt is out of scope here and would need its own APR, per the `report_band_monitor_verdicts()`/GG-098
   precedent of shipping visibility before shipping automated action.

---

## Open Questions This APR Does NOT Pre-Decide

1. **Persistence model (design option 3 above)** — accept the weak per-run window, build a JSONL sidecar,
   or replay from the existing audit log. This is the single highest-leverage decision in this proposal;
   choosing wrong either ships a statistically noisy alarm (option a) or over-builds infrastructure for a
   monitoring signal whose value hasn't yet been demonstrated in production (options b/c).
2. **Shared window across T1/T2 and T4 MLB pools, or separate windows per pool/band?** T1 pregame
   calibration and T4 live-latency edge are explicitly independent theses per CLAUDE.md's alpha taxonomy
   — a shared Brier/ECE window would blend two theses' calibration quality into one number, which may be
   exactly the kind of T1/T4 conflation CLAUDE.md warns against in a different context (see APR-0030's
   analogous open question #2 on T1/T4 coupling). Separate per-pool `SystemMonitor` instances/windows may
   be the more defensible default; not decided here.
3. **Whether NBA's `run_resolve.py` gets the same wiring in the same change, or as a follow-on.** NBA is
   dark/frozen per standing operator directive; wiring dead code's caller in a frozen pool is low-risk but
   also low-value until NBA work resumes. Bundling both in one APR keeps the fix symmetric across sports;
   splitting them avoids touching frozen-pool code unnecessarily. Not decided here.
4. **Whether `check_and_alert()`'s alert thresholds (`BRIER_L1_DELTA`/`L2`/`L3`, `ECE_L2_DELTA`) were ever
   validated against MLB-native cadence/volume**, as opposed to only against the baseline *value* GG-044
   addressed. A threshold tuned assuming a full, dense 30-event window may misbehave against whatever
   window size option 1 above actually produces. Flagged, not resolved.
5. **Whether the existing `check_portfolio_pnl()` C7 kill-switch path and this drift-alarm path should
   share one `SystemMonitor` instance (as sketched in design step 1) or remain deliberately separate
   instances with separate lifecycles** — sharing one instance means a future drift-driven halt (if ever
   authorized) and the PNL-driven halt would share the same `is_kill_switch_active` flag; that coupling
   may be desirable (one kill switch, per Hard Rule 6) or may conflate two independently-reasoned halt
   conditions. Not decided here.

---

## What This Does NOT Claim

- **This does not claim wiring the alarm will find real drift.** No alarm has ever fired in production for
  either sport; this proposal is about making the *mechanism* observable, not a claim about current
  calibration quality (that is GG-004/EXP-017's question, not this one).
- **This does not authorize any code change.** This is a draft proposal document only, per Hard Rule 3 and
  this session's explicit scope ("APR draft," not implementation).
- **This does not change L4's current dead-via-drift-path status.** The kill-switch auto-trigger branch
  remains gated on drawdown/daily-loss via `check_portfolio_pnl()`, unchanged by this proposal.
- **This does not retract or modify ADR-0046/APR-0026's baseline-value work.** This proposal is the wiring
  that makes that already-accepted baseline actually consumed by a live computation, not a replacement for
  it.
- **This does not change GG-125's OPEN status** until DS reviews and, if accepted, a superseding ADR and
  actual implementation land.

---

## Broken-System Test

| Failure mode | How this draft prevents it |
|---|---|
| A future session implements the naive per-run-reset window (design option 3a) without realizing it produces statistically weak alerts on n<30 samples | Named explicitly in the design section and Open Question #1 as an unresolved, consequential choice — not defaulted into silently |
| T1 and T4 MLB calibration quality get blended into one drift number, obscuring which thesis is actually drifting | Flagged as Open Question #2, cross-referenced to CLAUDE.md's explicit T1/T4 independence framing |
| This wiring is implemented and, on first real alert, is assumed to auto-halt trading because "the kill switch is CLAUDE.md Hard Rule 6" | Explicitly scoped log-only/no-auto-halt in design step 4, with the dead-L4-branch code comment cited directly so a future reader doesn't have to rediscover it |
| NBA's `run_resolve.py` silently diverges from MLB's wiring because nobody decided whether to bundle them | Named as Open Question #3, not silently resolved either way |
| A future implementer picks the audit-log-replay persistence option without scoping the read-path cost or C6 event design | Design step 3(c) explicitly flagged as "not scoped or estimated here" |

---

## Review Checklist (for DS, when/if this is submitted)

- [ ] Reviewed GG-125's discovery (`record_forecast_outcome()`/`check_and_alert()` never called in
      production for either sport, despite ADR-0046/APR-0026 correctly wiring the baseline *value* they
      would consume) as the motivating premise
- [ ] Decision: select a persistence model (Open Question #1 — accept weak per-run window / JSONL sidecar
      / audit-log replay) or defer this APR pending further scoping of the audit-log-replay option
- [ ] Decision: shared vs. per-pool/band `SystemMonitor` window (Open Question #2)
- [ ] Decision: bundle NBA `run_resolve.py` wiring in the same change or defer (Open Question #3)
- [ ] Acknowledged: alert behavior is log-only/no-auto-halt in this proposal; any future auto-halt-on-drift
      proposal requires its own separate APR
- [ ] Acknowledged: this draft does not authorize implementation; a superseding ADR remains required per
      Hard Rule 3 before any `run_resolve_mlb.py`/`run_resolve.py` change ships

**Sign-off:** _not yet submitted for DS review_
**Date:** _n/a_
**Role:** _n/a_
