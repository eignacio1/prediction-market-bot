# ADR-0024: Project-Level Stop/Pivot Criterion

**Status:** ACCEPTED  
**Date:** 2026-06-11  
**Author:** Earl Ignacio (DS) + Claude Code (implementation)  
**Supersedes:** Nothing — fills the governance gap identified in GG-021. Companion to APR-0017.  
**Decisions logged:** true

---

## Context

GG-021 (2026-06-10, PDTP blind-spot pass) identified that the governance system is asymmetric: all gates govern advancing, nothing governs stopping. APR-0017 defines what evidence authorizes live capital deployment (G6). No document defines what evidence forces the conclusion that commercial edge does not exist and the project should halt or pivot.

The absence of a pre-committed stop criterion creates a structural failure mode: any negative result can be scoped away as "underpowered, adverse window, adverse opponent" indefinitely. A well-governed project without a falsification standard does not fail — it just never closes.

This ADR must be ratified COLD — before 2026-27 regular-season data exists. The criterion must be set before the data that would trigger it is available. Setting the criterion after seeing the data is motivated reasoning by definition.

### Why the NBA Finals sample does not count

DS ruling (SESSION 51, 2026-06-11): The NBA Finals window (n ≈ 96-100 resolved markets from G2-G5, single series, 2-team matchup, T1-only, ~38 markets/game) is structurally insufficient for commercial conclusions. The reasons are structural, not statistical:

1. **Player pool**: ~20-30 active players across 2 teams vs. 400+ in regular season
2. **Opponent diversity**: 1 series opponent vs. 29 different organizations
3. **Context breadth**: single elimination context, Finals-specific player usage, no home/road balance across league
4. **Market density**: ~38 markets/game vs. 400+ in regular season
5. **T-band completeness**: T1 only; T2/T3 are SKELETON; T4 under paper isolation

EXP-017B results from the NBA Finals period (G2: EV=+$0.1042/bet, n=33; G4: EV=-$0.0361/bet, n=96) are retained as historical data but are NOT the basis for any G6 or stop-criterion decision. They are high-variance point estimates from a structurally limited window.

---

## Definitions

**Structurally adequate sample:** A dataset that satisfies ALL of the following:
- n ≥ 500 unique resolved market evaluations (not game nights, not position counts — unique market × threshold combinations)
- ≥ 15 distinct opponent team matchups (ensures opponent diversity; a 5-game playoff series against one opponent does not qualify)
- OR: ≥ 2 distinct sports (algorithmic independence; NBA + MLB together qualify regardless of per-sport n, provided each sport n ≥ 150)
- ≥ 3 calendar months of data (eliminates single-window variance; 3 consecutive calendar months with active markets)

**CONFIRMED_NEGATIVE:** EXP-017B mean EV/bet < 0 AND statistically distinguishable from 0 at p < 0.05 (two-sided t-test on per-bet EV distribution).

**CONFIRMED_POSITIVE:** EXP-017B mean EV/bet > 0 AND p < 0.05.

**DIRECTIONAL:** Point estimate is positive or negative but p > 0.05 — inconclusive.

---

## Decision

### Tier 1 — Early Warning (n ≥ 150, ≥ 2 calendar months)

**Trigger:** EXP-017B EV/bet < -$0.03 at the Tier 1 sample floor.

This threshold represents economically meaningful persistent loss — not noise. At σ_EV ≈ $0.25/bet and n=150, the standard error is ≈ $0.020, so -$0.03 is ≈ 1.5σ below zero: directional with moderate confidence.

**Action:** Diagnostic sprint within 2 sessions:
1. Run EXP-018 with full breakdown: YES-only vs NO-only, archetype subsets (PRF-1 through PRF-15), injury-filtered vs unfiltered
2. Check model retrain eligibility: has ADR-0009 shadow model flagged calibration drift?
3. Identify which subset, if any, is driving loss
4. DS reviews and decides: continue full scope, initiate scope retreat, or accelerate Tier 2 monitoring

**Not a halt trigger.** Tier 1 is an alarm, not a stop.

---

### Tier 2 — Halt Trigger (structurally adequate sample)

**Trigger:** EXP-017B CONFIRMED_NEGATIVE on a structurally adequate sample.

