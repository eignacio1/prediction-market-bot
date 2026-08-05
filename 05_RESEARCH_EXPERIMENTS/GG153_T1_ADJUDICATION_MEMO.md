# GG-153 — T1 Adjudication Decision Memo

**Date:** 2026-08-05 | **Task:** T-418 | **Author:** session `t1-adjudication-stuck-positions`
**Read time:** <10 min. Decision needed: pick (a), (b), or (c) below, or explicitly defer.

## Live state (do not use the retracted framing)

GG-153 explicitly retracts "T1's clean cadence is frozen at 13 days, n=202" as the operative
description. The verified live state is `clean_n=0`, and — because `T1_MULTI_DAY.kelly_fraction`
has been `0.0` since ADR-0048 (2026-07-29) — **it cannot increase under the current regime.**
Every T1 evaluation that clears CHECK 3/4b is rejected downstream with `kelly_size_zero`. No
new resolved bet, clean or dirty, has been possible since ADR-0048 landed. This memo does not
restate the retracted 13-day/n=202 framing as current — it is dead, superseded state.

---

## Option (a) — Adjudicate against the last clean cohort before the epoch-10 reset

**Is it recoverable? Yes — by computation, not judgment.**

`logic_epoch.py`'s boundary register was walked directly: T1's `clean_epoch_floor` moved
5→9→10, not straight 5→10 (epoch 9/GG-135 already touched T1's write path — it edited
`T1_MULTI_DAY.kelly_fraction` in `execution_bands.py`, which the register correctly treats as
a genuine change). The strict pre-epoch-10 cohort is epochs 5-8 (no T1 bet was ever stamped
epoch 9 — ADR-0048's zeroing landed as part of that boundary and blocked every attempt from
that instant forward, confirmed directly against the live portfolio's `logic_epoch` histogram).

Pulled a direct copy of `paper_portfolio_mlb.json` from the VPS and replicated
`run_exp017b_decomp_mlb.py`'s `load_records()` filtering exactly:

| Cohort | n | win_rate | mean P&L/bet | stdev | cadence span |
|---|---|---|---|---|---|
| T1 epochs 5-8 (strict pre-epoch-9) | 202 | 45.54% | **-$0.6289** | $9.8707 | 2026-07-17 → 2026-07-30 (13d) |
| T1 epochs 5-9 (broad) | 202 | identical — zero bets ever stamped epoch 9 | | | |
| T1 epoch ≥10 (current floor) | 0 | — | — | — | — |

**This is a materially worse finding than "13 days short of mature."** The n=202 cohort is
physically intact and recoverable, but its own mean P&L per bet is **negative**. Per
`run_power_calc.py`'s own logic, a negative mean produces no finite n* — there is no sample
size at which this cohort's effect size would clear APR-0024's confirm bar. Recoverable ≠
favorable. Adjudicating against this cohort would not pass T1 through G6 sample-adequacy in
Earl's favor; if anything it is directionally consistent with GG-037's prior "no demonstrated
T1 alpha" verdict — a second independent read pointing the same direction, not a new one.

**Recommendation if (a) is chosen:** adjudicate honestly — record n=202, -45.5c/bet mean, 45.5%
win rate as T1's last-clean-data verdict, and close the sample-adequacy question as "answered
negative," not "insufficient data." That is a different, more final action than what GG-153's
phrasing ("if recoverable") implies.

---

## Option (b) — Extend ADR-0050's `fixed_stake_usd` bypass to T1

**Stake:** GG-135's empirical-bootstrap frontier (MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md)
found MAIN's real σ (~1.08%/bet) and cadence (~15.8 bets/day) trip the 20% drawdown kill
~100%/yr at **any** edge sign under the pre-zeroing 0.061 Kelly regime; cutting Kelly-equivalent
sizing to ~10% of that level is the frontier point that gets 1yr P(kill) down to 1.2% (cadence
cuts alone are NOT sufficient — 79% at 10% cadence — because Kelly-fraction scaling hits
variance quadratically and cadence only linearly). T1's mean stake under the old regime was
**$9.99/bet** (n=202, computed directly from closed positions). A `fixed_stake_usd` bypass
sized to the frontier's safe point is therefore **≈$1/bet**, not a judgment call — it is GG-135's
own number applied to T1's own historical stake.

This is a MAIN-book-wide cadence figure, not T1-isolated, so treat $1/bet as a conservative
anchor, not an exact T1-specific derivation — but it errs toward the frontier's safe side, which
is the right direction to err given ADR-0048's own rationale.

**Depth:** CLAUDE.md no longer states a fixed depth figure for any family (GG-155,
CLOSED-AS-ARTIFACT) — depth swings 14-67x intraday on direct measurement. A T1 bypass at
$1/bet is trivially below every depth reading taken this project (`$0.90` worst-case median to
`$4,313.72` best-case), so depth is not the binding constraint at this stake size — but the ADR
must still say "verify live at execution time," not cite a number, per CLAUDE.md's standing rule.

**ADR required:** yes — a new ADR (not a CLAUDE.md edit, not a GG-153 resolution note). It must
name: (1) the $1/bet stake and its GG-135 derivation, (2) that it does NOT reverse ADR-0048's
Kelly=0 zeroing (Kelly stays zero; this is a parallel fixed-stake path, same shape as ADR-0050's
T4M-PROJ precedent), (3) a live-depth-check requirement per CLAUDE.md, (4) explicit exit
criteria back to (a)'s honest read if the resumed cohort also comes back negative.

**Calendar cost to reach n\*:** cannot be computed today. n* requires a positive mean P&L/bet;
the only real T1 sample on hand (epochs 5-8) has a negative mean, so no finite n* exists yet —
n* can only be computed retrospectively once the fixed-stake cohort itself produces a positive
mean, which may not happen. At T1's historical resolved-bet cadence (202 bets / 13 days ≈
15.5/day), reaching e.g. n=200 again would take roughly 13 calendar days of resumed accrual —
but that is a cadence estimate, not an n* estimate, and should not be conflated with one.

