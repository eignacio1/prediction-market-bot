# Band-axis activation — proposed boxes for the expansion plan (GG-172)

**Status:** PROPOSAL. Not accepted. This document adds no boxes to `MARKET_EXPANSION_ACTION_PLAN.md`,
changes no `kelly_fraction`, and touches no `src/`. It is the operator-facing artifact GG-172 asked for:
what the plan is missing on the band dimension, with T1 as the worked (now live, not hypothetical) example.
**Author:** T-491 (`session/20260826T045905Z-t491-gg172-band-axis`)
**Depends on / cross-references:** `COVERAGE_TARGET_MATRIX.md` (the two-axis target this responds to),
`MARKET_EXPANSION_ACTION_PLAN.md` (Phases 1-4, market-type axis only — not edited here),
`ADR-0048` (kelly_fraction=0.0 zeroing, GG-135), `ADR-0050` (T4M-PROJ flat-stake pattern),
`ADR-0058` (PROPOSED — T1 game-market reopening, T-493), `ADR-0054` §4(b) (PROPOSED, unsigned —
per-cell epoch scoping; ADR-0058 is load-bearing on it), `GG-153` (T1 frozen clean_n, proposed
CLOSABLE-ON-ADR-0054(b), not closed), `GG-157`/T-488 (fill-haircut measurement), T-497/GG-218
(in-flight, unclosed as of this writing — building the literal T1-equivalent flat-stake wrapper this
document's Box T1 describes; do not duplicate that work, cross-check against it before either lands).

---

## 1. Why this document exists

GG-172 (OPEN, HIGH): Phases 1-4 of the expansion plan are written entirely in market-type terms.
`COVERAGE_TARGET_MATRIX.md` already names the gap — "the band dimension is currently unowned" — but
naming a gap is not the same as writing the boxes that close it. This was arguably hypothetical when
GG-172 was registered (2026-08-12: T1 zeroed, T2 raw_n=2, T3 raw_n=0, T5 never traded — no band work
was in flight). **It stopped being hypothetical on 2026-08-25**, when the operator directive behind
`ADR-0058`/T-493 reopened T1 on the game-market axis. The plan has no box anywhere for "reopen a band."
This document is that missing box set, plus the two things that make "activate a band" ambiguous enough
that a single box would mislead: the measurement/sizing split, and the band × market-type interaction.

---

## 2. The missing boxes, per band — T1 as the worked example

Format matches the plan's own convention: checkbox, explicit entry criterion, current status. **None of
these are checked here** — this is a proposal for boxes to add, not a claim any are done.

### Box T1 — Reopen T1 on the game-market axis (the live case)

- [ ] **T1.a** ADR-0058 signed (currently PROPOSED, T-493, 2026-08-25) — operator sign-off that T1's nine
  `(MarketType, T1_MULTI_DAY)` game-market cells (`MLB_MONEYLINE`, `MLB_RUN_LINE`, `MLB_GAME_TOTAL`,
  `MLB_TEAM_TOTAL`, `MLB_PARTIAL_GAME`, plus four NFL cells) promote from `NOT_IMPLEMENTED` to some
  active status. **Entry criterion: signature, not construction** — ADR-0058 is explicit that this is a
  cell-status promotion, not new code.
- [ ] **T1.b** ADR-0054 §4(b) signed (currently PROPOSED, unsigned) — per-cell epoch scoping. ADR-0058 is
  load-bearing on this; T1.a cannot close ahead of it. **Entry criterion: signature.**
- [ ] **T1.c** T1-equivalent flat-stake safety wrapper built — ADR-0050's wrapper is written for T4M-PROJ's
  shape (per-cycle, 45s loop) and does not generalize as-is to T1's shape (per-slate, ~once/day). **This is
  in-flight now as T-497/GG-218 — do not re-scope here, only note it as the literal content of this box.**
  Entry criterion: wrapper exists, unit-tested, enforces `size_usd == $1.00` regardless of `kelly_fraction`
  state.
- [ ] **T1.d** GG-153 closed CLOSABLE-ON-ADR-0054(b) — contingent on T1.b, not independently closable.
- [ ] **T1.e** Fill-haircut netted against T1's game-market EV case before any measurement is read as a
  verdict — `exp_output/T488_GG157_FILL_HAIRCUT/SUMMARY.md` Task 4 (synthetic, no real positions exist
  yet) already shows game-market haircuts running 3-5x props' median and tailing to ~$0.42/contract.
  Entry criterion: any T1 game-market clean_n readout is reported net of a haircut estimate, not raw mid.
- [ ] **T1.f** Own `clean_n` and `n*` per cell (APR-0024), scoped by ADR-0054(b)'s epoch boundary, not
  inherited from T1's frozen prop-market history. **This is the box that makes explicit what §3 below
  argues structurally: T1's old `clean_n=0` is a prop-market number and must not be read as if it says
  anything about the game-market cells this reopens.**

### Box T2 — Same-day overlay (raw_n=2, effectively untraded)

- [ ] **T2.a** Diagnose why `raw_n=2` after this band being nominally cron-active
  (`run_t2_mlb_sameday.py`, per `EXECUTION_BANDS.md` Live Registry) — is this a code path that never
  fires, a gating condition that's never met, or a genuine absence of qualifying signal? **Entry
  criterion: root cause identified and registered (GG or DECISION_LOG), not just re-observed.** This
  plan should not propose sizing or measurement activation for a band whose silence is undiagnosed.
- [ ] **T2.b** (Contingent on T2.a) MEASUREMENT activation on whichever `(MarketType, T2)` cells the
  diagnosis says are reachable — same ADR-0050-pattern flat stake, own wrapper analogous to T1.c.
- [ ] **T2.c** SIZING activation gated on ADR-0048's lookup table (§4 below) plus its own `n* ` — not
  before.

### Box T3 — Pre-first-pitch scan (raw_n=0, never traded)

- [ ] **T3.a** Same diagnostic requirement as T2.a, but starker: `raw_n=0` means the band has never
  produced a single evaluation that reached a bet, not merely an underpowered sample. **Entry criterion:
  a decision-tree trace confirming whether T3 code runs at all in production, and if so, why it has never
  fired.** This is a precondition the plan cannot skip past by assuming T3 "just needs more days."
- [ ] **T3.b** / **T3.c** — same MEASUREMENT-then-SIZING sequence as T2.b/T2.c, contingent on T3.a.

### Box T4 (non-PROJ sub-bands) — T4M-ARITH / T4M-FLOW

- [ ] **T4.a** These already have an entry criterion the plan should inherit verbatim rather than
  reinvent: EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01 (per `EXECUTION_BANDS.md`) must confirm edge before
  activation, and T4M-FLOW additionally needs its `score_diff` live-wiring gap closed. **This box is
  narrower than it looks — it is "run the two experiments already named," not new scoping.**
- [ ] **T4.b** Tier B roster (`T4M-BOUNDARY`/`EVENT`/`LINEUP`/`PITCHER`/`STAGED`/`CORR`/`EXIT`) is
  explicitly scoping-only, no DS sign-off — **this plan should state that box does not exist yet and
  should not be implied by "all five bands."** Do not build without a fresh, band-specific DS sign-off.

### Box T5 — Late-game certainty (never built, either sport)

- [ ] **T5.a** No code exists. Entry criterion for even opening this box: a decision on whether MLB T5
  is architecturally distinct from NBA's dark T5 (per `EXECUTION_BANDS.md`, NBA's is
  `phase_active="Phase 8"`, `kelly_fraction=0.25`, EXP-018 unrun) or whether one design serves both sports
  once NBA reactivates. **This is a scoping question, not a build task — the plan should say so rather
  than implying T5 is a smaller lift than T2/T3.**

