# ADR-0057 — G6 Closure Condition: Cell-Scoped Re-Expression (Decision Request)

**Status:** PROPOSED — drafted 2026-08-24 (T-485/GG-204) under explicit task instruction. Not yet ACCEPTED. This document does not close G6, does not reactivate T1, does not change any `kelly_fraction`, and does not resolve the operator decision it presents in §4. Awaiting operator/DS sign-off.
**Supersedes (in part):** ADR-0028 (`03_DECISIONS/ADR-0028_segmented-band-promotion-thresholds.md`), § "Updated G6 Closure Condition" only. Per Hard Rule 3 (ADRs are immutable), ADR-0028 is not edited in place — it stands as written, and this document supersedes the one section named above if and only if accepted. All other ADR-0028 content (Modifications 5–9, the T4 Activation Gate structure, GG-022 resolution) is unaffected and remains in force.
**Registers:** GG-204 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`) — this ADR is the decision-request response to that gap.
**Depends on / builds on:** APR-0024 (variance-derived `n*` sample-adequacy standard), ADR-0053 (market-type × band cell model, ACCEPTED as amended), ADR-0048 (T1/T2/T3/T4M-PROJ `kelly_fraction=0.0`), GG-153 (T1 permanently frozen at `clean_n=0`, OPEN, Blocked-On-Operator: YES).
**Author:** Session `session/20260824T233621Z-t485-adr0057-g6-rescope` (T-485)
**Scope:** Decision request only. No code change, no `execution_bands.py`/`risk.py`/`kelly_fraction` edit, no T1 reactivation, no `GOVERNANCE_GAP_LOG.md` edit beyond registering GG-204 itself.

**PREMISE AMENDMENT (2026-08-25, T-486):** this document's finding leans in part on T1 being permanently dead (GG-153: `clean_n=0`, cannot self-heal under the current regime). Operator directive 2026-08-25 reopens T1 on the game-market axis (moneyline/spread/run-line/totals — see T-493/ADR-0058, GG-213): those markets carry materially different variance characteristics than the `KXMLBHIT` player-prop cohort GG-153's ruin geometry was measured on, and re-measurement (T-494) is now in flight rather than assumed closed. **The premise that T1 is permanently dead is therefore no longer true as stated.** The §2 recommendation is unaffected by this amendment — a band-scoped gate still cannot express a 53-cell portfolio regardless of whether T1 specifically revives — but this ADR must not be signed on the "T1 is permanently dead" framing in §1/§4 without reading this note first. Status remains PROPOSED; §4's operator decision is not resolved by this amendment.

---

## 1. Finding (verified this session, not assumed)

**ADR-0028's G6 closure condition cannot close as written, and this is not a slowly-resolving data gap — it is structural.**

ADR-0028 § "Updated G6 Closure Condition" states plainly: **"G6 is a T1 live capital gate."** Of its six numbered conditions:

- **Item 2** — "Statistical floor — T1 ≥66 eligible bets + ≥5 game nights"
- **Item 3** — "Tier 1 — T1-A, T1-B, T1-C, T1-D all pass"
- **Item 4** — "Tier 2 (T1) — T2-A, T2-B (post-haircut...), T2-C, T2-D (post-haircut) all pass; evaluated on YES-direction eligible bets while YES-only gate is active (Mod 9)"

all require new T1 bets to be placed and resolved. T4 is explicitly out of scope for G6 by the same document's Rework Note: *"G6 is a T1 live capital gate... T4 Tier 2 and T-AGG are moved to a separate 'T4 Activation Gate.'"*

T1 cannot place a new bet. Verified two independent ways this session:

1. **Code.** `src/prediction_market_bot/execution_bands.py` line 142: `T1_MULTI_DAY.kelly_fraction=0.0` (ADR-0048, 2026-07-29, DS sign-off recorded). Every T1 evaluation that clears CHECK 3/4b is rejected downstream with `kelly_size_zero` — no new resolved bets can accrue.
2. **Data.** `scripts/run_power_calc.py`, run live against a freshly-pulled VPS portfolio snapshot this session:

   ```
   [T1] clean_n=0 (raw_n=466) — clean_n=0 < 2 — cannot estimate a sample variance.
   [T2] clean_n=0 (raw_n=2)   — clean_n=0 < 2 — cannot estimate a sample variance.
   [T3] clean_n=0 (raw_n=0)   — clean_n=0 < 2 — cannot estimate a sample variance.
   [T4M-PROJ] clean_n=719 (raw_n=2948). TARGET MET vs n*=608. Cadence=359.7/wk.
   ```

GG-153 (OPEN, Blocked-On-Operator: YES) already registers why this is *permanent*, not merely low: ADR-0048 zeroed `kelly_fraction`, and the epoch-10 `ALL_BANDS` reset (confirmed present in `src/prediction_market_bot/logic_epoch.py`, `bands_affected: frozenset[str] = frozenset({ALL_BANDS})`) cleared every band's `clean_epoch_floor`, including T1's. A band that cannot place a bet cannot accrue a clean cohort under any epoch floor, present or future, without an explicit reactivation. There is no passage of time under which G6 items 2–4 self-resolve.

Meanwhile, ADR-0028's own text designates T4 out of scope for G6 — yet T4M-PROJ is the only cell in the entire registry that is both `ACTIVE` and accruing evidence (raw_n=2948, clean_n=719, cadence 359.7 bets/week, vs. T1's static zero). The gate names the dark band as the one that must move, and excludes the only band that is moving.

**Conclusion, confirmed not refuted: G6 as written in ADR-0028 cannot close.** ADR-0028 is ACCEPTED and, per Hard Rule 3, immutable — the fix is a superseding decision, not an edit. That is what this document proposes, subject to operator sign-off, with the one live open question (§4) left explicitly unresolved.

One caveat carried forward honestly: T4M-PROJ's own `n*` reading above is **not itself a clean pass**. The same governance scan that produced the `clean_n=719/n*=608 TARGET MET` line also carries a live GG-046 alert: 532/719 of those rows (74.0%) carry a ticker-vs-`game_date` mismatch (GG-170/GG-185), and ADR-0055's repaired figures recompute `n*=5,580` — not met. This ADR does not paper over that. It is a reason the re-scoping below is framed as *which cell governs the gate*, not as a claim that T4M-PROJ already clears it.

---

## 2. Decision (proposed)

**Re-express G6's closure condition against the (market_type, band) cell registry established by ADR-0053, rather than against a single named band (T1).**

Concretely: replace ADR-0028's Items 2–4 (T1-specific statistical floor, Tier 1, Tier 2) with a **cell-scoped** formulation —

> G6's statistical-adequacy and calibration/EV conditions are met when **at least one ACTIVE (market_type, band) cell**, evaluated under APR-0024's variance-derived `clean_n ≥ n*` standard (via `scripts/run_power_calc.py`'s existing cell-scoped output, already implemented per ADR-0053 §6.3 Item 2 — `[market_type:band]` rows, not the legacy per-band rows), passes:
> - the cell's own statistical floor (`clean_n ≥ n*` at alpha=0.05, power=0.95, derived from that cell's own observed mean/stdev, not a fixed heuristic),
> - Tier 1 (T1-A–D, re-derived per-cell) and Tier 2 (T2-A–D, fill-realism-haircut-adjusted per Mod 5, re-derived per-cell) on that cell's own resolved, eligible population,
> - and any cell-specific direction-eligibility rule analogous to ADR-0028 Mod 9 that applies to that cell's execution logic.

This does not lower the bar — it relocates which population the bar is measured against, from a band that is structurally incapable of producing one, to whichever cell(s) are actually live. It does not by itself certify any cell as passing; T4M-PROJ's GG-046/GG-170 data-integrity issue (§1 caveat) means **no cell currently has a clean, uncontested pass** — this ADR changes the unit of measurement, not the current verdict.

**What this does NOT change:**
- Tier 0 (T0-A/T0-B), Tier 3 (T3-A/B/C/E), and the "Formal gate prerequisites" line of ADR-0028 Item 1/6 are retained, re-scoped to whichever cell(s) are under evaluation rather than to T1 specifically.
- ADR-0028's T4 Activation Gate section is untouched. A cell passing under this re-scoped G6 does **not** imply the T4 Activation Gate (which governs BLOCKED→ACTIVE promotion for T4 sub-bands, a different and independent gate) is satisfied. The two gates continue to test different things: G6 tests whether *any* validated cell justifies live capital; the T4 Activation Gate tests whether a *specific blocked* T4 sub-band may be promoted to active paper status.
- Mod 5 (fill-realism haircut mandate), Mod 6/7 (T4-specific Tier 2 derivation, retained as the template a T4-family cell's Tier 2 would instantiate), and Mod 8 (T-AGG) are retained as written, re-scoped from "MAIN book" / "T4M-PROJ" language to whichever cells are active at time of evaluation.
- Nothing here overrides ADR-0048's `kelly_fraction=0.0` settings or GG-105's open anti-predictive-edge finding for any band.

---

## 3. Open G6 preconditions — current state (none resolved by this document)

Re-scoping the statistical/calibration conditions (§2) does not touch four other standing G6 preconditions, all independently OPEN. A cell-scoped G6 cannot close while any of these remain unresolved, exactly as a T1-scoped G6 could not:

| Precondition | Current state |
|---|---|
| **GG-157** — paper fills never validated against the real book | OPEN, unstaffed. `paper_trader.py` has zero orderbook/depth/fill-size validation (confirmed by direct grep, T-412, 2026-08-04); every resolved paper position — including the epoch-12 flat-$1 cohort G6 is being evaluated against — assumes a mid-price fill never checked against available depth, which GG-155/T-411 independently showed swings 10-100x intraday. GG-157's own record states this explicitly: **"no live-capital authorization should proceed while the fill model remains unvalidated against production orderbook depth, regardless of how many resolved paper bets or how positive the recorded P&L."** A 2026-08-06 follow-up (T-428) found zero usable ticker/timestamp overlap between the epoch-12 cohort and the depth archive that exists, and concluded closing this gap structurally requires depth capture co-located with the bot's own decision-time evaluation — a Phase 3/4 build item, not yet started. |
| **GG-038** — kill-switch SLA is 12× too slow for continuous evaluation | OPEN, Severity HIGH, Actively-Broken: YES. NFR-03's 60s kill-switch SLA (Hard Rule 6) was designed for T1's batch cadence (~10-20 bets/night). At Kalshi's 60 calls/min execution rate, a 60s halt window permits up to 60 additional bets after a kill trigger — acceptable for T1's cadence, unacceptable for any continuously-evaluating band (T4M-PROJ: 359.7 bets/week measured this session, i.e., multiple per hour during live windows). This gap predates and is independent of which band G6 is scoped to; it becomes directly load-bearing the moment G6 is re-scoped toward a continuously-evaluating cell, since NFR-03 is a hard rule (Hard Rule 6) and is not itself amended by this document. |
| **GG-125** — C7 drift-alarm ladder never invoked in production | OPEN, Severity MEDIUM, Blocked-On-Operator: YES. `SystemMonitor.check_and_alert()`/`get_drift_snapshot()` — the methods that would actually raise a Brier/ECE calibration-drift alarm — are never called from any production pipeline script, for either sport (confirmed by direct grep of every call site, T-374, 2026-07-16). Only `check_portfolio_pnl()`, a separate P&L-threshold check, is wired in. A correctly-parameterized baseline (GG-044/ADR-0046) feeds a mechanism nothing invokes. Whichever cell G6 is evaluated against, its live calibration is not being drift-monitored by the mechanism built to do so. |
| **2026-05-29 `_HARD_LIMITS` ADR-revision obligation** | OPEN, unmet, unchanged by this document. The 2026-05-29 DECISION_LOG entry logging `_HARD_LIMITS` (`max_single_event_exposure_usd=500.0`, `max_drawdown_pct=0.20`, `max_portfolio_deployment_pct` per ADR-0026) explicitly states these values require formal revision via ADR at G6, when live bankroll is set. No such ADR has been drafted for any band or cell. This obligation attaches to G6 itself, independent of which population (T1 or a cell) satisfies the statistical/calibration conditions — it is a precondition on the *gate*, not on any one band's evidence. |

None of these four is resolved, mitigated, or scoped-around by the re-expression in §2. They are listed here so that a future reading of this ADR cannot be mistaken for "G6 preconditions cleared" — re-scoping the statistical unit is necessary but not sufficient for closure.

---

## 4. Operator decision required — T1's status (NOT resolved by this document)

This ADR does not decide what happens to T1. It states GG-153's open question explicitly as an operator decision, with options laid out, and stops.

**Question: what should T1's status be, given it is permanently `clean_n=0` under the current regime and cannot self-heal?**

| Option | What it means | What it requires |
|---|---|---|
| **A — Retire T1** | Formally close out T1_MULTI_DAY as a dead band. Remove it from future G6 evidence consideration entirely (not just de-prioritize). | A superseding ADR to ADR-0028/ADR-0010 stating T1 is retired, with rationale. GG-153 would close as "resolved by retirement," not "resolved by reactivation." |
| **B — Revive T1 at a nonzero Kelly fraction, via ADR** | Follow ADR-0048 §4's own stated reactivation path: GG-105's monotonicity gate must pass for T1 on a fresh cohort meeting APR-0024's `clean_n ≥ n*` standard, reporting a validated per-bet edge; then a fresh `mc_empirical_bootstrap.py` (D2) run must confirm 1yr P(kill) ≤ target at that edge, per ADR-0048 §3's lookup table. GG-105 is currently OPEN — three independent remediation attempts (A2 Platt refit, A3 isotonic, T9's feature-level and interaction-term checks) have all failed the monotonicity gate as of ADR-0048 §8's addendum. | A GG-105 fix (candidate: T-384/H2, blending `p_t1` into the shrinkage prior — not yet actioned) prior to any reactivation ADR being possible. This is the slowest and least certain path of the three. |
| **C — Leave T1 dark and exclude it from the gate** | T1 is not retired (no formal close-out) and not revived — it simply stops being counted toward G6 evidence, permanently or until an operator revisits it. This is closest to the practical effect of §2's re-scoping, made explicit rather than implicit. | No ADR beyond this document's §2 acceptance. Lowest-friction option; leaves GG-153 open indefinitely as a monitoring item rather than closing it either way. |

This document takes no position on which option is correct and does not recommend Option A. The choice is the operator's, per this project's standing capability boundary (CLAUDE.md: "You can verify, hunt, surface findings, and execute fixes. You cannot replace the operator's architectural judgment").

---

## 5. What this ADR does not do

- Does not mark itself ACCEPTED.
- Does not touch `execution_bands.py`, `risk.py`, or any `kelly_fraction` value.
- Does not amend ADR-0028 in place — ADR-0028 stands as originally accepted; this document supersedes only the one named section, and only upon acceptance.
- Does not resolve GG-153, GG-157, GG-038, or GG-125 — all remain OPEN.
- Does not certify any cell (including T4M-PROJ) as currently passing G6's re-scoped conditions — §1's caveat on GG-046/GG-170 stands.
- Does not decide T1's fate (§4).

---

## Sign-off

**Awaiting operator/DS decision on:**
1. Accept or reject the cell-scoped re-expression of G6's statistical/calibration conditions (§2).
2. Acknowledge the four open preconditions (§3) as still gating closure regardless of §2.
3. Select an option (or defer) on T1's status (§4) — not required for §1/§2 acceptance, but flagged as the standing open question this ADR was drafted to surface.

**Sign-off:** _(pending)_
**Date:** _(pending)_
**Role:** DS — Earl Ignacio