At n=500, σ_EV ≈ $0.25/bet, CONFIRMED_NEGATIVE at p < 0.05 means the point estimate is approximately < -$0.018/bet. This is the correct floor: any persistent measurable loss against market prices, at adequate power, is evidence that the model does not generate positive expected value.

**Action — mandatory sequence:**
1. **Halt paper trading immediately.** No new PIPE-03 runs until DS explicitly restarts.
2. **Initiate ADR-0004 supersession review.** Current model class (LR + Platt scaling) is the candidate for replacement. The review must ask: is the model class wrong, is the feature set wrong, or is the edge source wrong?
3. **Log halt decision in DECISION_LOG.md and APPROVALS_REGISTER.md.** No live capital under any circumstances without ADR-0004 supersession completed and new evidence baseline established.
4. **Scope Retreat Option (see below).** If a profitable subset exists at Tier 1 power, scope retreat to that subset is an acceptable alternative to full halt — requires separate DS decision and new ADR.

---

### Scope Retreat Option

If Tier 2 is triggered but a specific subset shows CONFIRMED_POSITIVE or strongly DIRECTIONAL_POSITIVE at Tier 1 power:

**Eligible subsets:**
- YES bets only (excludes NO betting entirely)
- Specific PRF archetypes (e.g., PRF-1 Franchise Cornerstone, PRF-4 Elite Scorer)
- High-confidence bets only (model probability > 0.70)
- Specific sport (e.g., MLB shows positive while NBA does not)

**Requirements for scope retreat:**
- Subset must show CONFIRMED_POSITIVE or strongly DIRECTIONAL_POSITIVE (EV/bet > +$0.02) at n ≥ 100 within the subset
- New ADR required: scopes the reduced deployment and resets the evidence baseline for the reduced scope
- Original ADR-0024 Tier 2 still OPEN on full-scope deployment until superseded

---

### Passability Drift Watch (standing, permanent)

GG-021 notes that G6 criteria were already revised once: APR-0016 → APR-0017. The concern is that criteria drift easier-to-pass over time as evidence fails to meet the bar.

**Standing rule:** Every future revision to G6 criteria (APR-0017 or any successor) must include in the DECISION_LOG entry:
- (a) What evidence prompted the revision
- (b) Whether the revision makes G6 harder or easier to pass
- (c) If easier: explicit justification that is NOT "current evidence is negative" — that is the definition of motivated revision
- (d) Confirmation that the revised criteria still answer the original commercial question

The SESSION 51 DS ruling on EXP-017 scope transition IS correctly motivated: the original criteria assumed an NBA Finals sample size that is structurally inadequate for the question being asked. Expanding the evidence window to regular season and multi-sport scale makes the criteria more rigorous, not less. That is the correct direction.

---

## EXP-017 Scope Transition

Per DS ruling (SESSION 51, 2026-06-11): EXP-017 commercial validation transitions from NBA Finals scale to:

1. **MLB 2026 season** (primary, immediate): Active April–October. Provides structural diversity: multiple opponents, large player pool, different sport mechanics. EXP-017 MLB run during dark period (Phase 3 of DARK_PERIOD_PLAN.md).
2. **NBA 26-27 regular season** (secondary, October+): Provides NBA-specific validation at adequate scale after model retrain.
3. **Combined** (definitive): n ≥ 500 across both sports satisfies the structurally adequate sample definition.

**Oversight note:** The original EXP-017 design scoped the NBA Finals as the validation window. That was an oversight in the evidence plan — the Finals window has structural limitations (single-series opponent, small player pool, T1-only, Finals-specific context) that make it inadequate as the commercial validation measure. This ADR formally acknowledges and corrects that oversight.

---

## Consequences

- GG-021 RESOLVED. Stop criterion is now documented, cold-decided, and binding.
- EXP-017 commercial validation window formally transitions to regular season / multi-sport scale.
- NBA Finals EXP-017B results (n=96) are historical data points, not commercial validation evidence.
- First ADR-0024 Tier 1 check: at n=150 in 2026-27 regular season or MLB 2026 (whichever comes first).
- First ADR-0024 Tier 2 check: at n=500 structurally adequate — estimated 2026-27 regular season Week 2-3 under T1 alone.
- Passability drift watch is standing and permanent.
- Live capital (G6) still requires APR-0017 Tier 0-A: EXP-017 CONFIRMED_POSITIVE on an adequate sample. This ADR defines what adequate means.
