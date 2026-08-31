# ADR-0061 — External-Repair-Safety Contract for Service-Owned Files (Decision Request)

**Status:** PROPOSED — drafted 2026-08-29/30 (T-505/session
`20260829T190312Z-t505-queue-install-instruments-adr0061`) under explicit task instruction. Not
yet ACCEPTED. **This document does not implement anything.** It does not change
`run_t4_mlb_live.py`, `paper_trader.py`, or any other service source. It does not restart any
service. It enumerates the affected services from source, presents four remedies with blast
radius and cost for each, and recommends one for operator decision — it does not decide. Hard
Rule 3 (ADRs are immutable once accepted; a superseding ADR is required before any service
change ships) applies in the other direction here too: **no service change may ship citing this
ADR until this ADR itself is ACCEPTED** by the operator.
**Depends on / builds on:** `GG-224` (OPEN, MEDIUM — the finding this ADR responds to, discovered
2026-08-28/T-502 during the ADR-0055 D2 repair). `ADR-0055` (epoch-12 ledger repair
preregistration — the repair whose silent revert produced GG-224's evidence).
**Registers:** none new. GG-224 remains OPEN and is not touched by this draft — Deliverable 3's
explicit constraint is "do NOT close GG-224 — this is a draft, not a fix."
**Author:** Session `t505-queue-install-instruments-adr0061` (T-505)
**Scope:** `03_DECISIONS/ADR-0061*` only (new file). No code change anywhere in `src/`, `scripts/`,
or `deploy/`. No `GOVERNANCE_GAP_LOG.md` edit accompanies this file — GG-224 already states the
factual record this ADR reasons from.

---

## 1. The finding this ADR is deciding what to do about (GG-224, not re-derived here)

`t4-mlb.service` (`src/prediction_market_bot/run_t4_mlb_live.py`) holds its trading portfolio in
memory for its entire (multi-hour, `Restart=on-failure`, effectively 24/7) process lifetime and
periodically persists that in-memory copy to `logs/paper_portfolio_mlb_t4.json`. On 2026-08-28,
T-502 wrote a fully correct external repair (verified backup, optimistic concurrency, atomic
write) directly to that file while the service was running. The repair appeared to succeed —
correct backup, correct write, correct exit code — and was then silently reverted within roughly
one flush interval (observed cadence ~22s/~72s post-restart), because the service's next flush
wrote its own stale in-memory state back over the file. GG-224's own conclusion, verified again
in this session's source read: **"no purely external, read-before-write safeguard can detect or
prevent this class of clobber"** — the danger window is strictly after the external write
completes, not before it, so no repair-side check alone closes the gap. The only workaround
applied so far was a session-scoped, operator-authorized `systemctl restart t4-mlb.service`
immediately after the repair, forcing the service to reload the corrected file from disk on
startup.

---

## 2. Enumeration — every long-running process in this repo that owns a shared,
externally-repairable file (from source, this session)

Method: searched for systemd unit files (`find . -name "*.service"`), for every script
containing a `while True:` loop in `src/` and `scripts/`, cross-referenced each against
`deploy/cron.conf` to distinguish a genuinely long-running process (systemd, or a cron line with
`timeout` measured in hours) from a short-lived cron invocation (fires, runs briefly, exits —
external-repair risk window bounded by that single run's wall-clock time, typically seconds).
Traced the actual persistence path for every candidate (`PaperTrader` in
`src/prediction_market_bot/c5_execution/paper_trader.py` is the single shared class behind every
`paper_portfolio*.json` file in the repo).

| # | Process | Deployment | Owned file(s) | Long-running? | In scope for this ADR |
|---|---|---|---|---|---|
| 1 | `run_t4_mlb_live.py` | `deploy/t4-mlb.service` (systemd, `Restart=on-failure`, effectively 24/7) | `logs/paper_portfolio_mlb_t4.json` | **Yes** — the confirmed GG-224 case | **Yes** |
| 2 | `run_t4_live.py` (NBA T4) | cron, `timeout 21600` (6h single process) | `logs/paper_portfolio_t4.json` | **Yes** — same `PaperTrader`-backed read-modify-write-flush shape as #1, just launched by cron+timeout instead of a persistent systemd unit. NBA is DARK/FROZEN (operator directive) so this is currently dormant, not currently exercised. | **Yes, architecturally** — same class, same fix surface, dormant only because NBA is tabled |
| 3 | `run_mlb_paper_trade.py` (PIPE-05 T1 MLB), `run_paper_trade.py` (NBA T1), `run_resolve*.py`, `run_t2_mlb_sameday.py`, `run_t3*_pretip.py` | cron, no `timeout` — fire once, run to completion (seconds to low minutes), exit | `logs/paper_portfolio_mlb.json`, `logs/paper_portfolio.json` | No — process lifetime is short and bounded; the same `PaperTrader` read-modify-write pattern applies, but the window in which an external repair could land between this process's load and its save is the process's own brief runtime, not an indefinite service lifetime. Non-zero risk, much smaller blast radius. | Out of scope — the residual risk here is real but structurally different (bounded by a single cron invocation, not indefinite); flagged, not solved, by this ADR |
| 4 | `scripts/pmbot-web-dashboard.service` (`web_dashboard.py`) | systemd, persistent | none — `ReadOnlyPaths=/opt/prediction-market-bot/logs/` in the unit file; confirmed by source read this service only reads log files, never writes | **Yes**, but read-only | **No** — cannot revert an external repair if it never writes |
| 5 | `ds02_nba_live.py`, `scripts/run_mlb_dashboard.py`, `scripts/poll_and_resolve_g1.py`, `scripts/cancel_demo_orders.py`, `scripts/live_terminal.py`, `scripts/phase0_refresh_markets.py` | none are systemd units; not present in `deploy/cron.conf` — manual/dev-invocation scripts only, per source read (`live_terminal.py` is an interactive terminal UI, `cancel_demo_orders.py`/`poll_and_resolve_g1.py` are one-off ops utilities) | none write a shared ledger file with a resumable read-modify-write-against-memory shape (checked: no `json.dump`/`write_text` against any `paper_portfolio*` path in any of these six files) | Some hold `while True` polling loops, but none own a shared externally-repairable ledger file | **No** |

**Bottom line: two processes are in scope — `t4-mlb.service` (live, confirmed) and NBA's
`run_t4_live.py` (same class, currently dormant because NBA is tabled).** Both are backed by the
same `PaperTrader` class, so a fix to the class fixes both at once; a fix to only
`run_t4_mlb_live.py`'s deployment does not.

**One relevant piece of existing partial mitigation, found by source read, that changes the
shape of the fix needed:** `PaperTrader`'s five explicit mutation methods
(`open_position`, `exit_position`, `resolve_pending`, `settle_position`, `mark_aged_open`) already
wrap every mutation in `with self._lock, self._file_lock(): self._reload_locked(); ... ;
self._save()` — an exclusive `fcntl` file lock plus a fresh disk re-read immediately before
applying the one change and saving (added per GG-034, for a different problem: cross-process
scalar drift on the bankroll/P&L accumulators). This is already most of Option (a) below, but
**only for these five call paths.** GG-224's repair-then-revert was observed at a flush cadence
(~22s/~72s) consistent with `open_position()` firing on a live evaluation cycle — meaning even
the already-locked, already-reload-before-save path did not preserve the external repair. This
ADR does not re-derive why (that would require instrumenting a live repair-under-load repro,
which is implementation work, out of this draft's scope) — it is stated here because it directly
affects Option (a)'s actual cost: the "reload before flush" mechanism already exists in the
class and still did not prevent the observed clobber, so Option (a) is not a from-scratch build,
but it is also not proven sufficient by its existing partial form — closing GG-224 fully via
Option (a) would require diagnosing why the existing reload-before-save didn't hold, not just
confirming the pattern is present in name.

---

## 3. Option (a) — Re-read from disk immediately before every flush, including any path that
bypasses the existing lock

**Mechanism:** ensure every write to a `paper_portfolio*.json` file — not just the five methods
identified above, but any other path that persists `PaperTrader` state — goes through
`_file_lock()` + `_reload_locked()` immediately before `_save()`, and diagnose why the existing
instance of this pattern did not prevent GG-224's observed revert (see § 2's closing paragraph).

**Blast radius:** Contained to `paper_trader.py` — one class, four consuming services (T1/T2/T3
MLB, T1 NBA, T4 MLB, T4 NBA all route through it). No schema change to the JSON file itself.

**Cost:** Requires first reproducing GG-224's clobber under controlled conditions (write an
external repair while a live `open_position()` cycle is in flight, on a non-production copy of
the file) to find the actual gap in the existing reload-before-save path — without that,
"re-read before flush" risks being re-declared already-done and shipping a fix that doesn't
close the observed failure. This is real diagnostic work, not a one-line change.

**What it does NOT solve:** A genuine simultaneous race — external write and service flush
landing inside the same lock-acquisition window — still resolves to whichever acquires the
`fcntl` lock second winning, which is correct handling of two writers but does not tell either
writer that a conflicting write from a *different actor* (not just a different process of the
same kind) just happened. It also does nothing for the field being repaired: if the service's
own mutation logic re-derives or reconstructs the exact positions the repair touched (e.g.
resolving an already-repaired "stuck open" position again using its own game-state view, rather
than treating the repair's field as authoritative), a correct reload can still be followed by the
service legitimately overwriting the repaired value with its own conflicting judgment — reload
prevents *losing* the repair on disk, it does not prevent the service *disagreeing* with it.

**Retires GG-224:** Partially. Closes the specific "in-memory copy older than disk" mechanism if
the diagnostic work confirms and fixes it. Does not address the disagreement case above, and
does not give an external repairer any way to know, without inspecting the file's own recent
mtime/hash history, whether their write actually survived a race.

---

## 4. Option (b) — An advisory lock or lockfile the repair path must acquire

**Mechanism:** any external repair script must acquire the same `fcntl` lock
`PaperTrader._file_lock()` already takes (the lock file already exists per-portfolio-path, e.g.
`logs/paper_portfolio_mlb_t4.json.lock`) before reading, backing up, or writing the target file.
This is a coordination contract between repair scripts and the owning service, not a new
mechanism — the lock already exists; the gap is that GG-224's repair script did not use it.

**Blast radius:** Every future repair script must be written or reviewed against this contract.
No change to the owning service's code at all (it already takes this lock for its own
mutations). Contained to repair-script authorship discipline plus, optionally, a shared helper
module (`scripts/lib/`) that wraps "acquire lock, read, verify, write, release" so repair authors
don't hand-roll the `fcntl` calls each time.

**Cost:** Low if formalized as a documented contract + a shared helper function. The lock
primitive itself costs nothing new to build.

**What it does NOT solve:** A lock only prevents two *lock-respecting* actors from clobbering
each other. It does nothing if a future repair script (or a person editing the file by hand, or
an unrelated tool) does not know about or does not use the lock — there is no OS-level
enforcement that only lock-holders may write the file, so this is a discipline-and-documentation
fix, not a structural guarantee. It also does not solve the "service disagrees with the repair"
case from Option (a) — even a repair that correctly holds the lock while writing can still be
legitimately overwritten by the service's next lock-holding turn if the service's own mutation
logic reconstructs the same field differently.

**Retires GG-224:** Partially, and only for repair scripts that are written to comply.
Codifying the contract (this ADR, or a follow-on doc) is necessary but not sufficient — it
retires the *specific* T-502 incident's root cause (repair didn't take the lock) but not the
general hazard (nothing stops the next repair script from making the same omission, short of a
review gate).