---

## 3. MEASUREMENT activation vs. SIZING activation — two gates the plan conflates

Every live band today is `kelly_fraction=0.0` (ADR-0048, GG-135 ruin geometry). "Activate a band" cannot
mean what it meant before ADR-0048 — there is no such thing as flipping a band from off to on with a
nonzero Kelly fraction as the first move anymore. There are two distinct gates, and the plan's Phase 4
boxes (`4.1` shadow, `4.2` flat-stake, `4.3` clean_n≥n*) already encode this sequence *for market types*
without naming it as two different kinds of gate:

**MEASUREMENT activation** (what T1.c / T-497 / ADR-0050 are):
- Flat stake (e.g. $1.00), `kelly_fraction` irrelevant — the wrapper enforces the flat size regardless of
  what the band-config field says.
- Zero ruin exposure by construction — this is the entire point of ADR-0050's pattern, and why ADR-0058
  can propose reopening T1 without touching ADR-0048's zeroing.
- Produces `clean_n` for that cell — data, not capital risk.
- Gate to open this: a signed ADR authorizing the cell-status promotion (ADR-0058-shaped) plus the
  cell's own flat-stake wrapper (T1.c-shaped).

**SIZING activation** (nonzero Kelly, not proposed for anything in this document):
- Requires ADR-0048's "edge-conditional reactivation" lookup table to exist and be populated for that
  cell — **this table does not yet exist for any cell**, per ADR-0048's own text ("pending edge-conditional
  reactivation via an ADR-0048 lookup table").
