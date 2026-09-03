# ADR-0060 — NFR-03 Band-Level Kill-Switch Latency Failure: Three Remedies (Decision Request)

**Status:** ACCEPTED — 2026-09-03 (operator, in-session sign-off; T-512, worktree
`session/20260903T002904Z-record-signoffs-20260903`; same pre-granted pattern as ADR-0050 and
ADR-0059). Originally drafted PROPOSED 2026-08-27 (T-498/session
`t498-adr0059-nfr03-latency`). See § 8 for the accepted scope, the trigger condition, and what
this signature does NOT authorize.
**Depends on / builds on:** `GG-038` (T4 kill-switch SLA gap, OPEN, HIGH — carries the full
measured data this ADR reasons from, including the 2026-08-26 T-489 addendum). `GG-209` (OPEN,
MEDIUM — T1 has no force-close/flatten path; a separate, adjacent gap this ADR does not attempt
to close). `ADR-0029` (T4 sub-band architecture, NBA-scoped, where NFR-03's original 60s figure
was first questioned for continuous evaluation). `ADR-0048` (T4M_PROJ `kelly_fraction=0.0`,
currently the reason this gap carries zero live capital exposure).
**Registers:** none. `GG-219` was reserved for this session and is returned unused — GG-038
already contains the complete factual record (T-489's measured latencies, non-coupling proof,
evaluations-in-window analysis) this ADR is reasoning about; opening a duplicate gap would
fragment one finding across two records for no benefit.
**Author:** Session `t498-adr0059-nfr03-latency` (T-498)
**Scope:** `03_DECISIONS/` only. No code change, no `execution_bands.py`/`risk.py`/`kelly_fraction`
edit, no cadence change, no NFR-03 spec-text edit, no `GOVERNANCE_GAP_LOG.md` edit (GG-038/GG-209
already state everything factual this ADR relies on).

---

## 1. The finding this ADR is deciding what to do about (verified by T-489, not re-derived here)

NFR-03 (CLAUDE.md Hard Rule 6): "Kill switch must halt all components within ≤60 seconds." This
is a hard rule, not a target — CLAUDE.md's rules are stated as non-negotiable.

T-489 (2026-08-26, commit `54e1fd0`) measured MLB's two kill-switch tiers against this bar with
real data, not a model of the system:

- **System-level** (`c7_monitoring.monitor.SystemMonitor.trigger_kill_switch()`): 150 real
  in-process trials, p50≈0.027ms, max<1ms. Trivially passes NFR-03 — but **zero MLB pipeline
  reads `is_kill_switch_active`**, so the fast flag-set enforces nothing on either live MLB
  process today (GG-038 TASK 2). This tier is not what this ADR is about; it is fast and inert.
- **Band-level** (T4M-PROJ, `run_t4_mlb_live.py`): a 200-trial *structural* harness (sleep+cycle
  model, no network I/O) reported p50=22.285s/p90=42.720s/max=51.236s — 0% over 60s, a clean
  PASS. But the same-day **real 48-cycle VPS production pull** (`t4_mlb_cycle_log.jsonl`,
  2026-08-26) measured actual cycle-start-to-cycle-start gaps at p50=66.955s/p90=74.670s/
  max=81.187s — **every percentile from the median upward exceeds 60 seconds.** T-489 attributed
  the gap to unmodeled network I/O (ESPN/Kalshi fetch) inside the real loop and explicitly
  discarded its own harness PASS in favor of the measured FAIL. This ADR does not revisit that
  judgment; it is preserved as given.

