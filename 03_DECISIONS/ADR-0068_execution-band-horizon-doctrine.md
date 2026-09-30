# ADR-0068 — Execution Band Horizon Doctrine: Decision-Tree Depth Is Governed by Decision Horizon

**Status:** PROPOSED
**Date:** 2026-09-30
**Decisions logged:** pending
**Author:** Strategic window (Cowork), drafted at operator direction from the operator's own restatement
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED
**Supplements:** ADR-0014 (per-band decision tree mechanics), ADR-0010 (band/Kelly hierarchy), ADR-0004 (model class)
**Related:** T-569 (T4 latency thesis — NOT SUPPORTED, current feature set), T-583 (game-clustered A/B harness), GG-318, GG-319
**Amends:** `CLAUDE.md` § Execution timing · `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` § Design Principle and § Band Assignment Protocol · `02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md` § P2

---

## Context

The T1–T5 band taxonomy was specified at project start on a principle borrowed from systematic trading:
strategies are tiered by time horizon, and how much structure a strategy may condition on is bounded by how
much time it has to decide. The operator stated this repeatedly while the band requirement was being built.

**It was recorded, but incompletely, and in two places that contradict each other.**

1. `EXECUTION_BANDS.md` § Design Principle states it correctly: *"At the lowest latency, execution quality IS
   the edge. Model complexity is inversely proportional to time horizon because computation time eats into the
   edge window."* It then licenses T4/T5 to run with **no model** on the stated ground that *"sub-second
   execution IS the edge."*
2. `CLAUDE.md` § Execution timing stated the **inverse** — that T1 is the simplest band and T4/T5 the most
   complex — and drew an activation-sequencing conclusion from it. This contradicted both the document above
   and the implementation. Corrected 2026-09-30.
3. `ADR-0014` specifies, band by band, *what each tree computes*. It never states *why the trees differ*. The
   words latency, horizon and speed do not appear in it. So the taxonomy's organizing principle was not
   available as a rule that any session could check a cell against.

**The consequence was a misfiled cell that ran for a full MLB season without contradiction.** T4M-PROJ — the
only ACTIVE cell in the 92-cell registry — runs `p_hits_gte_threshold(h_so_far, ab_remaining, ba_l10,
threshold)`: a binomial over three scalars, with no pitcher, park, weather, lineup, score or leverage input.
That stripping was licensed by the sub-second-execution clause. The pipeline is a **~60-second polling cycle**
and has never been sub-second; `BAND_ASSIGNMENT_FRAMEWORK.md` § P3 independently records the T5 kill-switch
SLA as 60s, "12x too slow." T-569 tested the latency premise directly and returned **NOT SUPPORTED (current
feature set)**.

The defect was not that the doctrine was wrong. The defect was that the doctrine licensed shallowness on an
**assumed** speed advantage and never required it to be measured.

---

## Decision

### D1 — The doctrine, stated canonically

**Decision-tree depth is governed by decision horizon.** A short horizon buys less time to compute, so the
tree is stripped and execution quality carries the edge. A long horizon buys time to condition on matchup,
sport, player, team, external and qualitative factors, so the tree is deep and estimation quality carries the
edge. **The longer the horizon, the deeper the tree.**

### D2 — The test that makes it checkable

> **A band's decision-tree depth must be justified by its decision horizon, and a stripped tree must be paid
> for by a measured execution advantage. A cell that is shallow without being fast is misfiled, not
> optimized.**

This is added to the band assignment test as **criterion C5**, alongside C1 (compute fit), C2 (SLA
achievable), C3 (signal exists) and C4 (evidence validated). Assumed speed does not satisfy C5; a measurement
does.

**Corollary.** The remedy for a misfiled cell is not automatically more speed. Where the cadence already
affords time to compute, the remedy is **more structure**. A stripped tree inherited from a band the cell does
not actually occupy is a defect in filing, not a design constraint.

### D3 — Horizon is not throughput

Evaluation rate is how often the system looks. Horizon is how fast the underlying information changes.
**Band membership keys on decision horizon and never on evaluation count.** A cell issuing thousands of
evaluations per game against markets that move on discrete events arriving minutes apart is a long-horizon
cell with a high poll rate, and is entitled to a deep tree.

### D4 — Routing and depth are different questions

`CLAUDE.md` holds that bands are not pre-decided thresholds and that the model computation determines which
decision tree a bet routes to. `EXECUTION_BANDS.md` defines each band by a horizon. Both stand:
**horizon determines how deep a tree may be (structural); routing determines which tree a given bet is
evaluated under (runtime).**

### D5 — Build sequencing: widest horizon first

The matchup/sport/player/team/external/qualitative architecture is built at **pre-game** first, for two
reasons:

- **Feasibility.** Pre-game is where those factors exist, are stable, and have a context window wide enough
  to evaluate against. In-play, they change faster than they can be ingested.
- **Accrual.** Pre-game markets resolve once per game and are roughly independent across games, so evidence
  accrues at a countable rate and n\* is reachable within a season. In-play rows are serially correlated
  within a game and inflate n without inflating information — the reason the T-583 A/B harness clusters by
  game.

Granularity established at the widest horizon is then carried inward toward the shorter bands. **The north
star is unchanged: that level of granularity at every arm.** This is a sequencing decision, not a scope
reduction, and nothing here recommends against any band, sport or market family.

---

## Consequences

**Immediate, on acceptance:**

- Every existing cell becomes re-testable against C5. **T4M-PROJ is the first candidate and the known case:**
  shallow tree, 60s cadence, latency thesis measured NOT SUPPORTED. Its disposition is an operator decision
  and is explicitly **not** made by this ADR.
- New cells must state their decision horizon and justify their tree depth against it at registration.
- Band reassignment remains governed by the existing change-control path (DECISION_LOG entry + DS sign-off,
  ADR if the strategy held live capital).

**What this ADR does NOT do:**

- It does not reband, demote, deactivate or activate any cell.
- It does not touch sizing, stake, or any `kelly_fraction`.
- It does not recommend against T4, against in-play markets, or against any sport.
- It does not relabel T-569's verdict, which stands as **NOT SUPPORTED (current feature set)** — a statement
  about the feature set tested, not a permanent property of the band.

**Risk accepted.** C5 is a judgement criterion with a measurement attached; "measured execution advantage"
must be defined per band or it becomes a rubber stamp. Defining that threshold per band is follow-on work and
is called out as such rather than assumed here.