**Does this reopen the ruin surface ADR-0048 deliberately closed? Honestly: partially, and
that must be said plainly.** ADR-0048 closed GG-135 "by construction (size=0 cannot
self-terminate on variance)." Any nonzero `fixed_stake_usd` reopens a nonzero variance
contribution — it is smaller by ~10x than the frontier's own survivable point, so the reopened
surface should sit near the frontier's 1.2%/yr region, not back at the ~100%/yr region ADR-0048
escaped. But "should sit near" is not "is confirmed to sit near" — ADR-0050's own T4M-PROJ
precedent required a fresh D2 bootstrap re-run before any nonzero deploy (ADR-0048 §2.1), and
that same discipline applies here: **a fresh `mc_empirical_bootstrap.py` run at the proposed
$1/bet stake, before deploy, is not optional.** Do not treat this memo's arithmetic as a
substitute for that re-run.

---

## Option (c) — Document T1 as permanently unmeasurable under the current regime

**What gets written, where:** an update to GG-153 itself (Status → RESOLVED-AS-DOCUMENTED or
similar, not a code change) stating that under ADR-0048's standing Kelly=0 zeroing, T1's
`clean_n` is structurally frozen at 0 and no calendar-time waiting will change that — distinct
from every other GG-153-adjacent entry, which describes bands still accruing. A one-line
pointer belongs in CLAUDE.md's "commercial validation gap" section only if this becomes T1's
durable status (that section explicitly says do not re-embed n-counts there — a pointer only).

**What it forecloses:** nothing structurally — T1 remains reactivatable exactly as ADR-0048
§2.1 already specifies (GG-105 monotonicity PASS + B2 frontier lookup + fresh D2 bootstrap).
It forecloses the *passive* path of "wait and clean_n will eventually clear APR-0024" — that
path was already false before this memo, GG-153 just makes it explicit. It does not foreclose
(a) or (b) being picked later; this option is a documentation state, not a lockout.

**Reversible:** yes, trivially — reopen GG-153 or supersede the status note the moment any
reactivation path is pursued. This is the lowest-cost, lowest-risk option of the three, and the
only one that requires no new stake exposure and no new ADR. Its cost is that it does not move
T1 toward G6 — it formalizes that T1 is stalled, not that T1 is fixed.

---

## Recommendation

(a) and (c) are not mutually exclusive and cost nothing further to do together this session:
adjudicate the recoverable cohort honestly (negative, n=202, no finite n*) **and** document that
the path is now structurally closed pending an ADR. (b) is the only path that could still move
T1 toward G6, but it requires a new ADR, a fresh GG-135-class bootstrap re-run before deploy, and
an honest acknowledgment that it reopens — at ~10x-smaller magnitude — the exact ruin surface
ADR-0048 was written to close. That is Earl's call, not this memo's.
