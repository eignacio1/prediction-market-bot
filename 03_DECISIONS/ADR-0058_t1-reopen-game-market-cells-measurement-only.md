# ADR-0058 — Reopen T1 on the Game-Market Axis, Measurement Only (GG-213)

**Status:** PROPOSED. Not signed. This ADR authorizes zero `kelly_fraction` change, zero cell-status
promotion, and zero `src/` edit by itself — it is a decision record only, per the task's explicit scope
fence. `execution_bands.py`, the cell registry, and `ADR-0048` are unmodified by this document.
**Date:** 2026-08-25
**Author:** Session T-493 (`t493-adr0058-t1-reopen` worktree)
**Registers/depends on:** `ADR-0048` (2026-07-29, ACCEPTED — zeroed T1_MULTI_DAY's `kelly_fraction` to 0.0 on
GG-135's ruin-geometry finding; this ADR does not reopen or reverse that zeroing). `ADR-0050` (2026-07-30,
ACCEPTED — the flat measurement-stake mechanism this ADR proposes extending to T1). `ADR-0054` §4/item (b)
(PROPOSED, unsigned — per-cell epoch scoping; this ADR's reopening is load-bearing on it, not independent of
it). `GG-135` (RESOLVED via ADR-0048). `GG-153` (OPEN, MEDIUM, Blocked-On-Operator — T1's frozen `clean_n`;
this ADR proposes closing it CLOSABLE-ON-ADR-0054(b), not closed). `GG-213` (reserved for this session; not
used — no new defect found that isn't already covered by an existing gap or reported below as an unconfirmed
premise).
**Scope:** `03_DECISIONS/` only. Does not touch `src/`, `execution_bands.py`, the cell registry, or any
`kelly_fraction`.

---

## 1. Context — what "T1 reopens" does and does not mean

The operator directive superseding the standing "do not reopen T1" instruction (quoted in the task claim,
2026-08-25) draws a distinction this ADR makes structural: T1_MULTI_DAY was zeroed by `ADR-0048` on ruin
geometry (`GG-135`) computed from the MAIN book's real resolved bet history. That history — confirmed live
this session by importing `market_type_registry.py` and querying every `(MarketType, T1_MULTI_DAY)` cell — is
100% `KXMLBHIT` player-prop trades, because T1's own cells against every non-prop MLB and NFL market type
(`MLB_MONEYLINE`, `MLB_RUN_LINE`, `MLB_GAME_TOTAL`, `MLB_TEAM_TOTAL`, `MLB_PARTIAL_GAME`, `NFL_MONEYLINE`,
`NFL_SPREAD`, `NFL_GAME_TOTAL`, `NFL_TEAM_TOTAL`) are `CellStatus.NOT_IMPLEMENTED` and always have been.
`GG-135`'s title names the MAIN book, not narrowly "prop market" — that is preserved here, not overclaimed —
but the empirical dataset behind its 1.08% per-bet σ figure had no game-market bet to draw on even in
principle.

**Whether that ruin geometry transfers to game markets (materially different per-bet variance, no lineup
risk) is an empirical question. This ADR does not answer it and is written so that it does not need to.**
That question is T-494's, not this session's. Nothing below asserts either answer.

---

## 2. Item 1 — Reopen as cells, not a band-sizing change (CONFIRMED)

Verified live this session via `market_type_registry.get_cell(market_type, ExecutionBand.T1_MULTI_DAY)`: all
nine target `(MarketType, T1_MULTI_DAY)` cells exist today at `CellStatus.NOT_IMPLEMENTED`. Per `ADR-0053`'s
cell-registry design, a `NOT_IMPLEMENTED` cell is not an absence requiring construction — it is a first-class
status already occupying its `(MarketType, ExecutionBand)` key. **Reopening T1 on the game-market axis is
therefore an authorization to promote existing cells, not new construction of the cell axis itself.** No
registry schema change, no new `MarketType`, no new `ExecutionBand` is required by this proposal.

---

## 3. Item 2 — Flat measurement-stake mechanism: generalizes at the core, T4-shaped at the wrapper

Verified this session by reading `ADR-0050` in full and the `evaluate_forecast(fixed_stake_usd=...)` call
site in `risk.py`.

