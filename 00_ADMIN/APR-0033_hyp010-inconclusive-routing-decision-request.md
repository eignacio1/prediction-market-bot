# APR-0033 — HYP-010 Phase 2 box 2.4: routing when the gate returns INCONCLUSIVE twice (GG-221)

**Status:** DECISION REQUEST — not adjudicated at drafting time; presented options, did not select one. **See Addendum (2026-09-03, T-517): ACCEPTED, Option 3 selected.**
**Touches (if accepted):** `04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md` box 2.4 and the "Note on model
class" that follows it. No file is modified by this document itself beyond this proposal.
**Drafted:** 2026-08-28, T-500/GG-221
**Prior context:** T-487/GG-207 ran box 2.3 (Poisson, `EXP-022`) — verdict INCONCLUSIVE — EXTEND ARCHIVE.
T-500/GG-221 ran the pre-registered NB refit (`EXP-025`, `05_RESEARCH_EXPERIMENTS/EXP025_HYP010_NB_PREREGISTRATION_2026-08-28.md`)
on the identical 214-game archive — verdict INCONCLUSIVE — EXTEND ARCHIVE again. Both are recorded against
HYP-010 in `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md`.

---

## The gap

`MARKET_EXPANSION_ACTION_PLAN.md`'s "Note on model class" defines a reroute for exactly one outcome:

> if 2.3 falsifies NB/Poisson for team totals, that does not kill Phase 2 — moneyline is a binary target
> where LR (the production class, ADR-0004) applies directly and needs no distribution fit at all. A
> falsified 2.3 should reroute to moneyline-first, not terminate the phase.

Neither run falsified. Both landed INCONCLUSIVE — EXTEND ARCHIVE, which the plan's own three-state
definition explicitly distinguishes from FALSIFIED ("`clean_n < n*`, explicitly *not* falsified"). Box 2.4
has been marked N/A twice now, by two different distributional fits, for the same reason: not underpowered
in a way that's about to resolve itself soon, and not disproven either. The plan defines what happens next
for PASS and for FALSIFIED. It does not define what happens next for INCONCLUSIVE reached twice. This
document exists so that gap is decided in writing, not defaulted to "stopped" silently.

---

## What's actually true right now, verified this session

- Both fits used the **same 214-game archive**, the same outcome join, the same `mu_total` (L10
  offense/defense blend), and the same `|model_p − mkt_p| > 0.010` selected-subset rule. Only the
  distribution feeding `model_p` changed (Poisson → NB1, phi=2.33 fixed).
- Both landed on `clean_n=207` games (NB's own subset rule happened to select the same games Poisson did on
  this archive — not forced, an observed outcome).
- The NB `n*` (44,220) is **less than half** the Poisson `n*` (94,260) at the same `clean_n=207`, because
  NB's *effect size* (mean P&L/bet, magnitude) was larger in this run (−0.0048 vs −0.0026) even though its
  variance was also larger (sd 0.3069 vs 0.2425). Neither model produced a positive mean — both point
  estimates are negative.
- Archiving continues regardless (the price-archiver cron feeds T-488/T-494 too; explicitly out of scope to
  touch this session). At ~14 games/day, even NB's smaller `n*` of 44,220 games is not a "wait a few weeks"
  gap — it is roughly 8.7 years of archiving at the observed cadence, before accounting for off-season gaps.
  The Poisson `n*` was ~18.4 years. Both are "extend archive" in name only; neither is practically reachable
  by waiting.

## n\*-vs-effect-size table, re-derived with NB's own sd (sd=0.3069, `clean_n=207`)

| Effect size (P&L/bet) | `n*` | `clean_n` | short by |
|---:|---:|---:|---:|
| +0.005 | 40,779 | 207 | 40,572 |
| +0.010 | 10,195 | 207 | 9,988 |
| +0.015 | 4,531 | 207 | 4,324 |
| +0.020 | 2,549 | 207 | 2,342 |
| +0.025 (top of pre-registered band) | 1,631 | 207 | 1,424 |
| +0.030 (suspect threshold) | 1,133 | 207 | 926 |