---

## 5. Option (c) — A documented stop-repair-start operational runbook, no code change

**Mechanism:** formalize what T-502 already did manually as the standing operational procedure
for any external repair to a service-owned ledger file: `systemctl stop <service>` (or halt the
long-running cron process for NBA T4), perform the repair against the now-static file, verify,
then `systemctl start <service>` (or re-launch). No in-memory state exists to clobber the repair
because nothing is running during the repair window.

**Blast radius:** Zero code change. Purely a documentation + operator-discipline artifact — a
runbook file plus a rule that no repair to these two files ships without following it.

**Cost:** Lowest implementation cost of the four options. The ongoing cost is entirely
operational: every repair now requires deliberate service downtime (T4 MLB stops evaluating and
placing bets for the duration of the repair + verification), and requires a human to remember
and follow the runbook every time — there is nothing in the code that enforces the sequence or
prevents someone from repairing a live file directly, as T-502 did.

**Evidence this ADR must weigh, per explicit task instruction, without over-crediting it:** the
operator granted a scoped restart pre-authorization on 2026-08-29 (block 11.1) covering exactly
this stop/repair/restart sequence for `t4-mlb.service`. That authorization demonstrates the
runbook is operationally *executable* — a human can request it and get a same-day yes. **It is
not evidence that the runbook is *sufficient* as a general answer.** A per-incident
pre-authorization is a decision made once, under full context, by the operator personally
reviewing that specific repair. It says nothing about what happens the next time a repair is
attempted by a session that does not think to ask, does not have the operator immediately
available, or is under time pressure and repairs the live file "just this once" rather than
requesting the stop — exactly the failure mode Option (c) as a runbook-only artifact cannot
prevent, because it has no code-level enforcement at all. The authorization is proof the
procedure works when followed, not proof it will be followed.