- Requires T-494's variance re-derivation — **referenced in this task's brief as the SIZING gate's
  precondition; a search of this repo (DECISION_LOG.md, SESSION_CLAIMS.md, 05_RESEARCH_EXPERIMENTS/) did
  not turn up a T-494 claim or artifact as of this session. Flagging as unconfirmed rather than citing it
  as verified — the same discipline the task brief itself models (T-493 similarly flagged an unconfirmable
  "T-487" reference rather than asserting it).**
- Gate to open this: both of the above, plus the cell's own `clean_n ≥ n*` under APR-0024, computed on
  MEASUREMENT-activation data (a `size_usd=$1.00` cohort), not backfilled from pre-ADR-0048 sized bets.

**Why the plan conflating these matters concretely:** a box that reads "T2 activation" without specifying
which gate is being asked for could be read as inviting a nonzero Kelly fraction on a band whose entry
diagnosis (T2.a above) hasn't even run. Every box in §2 above is written as MEASUREMENT-only; none of them
propose or imply SIZING. That is deliberate, not an oversight — SIZING requires an artifact (the lookup
table) that does not exist yet for any band, T1 included.

---

## 4. The band × market-type interaction — the actual finding, not a formality

`COVERAGE_TARGET_MATRIX.md` and the plan both already treat cells as `(MarketType, ExecutionBand)` pairs
(ADR-0053). What neither document states plainly is *why* that pairing is load-bearing rather than
bookkeeping, and T1's own history is the proof:

**T1 was measured only on player props, and killed on prop variance.** ADR-0058 confirms this directly —
GG-135's ruin-geometry finding (the 1.08%/bet σ that drove `kelly_fraction` to 0.0) was computed
exclusively from T1's `KXMLBHIT` bet history, because every other `(MarketType, T1_MULTI_DAY)` cell was
`NOT_IMPLEMENTED` and had no data to contribute. **GG-135's title names the MAIN book, not narrowly "prop
market" — this document does not overclaim that distinction — but the empirical variance behind the
number had no game-market bet to draw on even in principle.** Whether that variance transfers to a
moneyline or run-line bet on the same band is exactly the open empirical question ADR-0058 declines to
answer and defers to T-494. A plan that reads "T1: ✅ ACTIVE" without qualifying *on which market type* is
already the failure mode this section is warning about.