Even at the *top* of the pre-registered effect band (+0.025) — well above what either fit actually measured
(both are negative) — 207 games is still short by more than 7×. This table exists to make concrete what
"extend archive" would actually cost even under an optimistic future re-measurement, not to argue for a
specific verdict.

---

## Options (presented, not selected)

**Option 1 — Treat two-for-two INCONCLUSIVE, both negative-point-estimate, as a de facto soft-FALSIFIED and
fire the existing moneyline-first reroute anyway.** T-487's own results file already flagged this
possibility for the Poisson run alone ("closer to a soft-FALSIFIED for planning purposes"); the NB run adds
a second independent confirmation of a negative point estimate under a corrected distribution, which
strengthens rather than weakens that read. Cost: this extends a "not literally FALSIFIED" state into a
decision the plan didn't literally authorize for this state — an explicit operator call, not an automatic
one, per HYP-010's own falsification condition being about `n*`, not about repeated INCONCLUSIVE.

**Option 2 — Hold 2.4 at N/A and keep archiving, accepting the multi-year timeline the table above makes
explicit, on the theory that the archive itself is cheap (already running, feeds other consumers) and stopping
early forecloses a result that might change once real n grows even partially.** Cost: this is not actually
"3–4 weeks" as HYP-010's original pre-registration assumed for the market-noise=0.05 scenario — that
scenario assumed a positive point estimate near the pre-registered band's low end, which is not what either
fit measured. Waiting on the current negative-mean trajectory does not obviously get closer to a PASS with
more data; it mostly makes the FALSIFIED threshold (`clean_n ≥ n*` with `mu ≤ 0`) reachable sooner instead,
which is itself useful information but is a different framing than "still deciding."

**Option 3 — Reroute to moneyline-first now (same infrastructure the FALSIFIED branch would use:
`KXMLBGAME`, 30,302 observations already archived, production LR class per ADR-0004, no distribution fit
required) while formally leaving HYP-010 open at INCONCLUSIVE rather than reclassifying it as FALSIFIED.**
This decouples the *routing* decision (what Phase 2 does next) from the *verdict* label (what HYP-010's
own record says), avoiding Option 1's need to relabel a result that isn't literally falsified while still
moving the phase forward. Cost: two workstreams (totals-archive-extension and moneyline) now run in
parallel rather than the plan's original single-threaded sequencing, which is a scope/resourcing question
the plan doesn't currently answer either.

---

## Not decided here

This document does not choose among the three options above, does not amend `HYPOTHESES.md`'s recorded
verdicts, and does not touch `04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md`'s "Note on model class" text.
Box 2.4 remains marked N/A pending this decision. Per Hard Rule 11, resolving this is out of scope for
T-500/GG-221 — registered and stopped here for the operator.

---

## Addendum (2026-09-03, T-517) — decision recorded

**Operator selected Option 3.** Sign-off given verbally in-session ("Yes - you have my operator sign off.
Proceed.") and formally recorded in `00_ADMIN/APPROVALS_REGISTER.md`'s APR-0033 row (ACCEPTED — Option 3,
2026-09-03) before any downstream work proceeded, consistent with this project's register-is-source-of-truth
convention for the GG-126 desync failure class.

Effective immediately: Phase 2 reroutes to moneyline-first (`KXMLBGAME`, LR per ADR-0004, no distribution
fit) via the same infrastructure the FALSIFIED branch would have used. HYP-010 itself is **not** amended —
both its box 2.3 verdicts (Poisson `T-487/EXP-022`, NB `T-500/EXP-025`) remain recorded as INCONCLUSIVE —
EXTEND ARCHIVE in `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md`, unchanged by this addendum, per Option 3's own
premise of decoupling the routing decision from the verdict label. This addendum does not reopen Options 1
or 2, and does not itself edit `MARKET_EXPANSION_ACTION_PLAN.md` — that re-scope is a separate tracked step
(T-517 Deliverable 1).