**Why this is a decision request and not a fix.** Three remedies exist. They are not
interchangeable — each trades against a different constraint this project already has open
(API budget, the spec's own authority, or architectural surface area), and none of the three
fully closes the adjacent gap (GG-209) that this same measurement work also surfaced. Picking one
without naming what it costs and what it leaves unsolved is how a project ends up "fixing" a
measured problem in a way that only moves it.

---

## 2. Option (a) — Shorten the T4 cycle so a halt lands inside 60s

**Mechanism:** reduce `POLL_INTERVAL_S` (currently 45s) and/or the per-cycle work
(`_run_cycle()` duration) enough that cycle-start-to-cycle-start gap's p90/max both land under
60s, closing the gap the same way it was measured — by shrinking the denominator T-489 measured
against.

**Cost:**
- **API budget.** T4's call volume against ESPN/Kalshi is already sized against a 45s cadence
  (ADR-0005's rate-limit headroom, and the `max_api_calls_per_decision` constraint GG-039
  documents for the NBA sub-band architecture). Shortening the cycle directly raises call
  frequency; the current cadence was not chosen carelessly, so this is not free headroom sitting
  unused — it is headroom that has to be re-justified against Kalshi's 60-calls/min ceiling and
  ESPN's own rate limits.
- **Interacts with GG-038's own separate claim.** GG-038's original 2026 finding (independent of
  T-489's later addendum) is that 60s is *itself* 12x too slow for continuous T4 evaluation at
  full throughput — i.e., even a cycle that lands inside 60s does not resolve GG-038's underlying
  concern, only this ADR's narrower NFR-03 compliance question. Shortening the cycle to clear
  NFR-03 does not retire GG-038; it satisfies one reading of the spec while leaving GG-038's
  harder claim (a kill trigger during a live burst can still let many bets through before halt at
  a 60s-class SLA) exactly where it was.
- **Blast radius:** contained to `run_t4_mlb_live.py`'s cadence constant and whatever downstream
  timing assumptions depend on it (staleness windows, `CONTAMINATION_HALT` thresholds). Does not
  touch T1, does not touch the risk engine, does not touch any `kelly_fraction`.

**What it does NOT solve:** GG-209 (T1 has no force-close path at all — a cycle-length change to
T4 has zero effect on T1's separate, already-registered gap). Nor does it resolve GG-038's
"12x too slow" throughput claim above.

---

## 3. Option (b) — Revise NFR-03's 60s bar to a measured, defensible number per band

**Mechanism:** rather than shrink the system to fit the spec, change the spec to state a number
the real, measured system can actually meet — potentially different numbers per band (T1's
batch-bet cadence vs. T4's continuous-evaluation cadence were already effectively different
regimes before this ADR; GG-038 itself calls the original 60s figure a batch-era number applied
unmodified to a continuous-evaluation architecture).

**Cost:**
- **NFR-03 is a hard rule, and a spec change needs its own authority, not a session's
  preference.** CLAUDE.md states hard rules as non-negotiable; this project's own governance
  posture (ADR-0024 stop-pivot-criterion is immutable per Hard Rule 3; ADRs supersede, they do
  not edit) treats a standing rule the same way — a superseding ADR is the correct mechanism,
  but it requires explicit DS/operator sign-off naming the new number as the new bar, not a
  session concluding on its own that the old number no longer fits. This ADR does not attempt
  that sign-off; it only names the option.
- **Risk of goal-post-moving.** A number chosen to match what the system currently does, rather
  than what safety requires, is indistinguishable after the fact from weakening the control to
  make a failing measurement pass. Any accepted revision under this option needs its derivation
  stated in the same terms APR-0024's variance-derived `n*` standard demanded for sample
  adequacy — a number derived from what a kill-trigger event can actually cost at current
  exposure, not from what the current loop happens to measure.
- **Blast radius:** if accepted, touches the spec/NFR-03 text and any place that cites "≤60s" as
  the standard (this ADR, GG-038, CLAUDE.md Hard Rule 6 itself). Zero code change required by
  this option alone — it is a documentation/authority action, not an implementation one.

**What it does NOT solve:** the actual capital-exposure window during a kill trigger is
unchanged by relabeling it compliant. GG-209's force-close gap is untouched. And if the revised
number is band-specific, it does not by itself decouple the mechanisms GG-038 TASK 3 found are
already accidentally non-coupled (system-level switch has no effect on either MLB module) — a
renamed bar does not wire the system-level switch into either pipeline.

---

## 4. Option (c) — Decouple halt from the cycle: an out-of-band kill path

**Mechanism:** instead of checking `kill_switch_armed()` only at top-of-loop and per-game (GG-038
TASK 1's characterization: "never inside `_run_cycle()` and never during the unconditional 45s
post-cycle `time.sleep`"), add a kill-check that can interrupt mid-cycle and mid-sleep — e.g. a
signal handler, a short-interval watcher thread, or restructuring the sleep into short polled
increments that re-check the flag. This is the option that also wires the system-level
`SystemMonitor.trigger_kill_switch()` mechanism into the MLB pipelines that currently do not read
it at all (GG-038 TASK 2/3).

**Cost:**
- **Architecturally cleanest, and the largest change of the three.** It touches the control flow
  of the live loop itself (`run_t4_mlb_live.py`'s cycle/sleep structure), not just a cadence
  constant or a spec number. It is also the only option of the three that can plausibly close
  GG-209 in the same motion — a real out-of-band halt path for T4 is architecturally the same
  primitive T1 is missing (a way to interrupt in-flight/pending work rather than only gate the
  next scheduled entry point), so building it for T4 creates the template T1's force-close gap
  would reuse. That said, GG-209 explicitly registers T1's gap as *forced-close of already-open
  positions*, which is a different operation from *halting further evaluation* — this option
  makes the second easier without automatically building the first; T1 would still need its own
  `exit_position()` call sites wired in (GG-209's own stated remaining work) even after this
  option lands.
- **Testing/verification surface.** A mid-cycle interrupt point is exactly the kind of mechanism
  a structural harness under-measures for the same reason T-489 found the sleep+cycle harness
  under-measured cadence: an interrupt path that is never actually exercised against live network
  I/O timing can look correct in a harness and still miss in production. This option would need
  the same real-VPS-data discipline T-489 applied here, not a synthetic re-test, before it could
  be trusted to close GG-038.
- **Blast radius:** the widest of the three. Any place that currently assumes the loop only
  observes kill-switch state at fixed checkpoints (staleness/`CONTAMINATION_HALT` logic, per-game
  bookkeeping) needs re-auditing against a control flow that can now be interrupted at points it
  previously could not be.

**What it does NOT solve:** it does not by itself change what the state of the system's other
mechanisms is *for* — GG-038 TASK 3's finding that the risk-engine's `KILL_SWITCH` approval
status is currently handled asymmetrically (T1 self-halts on it, T4 treats it identically to an
ordinary `REJECTED`) is a separate defect in a third mechanism (`RiskEngine.evaluate_forecast()`)
that an out-of-band halt path does not touch. All three of T-489's "three real, distinct
mechanisms" (band-level flag, system-level monitor, risk-engine approval-status branching) would
still need to be reconciled under this option, not just the first.

---

## 5. Recommendation

**Recommend (c), decoupled out-of-band halt, as the target architecture — but do not treat it as
the immediate action.** Reasoning:

- (a) buys compliance with the letter of NFR-03 while leaving GG-038's harder claim (60s-class
  SLA is structurally too slow for continuous evaluation) and GG-209 (T1 force-close) exactly
  where they are. It is the cheapest option and the one most likely to look finished without
  being finished.
- (b) is honest about what the system currently does, but changing a hard rule to match current
  behavior — without an independent, capital-exposure-derived justification for the new number —
  risks exactly the failure mode this project's own governance model was built to catch (a
  control weakened to make a red measurement look green). It is not free of merit: if a
  band-specific SLA is the *correct* long-run answer (T1's batch cadence and T4's continuous
  cadence plausibly warrant different bars, per GG-038's own framing), that derivation work is
  real and worth doing — just not as a substitute for measuring cost first.
- (c) is the only option that also creates the architecture GG-209 needs, and the only one that
  addresses the actual mechanism (uninterruptible cycle/sleep) rather than either its symptom
  (measured against a 60s bar) or the bar itself.

**Given current exposure is zero** (T4M_PROJ `kelly_fraction=0.0` under ADR-0048, confirmed live
in `execution_bands.py` this session — every in-window evaluation during the measured latency
gap currently carries no live capital), there is no operational urgency forcing an immediate
build. The recommendation is sequencing, not a mandate to build now: (c) should be the option
scoped and authorized whenever T4M_PROJ's `kelly_fraction` is next considered for
edge-conditional reactivation (ADR-0048's stated reactivation path) — reactivating live sizing on
a band with a known, measured, uninterruptible kill-switch gap is the point at which this stops
being a research-mode finding and becomes a live-capital risk.

**This ADR decides none of the three.** It is a decision request; the choice among (a), (b), (c)
— or a combination, or deferral — is the operator's.

---

## 6. What none of the three options solve, stated plainly

- **GG-209** (T1 has no force-close/flatten path) is closed only partially, and only under
  option (c) as a byproduct, not directly. All three options leave T1's *own* force-close gap as
  a separate piece of work.
- **The risk-engine asymmetry** (T1 branches on `approval_status=="KILL_SWITCH"`; T4 does not,
  per GG-038 TASK 3) is untouched by all three options as stated. Any implementation of (a), (b),
  or (c) would still need to separately fix `run_t4_mlb_live.py`'s handling of a `KILL_SWITCH`
  approval if the goal is a kill switch that actually halts T4 bet submission, not merely a
  faster or differently-labeled detection loop.
- **The system-level monitor's non-wiring** (`is_kill_switch_active` read by zero MLB pipelines)
  is only addressed by (c), and only if (c)'s implementation specifically chooses to route through
  `SystemMonitor` rather than build a second, parallel out-of-band mechanism — that choice is not
  made by this ADR.

---

## 7. A generalizable finding about this project's test posture

**This failure was invisible to every prior check because the only instrument ever pointed at it
was a harness that modeled the system rather than measured it.** GG-038's original 2026 concern
(60s is architecturally too slow for continuous evaluation) was a design-time argument, correctly
reasoned but never checked against a running system. When T-489 finally built an instrument, it
built two: a 200-trial *structural* harness (sleep+cycle model, no network I/O) that reported a
clean PASS, and a same-day pull of *real* production cycle-log data that reported a FAIL from the
median upward. The structural harness was not wrong about what it modeled — it was wrong about
what it claimed to represent. It is a model of the loop's own sleep/compute primitives, not a
measurement of the loop as it actually runs against live ESPN/Kalshi network calls, and the gap
between the two (≈45-52s modeled vs. ≈51-81s measured) is exactly the unmodeled I/O.

This is the same failure shape CLAUDE.md's Q1-Q7 protocol already exists to catch in other forms
— Q7 was added (T-432, GG-166) specifically because a decoupled real data path was the only thing
that caught a corrupted ledger value that every prior in-process check had missed. The lesson
here is the same lesson in a different location: **a synthetic harness that models the system's
own primitives will pass exactly when those primitives behave as modeled, and say nothing about
whether the model itself omits the dominant cost.** For a live-network, real-time system, network
I/O is very often that dominant cost, and a harness built without pulling real production data to
cross-check against will not surface its own blind spot — it has no way to know what it left out.

**The generalizable rule this suggests:** any latency, throughput, or SLA claim about a
live-network component should be treated as unverified until cross-checked against real
production data pulled from the running system, not asserted safe on the strength of a structural
harness alone — even a well-constructed one, and even one with a large trial count (n=200 here).
Trial count does not compensate for measuring the wrong thing. This is not a new process
requirement this ADR is proposing; it is a description of what T-489 already had to do by hand to
find this gap, offered here as a pattern worth repeating deliberately rather than by luck.

---

## 8. Sign-off (2026-09-03, T-512)

**Accepted: option (c), decoupled out-of-band halt, as TARGET ARCHITECTURE. Implementation is
DEFERRED — this signature does not authorize building it now.** This is § 5's own recommendation;
this signature does not read broader than it.

Recorded verbatim in substance: (c) is the chosen target architecture. It is NOT authorized to
build now. **Trigger:** (c) is scoped and authorized when T4M-PROJ's `kelly_fraction` is next
considered for edge-conditional reactivation under ADR-0048. **Rationale:** current exposure is
zero (`kelly_fraction=0.0`, confirmed live in `execution_bands.py`), so there is no operational
urgency; reactivating live sizing on a band with a known, measured, uninterruptible kill-switch
gap is the point at which this stops being a research finding and becomes live-capital risk.

Options (a) and (b) are NOT adopted. ADR-0054 item (d)'s implementation remains blocked until
(c) is built.

**Decision owed, recorded but not solved by this signature:** § 6 names two defects no remedy
option here touches — `run_t4_mlb_live.py` treats a `KILL_SWITCH` approval status identically to
an ordinary `REJECTED` (T1 branches and self-halts on it; T4 does not), and
`is_kill_switch_active` is read by zero MLB pipelines. Both are GG-038 TASK 2/3 and both remain
unstaffed.

GG-209 (T1 force-close/flatten path) is unresolved by this signature — (c), when built, makes it
easier but does not itself build it.