**The inverse case is T4M-PROJ.** It is the one band-market pair actually live today, and it is live
specifically *because* it is in-play: 45-second polling loop, live batter/game state, no pregame
distribution to fit. It **cannot** consume the kind of model T1 or a hypothetical Phase 2 team-total fit
would produce — there is no "T4M-PROJ pregame calibration," because T4's entire model class is live
arithmetic/Bayesian update on in-game state, not a distribution fit scored once before the game starts
(see `EXECUTION_BANDS.md` § Design Principle: "T4/T5: no model — pure game-state arithmetic or Bayesian
update"). A market-type-only phase plan (Phase 2's team-total NB/Poisson fit, e.g.) has no way to express
which bands its output is even structurally compatible with — it produces a pregame probability, which is
T1/T2/T3-shaped by construction, and the plan as written has no box that says so.

**This is the concrete meaning of "a cell is a (market_type, band) pair for a reason":** a model belongs
to a band, not just a market type answers to a band. Phase 1's market-type registry (`MarketTypeCell`)
already has the right shape to hold this (RULED_OUT requires a reason + measured_date, per band). What the
plan is missing is the box that forces Phase 2's team-total work, when it lands, to declare which bands
its output is model-compatible with *before* scoring it against any band's depth gate — otherwise a
correctly-built model can be scored against the wrong band and both the model and the band absorb blame
that belongs to the pairing.

---

## 5. Surfaced, not resolved — the efficiency-gradient tension (operator decision, not softened)

`COVERAGE_TARGET_MATRIX.md` § "The strategic tension nobody has adjudicated" already states this; this
document adds the concrete measurements that sharpen it and restates explicitly that **this is an OPEN
OPERATOR DECISION** — not something this proposal resolves, defaults on, or converts into a monitoring
note.

- **Fill cost, measured (T-488/GG-157, 2026-08-26):** game markets cost 3-5x props' median per-contract
  haircut and tail to ~$0.42/contract (vs. props' $0.06 max observed) — `GAME_WINNER` median $0.035 vs.
  props' $0.0100 (3.5x); `RUN_LINE` p90 $0.15 vs. props' p90 $0.02 (7.5x). This is a real, measured cost
  a game-market EV case must net out before any clean_n readout means what it appears to mean.
- **Pregame market reliability on `KXMLBTOTAL`: the task brief cites a figure of 0.0001, framed as
  evidence that no recalibration edge exists on that series pregame.** This session searched
  `DECISION_LOG.md`, `SESSION_CLAIMS.md`, and `05_RESEARCH_EXPERIMENTS/` for the source measurement and
  did not find it under that name or a nearby phrasing. It may be from concurrent, unmerged in-flight
  work (T-487's EXP-022, Phase 2 boxes 2.2/2.3, is topically adjacent — team run-total model + gate against
  `KXMLBTOTAL`). **This document cites the figure as given, flagged as unverified against current
  `origin/main` at time of writing** — consistent with the instruction to surface, not resolve, this
  tension; independently re-deriving it is out of this proposal's scope.
- **The decision itself, restated plainly:** the coverage target expands toward moneyline/run-line/totals
  — the most-attended, most-efficiently-priced markets on the board — which is the opposite end of the
  efficiency gradient CLAUDE.md's core thesis targets. Two measured facts now bear directly on how costly
  that bet is: game-market fills cost more (§ above), and at least one game-market series may carry near-
  zero pregame recalibration edge by the cited figure. Whether the operator proceeds expecting thinner
  edge as an accepted cost of generality, or holds expansion to markets that fit the efficiency gradient,
  **remains undecided by this document.** Nothing in §2-4 above requires that decision to be made first —
  the MEASUREMENT-activation boxes produce data regardless of which way it resolves — but no SIZING
  activation on a game-market cell should be read as implicitly answering it.

---

## 6. What this document deliberately leaves undecided

- Whether GG-172 itself should be closed by this document, by the operator accepting some subset of §2's
  boxes into the plan, or left open until the boxes are actually written into
  `MARKET_EXPANSION_ACTION_PLAN.md`. **Not this session's call — GG-172 stays OPEN.**
- The §5 efficiency-gradient decision (generality-at-a-cost vs. hold-to-the-gradient).
- Whether ADR-0058 and ADR-0054(b) should be signed — this document assumes neither signature and builds
  every T1 box contingent on both.
- The T-494 variance re-derivation's actual content and status — flagged unconfirmed, not assumed.
- Any box numbering or placement inside `MARKET_EXPANSION_ACTION_PLAN.md` itself — this document is
  deliberately standalone (not an edit to that file) both per the task's scope fence and because two
  other sessions (T-490/GG-210 box 3.4, T-487/GG-207 boxes 2.2-2.3) had unclosed claims against that file
  at the time this session started; merging this proposal's boxes into the plan is left for whoever picks
  it up once those land and the operator has ruled on the sections above.