**Retires GG-224:** Partially, and conditionally. Fully closes the *specific* clobber mechanism
for any repair that follows the runbook (no service is running, so there is no in-memory state
to flush over the repair). Does not retire the *general* hazard — GG-224's own record already
demonstrates the failure mode this option exists to prevent was produced by a repair script that,
however well-designed on the write-safety side, did not coordinate a stop first. A documentation
fix cannot itself guarantee the next repair author reads and follows it.

---

## 6. Option (d) — Service-owned repair endpoints so external writes never happen

**Mechanism:** the owning service exposes its own repair interface (e.g., a Unix socket, a
signal handler, or a file-watched "repair request" queue the service itself drains and applies to
its own in-memory state before its next flush) so external code never writes the ledger file
directly — it asks the service to perform the repair, and the service, already holding the
authoritative in-memory state, applies it exactly once and flushes normally.

**Blast radius:** Largest of the four. Requires new code in the owning service (a listener, a
request schema, an application path, its own error handling and audit logging for
service-applied repairs) — for both `t4-mlb.service` and NBA's `run_t4_live.py` if both are to be
covered, since they do not currently share more than the `PaperTrader` persistence class.

**Cost:** Highest. This is a genuine feature build, not a coordination contract or a doc — new
attack surface (what can request a repair, with what authorization), new failure modes (what
happens if the service is mid-crash-loop when a repair request arrives), and a design question
this ADR does not resolve: whether the request channel itself needs to survive a service restart
(a request filed the moment before a crash must not be silently lost).