**What generalizes:** the core bypass — `fixed_stake_usd` as an opt-in parameter to `evaluate_forecast` that
routes around the `kelly_size_zero` rejection path — is band-agnostic by construction. It does not reference
T4M-PROJ, MLB, or any band-specific state. Nothing prevents T1 from calling it today at the risk-engine
layer.

**What does not generalize, and must be said plainly rather than assumed:** `ADR-0050`'s safety and hygiene
wrapper — contract cap, price-stratum sampling, wash-trade suppression (its §9 addendum) — exists only in
`run_t4_mlb_live.py`, T4's own live-loop script. That wrapper is T4-shaped: it was built against T4's
45–90-second in-play cadence and its specific staleness/contamination risks. **This ADR does not propose that
T1 reuse `run_t4_mlb_live.py`'s wrapper as-is.** A T1-equivalent wrapper — scoped to T1's own pregame cadence
and risk surface (lineup confirmation timing, rest/scratch state, not live-market staleness) — would need to
be designed before any T1 measurement-stake bet is placed for real. This ADR authorizes the *pattern*
(flat-stake evidence accrual at zero Kelly, per `ADR-0050`'s precedent), not a specific wrapper
implementation. Designing that wrapper is out of scope here.

---

## 4. Item 3 — Dependency on ADR-0054(b); GG-153 proposed CLOSABLE-ON-(b), not closed

Verified this session by reading `ADR-0054` in full: item (b), per-cell `logic_epoch`/`clean_n` scoping, is
unsigned — only item (c) carries an operator signature (2026-08-17). `logic_epoch.py`'s `LogicEpochBoundary`
is band-keyed (`bands_affected: frozenset[str]`, with an `ALL_BANDS = "*"` sentinel), not cell-keyed, today.

This matters directly for T1's reopening: `GG-153` (OPEN, Blocked-On-Operator) documents T1's global `clean_n`
frozen at 0 by the combination of `ADR-0048`'s zeroing and the epoch-10 `ALL_BANDS` reset. Under the current
band-only epoch scoping, any T1 measurement-stake activity — game-market or prop — accrues into the same
frozen global T1 cohort, and `GG-153` stays open regardless of what this ADR proposes. Under `ADR-0054`(b)'s
per-cell scoping, each of the nine newly-authorized cells would carry its own clean floor, independent of the
frozen legacy prop cohort — which is, notably, `GG-153`'s own listed resolution option (b): "extend
`ADR-0050`'s fixed-stake bypass mechanism to T1 as well." This ADR's proposal is that option, made explicit.

**This ADR does not close GG-153.** It proposes GG-153 be re-labeled CLOSABLE-ON-ADR-0054(b) — i.e., its
resolution is now correctly scoped to a named, existing, unsigned dependency rather than an open-ended
operator block — and that the game-market T1 cells authorized here not begin accruing measurement bets until
ADR-0054(b) is signed and implemented, so that their `clean_n` is cell-scoped from the first bet rather than
inheriting the frozen band-global cohort.

---

## 5. Item 4 — What a nonzero T1 Kelly would still require (none of it authorized here)

This ADR authorizes cell promotion to a flat-stake `NOT_IMPLEMENTED → <measurement status>` transition (exact
status name and promotion mechanics are an implementation-session decision, not fixed here) and nothing past
it. A nonzero `kelly_fraction` for any T1 cell — game-market or prop — additionally requires, none of which
this document performs or authorizes:

1. **T-494's variance re-derivation.** GG-135's ruin geometry must be recomputed on the game-market cells'
   own resolved bet history (once one exists) before any claim that the prop-derived 1.08% σ figure does or
   does not apply. This is the empirical question Section 1 defers.
2. **ADR-0048's edge-conditional reactivation lookup table.** ADR-0048 zeroed T1's Kelly pending a table that
   reactivates it conditional on measured edge — that table does not yet exist for any T1 cell and is not
   created by this ADR.
3. **A fresh operator signature.** Per Hard Rule 2/3, no ADR is self-executing into live risk parameters;
   moving any T1 cell off `kelly_fraction=0.0` requires its own signed decision record, separate from this
   one.

---

## 6. Item 5 — Phase 2 sequencing note (T-487 reference could not be confirmed)

The task instructed this ADR to note: "if gate 2.3 passes, the cell it is evidence for is `(mlb_game_total,
T1)` — cross-reference T-487 step 0(e)." Verified this session:

- **`T-487` does not exist anywhere in this repository.** Repo-wide `grep -rln "T-487"` across all `.md`
  files, and targeted greps of `SESSION_CLAIMS.md`, `ACTIVE_QUEUE.md`, `HYPOTHESES.md`,
  `GOVERNANCE_GAP_LOG.md`, `DECISION_LOG.md`, and both 2026-08-17 handoff/digest files, returned zero matches
  for the literal string. This premise could not be confirmed and is not asserted here.
- **Gate 2.3 itself does exist and is corroborated:** `05_RESEARCH_EXPERIMENTS/HYP010_PHASE2_PREREGISTRATION_2026-08-15.md`
  documents gate 2.3 as a Phase 2 power-analysis gate found to be underpowered by roughly an order of
  magnitude (its Finding 3). `04_EXECUTION/ACTIVE_QUEUE.md` (box E, GG-207) confirms Phase 2 box 2.2→2.3
  (EXP-022) is unstarted pending the HYP-010 pre-registration amendments, and that its underlying data —
  `KXMLBTOTAL` outcomes, i.e. game-total markets — plausibly maps to the `mlb_game_total` cell this task
  named. **The mapping to `(mlb_game_total, T1)` specifically, and the "step 0(e)" reference, could not be
  independently verified against any file in this repository** and should be treated as unconfirmed rather
  than restated as fact in downstream sessions.

**Sequencing consequence, stated conditionally rather than asserted:** if gate 2.3 passes and its evidence is
intended to feed a T1 game-market cell, this ADR's Section 2 confirms `(mlb_game_total, T1_MULTI_DAY)` is
already a valid, existing `NOT_IMPLEMENTED` cell key ready to receive that evidence once promoted — but the
specific gate-to-cell mapping asserted in the task claim is not something this session could source.

---

## 7. Item 6 — ADR-0057 / T-485 / T-486 status (flagged, not resolved; landed after this session's initial check)

At the time this session's worktree branched (2026-08-25T04:34:05Z), `03_DECISIONS/ADR-0057*.md` did not
exist, T-485's `SESSION_CLAIMS.md` row carried no CLOSED entry, T-486 did not appear in `SESSION_CLAIMS.md`
at all, and GG-204 did not appear in `GOVERNANCE_GAP_LOG.md` — the task's premise did not match repo state at
that point. **A subsequent re-fetch of `origin/main`, done before this session's close-out per Hard Rule 10,
shows this has since changed:** T-485 closed (05:00:00Z CLOSED row, GG-204 registered HIGH, `ADR-0057`
drafted PROPOSED), and T-486 (claimed 04:34:23Z, "install rebuilt ACTIVE_QUEUE + land T-485's ADR-0057
branch") landed it via PR #113 (merge commit `9f3b78b`) — `03_DECISIONS/ADR-0057_g6-cell-scoped-rescope-decision-request.md`
now exists on `origin/main`, Status PROPOSED, not ACCEPTED, addressing G6's closure condition against T1's
frozen `clean_n=0` (the same GG-153 fact this ADR's §4 builds on, from the complementary G6-rescoping angle
rather than the reopening angle). **This ADR does not edit `ADR-0057`** — it is noted here as now-current,
directly relevant context, not resolved or acted on further.

---

## 8. What this ADR does NOT do

- Does not change any `kelly_fraction` for any band or cell.
- Does not promote any cell above `NOT_IMPLEMENTED`.
- Does not resolve whether GG-135's ruin geometry transfers to game markets (T-494's question).
- Does not design or authorize a T1-equivalent safety wrapper for the flat-stake mechanism.
- Does not sign or implement `ADR-0054`(b).
- Does not close `GG-153`.
- Does not edit `ADR-0057`, `T-485`, or `T-486`'s state.

---

## 9. Sign-off

**Status:** PROPOSED — awaiting operator review. Not signed. No mechanism described above is authorized to
ship until this ADR is ACCEPTED, and even upon acceptance, Section 5's three items remain independently
required before any T1 cell may carry a nonzero `kelly_fraction`.
