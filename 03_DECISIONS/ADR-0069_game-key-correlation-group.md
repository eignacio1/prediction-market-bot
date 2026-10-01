# ADR-0069 — Game-Key Correlation Group: Definition, Membership, Aggregation, and Group-Level Halt/Budget Semantics

**Status:** PROPOSED
**Date:** 2026-10-01
**Decisions logged:** pending
**Author:** Session `multileg-coherence` (EXP-033), drafted from ADR-0053 §2.5, which named this mechanism and expressly left it to its own ADR
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED
**Supplements:** ADR-0010 (band/Kelly hierarchy), ADR-0026 (portfolio free-cash invariant)
**Related:** ADR-0053 §2.5 and §6.3 item 6, GG-149 (identical-ticker guard), EXP-033 (multi-leg coherence)
**Does not touch:** ADR-0016 (fees), ADR-0040/ADR-0048 (per-band `kelly_fraction`), ADR-0014 (per-band tree mechanics), every pool, ledger and model file

This ADR is a draft for the operator's decision. It has no register row, authorises nothing, and is not evidence that any parlay or multi-leg arm should exist.

---

## Context

Several Kalshi tickers can resolve off the same game: on a typical MLB game EXP-033 found moneyline, run line, totals, team totals and the first-3/5/7 families together, and 878 of 1,039 archived game keys carry ten families. They are economically one exposure under many names. GG-149's guard keys on an identical ticker and cannot see this. ADR-0053 §2.5 named a *game-key correlation group* and stated it needs its own ADR because it is a threshold/cap decision. This is that ADR, scoped to the mechanism's definition. It does not choose a cap.

## Decision (proposed)

### 1. What a correlation group is
A **correlation group** is the set of all open or intended positions whose tickers resolve off the same underlying game, identified by one **group key** = `(sport, game_key)`. The group is an *accounting and halting unit*, not a sizing input.

### 2. How membership is determined and stored
- **Source of truth is venue metadata, never a ticker-string pattern.** A ticker joins a group only if its `event_ticker` game-key suffix is used as a *join key* **and** the join passes two checks recorded at build time: the event `sub_title` is identical across all families of that key, and, for team-conditioned legs, the team uuid in `custom_strike` matches a leg of the other family. A ticker failing either check is **ungrouped and counted**, never guessed into a group. (EXP-033 applied exactly these checks: 0 sub_title mismatches over 1,039 game keys; unmatched floors and legs were excluded and counted.)
- **Relation labels on each pair** are one of `complementary` (event `mutually_exclusive`), `nested` (implication: one leg true forces another), or `related` (same game, no arithmetic constraint). A label is stored with its evidence (the metadata fields used), and a `nested`/`complementary` label is withdrawn if a settled instance contradicts it.
- **Storage:** a derived, append-only mapping `ticker → group_key (+ relation evidence)`, rebuilt from venue metadata, owned by the C1/settlement data path that already resolves a ticker to its game. It is read by C4; C4 never writes it.

### 3. How exposure aggregates across a group
- **Default is gross:** group exposure = sum of capital at risk across every leg held in the group, regardless of side or relation. `related` legs never offset.
- **Netting is allowed only for a provably dominating pair** (a `nested` or `complementary` relation with stored evidence) and only to the extent the *worst-case* loss across outcomes is reduced; it is computed from worst-case payoff, not from correlation estimates. No estimated correlation coefficient enters this ADR.
- The group figure is an **additional** check beside GG-149's identical-ticker check, not a replacement.

### 4. Kill-switch and budget semantics at group level
- A **group halt** stops new positions in that group only; it does not close existing positions and does not touch other groups.
- It is a third tier beside the band-level and system-level kill switches and is **independent** of both: it neither triggers nor is triggered by them, and a system halt overrides it.
- A **group budget** is a *ceiling on aggregate group exposure*, checked at position-open time. The **value of that ceiling, and the conditions that trip a group halt, are not decided here** and remain an open operator decision (ADR-0053 §2.5: "a threshold/cap decision"). No number appears in this ADR.

## What this supplements, and what it does not touch
- **Supplements ADR-0010:** adds a group dimension orthogonal to the band/cell hierarchy; per-band `kelly_fraction` values and their hierarchy are read, never changed.
- **Supplements ADR-0026:** the free-cash invariant still governs total deployment; the group check can only *further restrict* what that invariant permits, never loosen it.
- **Does not touch** fee model, sizing, stake, per-band Kelly, kill-switch timing (NFR-03), any pool or model, or ADR-0053's own accepted items 1–5.

## Evidence base (descriptive, from EXP-033)
Complementary sets are exhaustive in the archive window (every settled MLB GAME/F3/F5/F7 set had exactly one YES; NFL GAME treated as non-exhaustive, ties possible). Across 24 pre-registered cells no multi-leg incoherence survived the cost of crossing every leg, the persistence rule and the multiple-testing correction. That is *not* an argument for or against this mechanism: the group is justified by exposure accounting (GG-149's blind spot), independent of whether incoherence is exploitable.

## Consequences
- **This ADR changes no sizing and activates nothing.** No `kelly_fraction`, stake, cap, threshold or limit changes; no code is built or enabled; no position, order or schedule results from its existence.
- Acceptance would authorise only a later implementation task, which must itself state the ceiling value and halt conditions and obtain operator sign-off.
- Risk if never accepted: cross-family same-game exposure stays invisible to C4 (GG-149's known blind spot persists).

## Open questions (for the operator)
1. The group ceiling value and group-halt trigger (deliberately undecided).
2. Whether `related` legs from different sports' same date should ever group (proposed: no).
3. Whether group exposure should be reported in the Operator Console before any enforcement exists.