**What it does NOT solve:** Nothing architecturally — properly built, this is the only option
that removes the race by construction rather than by discipline or timing. But "properly built"
carries the largest unknown-unknown surface of the four, and until built, it retires nothing.

**Retires GG-224:** Fully, if and when built and verified — this is the only option in the set
that structurally prevents the clobber rather than reducing its likelihood or window. It is also
the only one that costs meaningfully more than the problem has so far demonstrated it's worth:
GG-224 is one incident, MEDIUM severity, with a working (if manual) session-scoped remedy already
applied.

---

## 7. Recommendation

**Recommended: Option (c) now, Option (a)'s diagnostic half as a staffed follow-on, Option (b) as
a cheap complement to whichever of (a)/(c) is adopted. Option (d) not recommended at this time.**

Reasoning: GG-224 is a single MEDIUM-severity incident with a session-scoped workaround already
verified durable. That does not warrant Option (d)'s cost — building a service-owned repair
channel is the correct answer if this class of incident recurs or if repairs to these files
become routine, but building it now would be sizing the fix to a hypothetical repair cadence, not
the one observed. Option (c) is cheap, immediately available, and — per the operator's own
2026-08-29 pre-authorization — already demonstrated to work when followed; formalizing it as a
written runbook costs almost nothing and closes the specific incident class for any repair that
follows it. But per § 5's explicit caution, a runbook alone is not a structural guarantee, so it
should not be treated as fully retiring GG-224 on its own. Option (a)'s diagnostic work (why did
the existing reload-before-save not hold?) is worth doing regardless of which operational option
is adopted, because § 2 found the mechanism GG-224 blamed is not, in fact, entirely absent from
the code — something more specific than "no reload exists" produced the observed revert, and
that specific mechanism should be understood before anyone trusts the existing lock/reload
pattern for anything else it's used for (GG-034's original bankroll-drift problem, for instance).
Option (b) is close to free once (a)'s diagnostic work or (c)'s runbook exists — requiring future
repair scripts to take the existing lock costs nothing to state as a rule and can be checked
mechanically (a lint-style check that any script writing `paper_portfolio*.json` imports and
calls the lock helper) at comparatively low build cost, well short of Option (d)'s full endpoint
build.

This recommendation does not decide anything — it is a recommendation, not an acceptance. Per
Hard Rule 3, no combination of these options may ship as code until a superseding ADR (or this
one, amended to ACCEPTED with the operator's chosen combination) exists.

---

## 8. What none of the four options solve, stated plainly

None of them address *why* a repair was needed in the first place (GG-166/T-429's underlying
ledger-corruption class, or ADR-0055's epoch-12 repair scope) — this ADR is entirely about
making repairs to service-owned files *safe once undertaken*, not about reducing how often they
are needed. None of them give an external repairer a way to verify, purely from the file's own
content, whether their write is currently "live" (service stopped/not about to flush) versus
"about to be silently reverted" — that visibility gap is real under Options (a) and (b) both,
and only Option (c) (nothing running) or Option (d) (service is the sole writer) close it
structurally. And none of them retroactively verify that the 2026-08-28 repair's *other* fields —
beyond the `repair_ref` stamps T-502 specifically re-checked — survived the eventual restart
intact; that verification, if not already done, is a distinct and smaller follow-on this ADR
does not attempt.
